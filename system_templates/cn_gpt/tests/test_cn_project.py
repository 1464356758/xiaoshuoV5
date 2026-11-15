import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from cn_project import Project, Problem, PLAN, DOCS, START, END, json_bytes


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cn-synthetic-book-')
        self.addCleanup(self.temp.cleanup)
        self.book = Project(self.temp.name)
        self.book.create('https://github.com/example/synthetic-cn', 'serial/main', '临时合成小说', '测试', 3)
        self.meta, self.plan, _ = self.book.snapshot()
        self.path = self.meta['projectPath']
        for name in DOCS[:3]:
            self.book.write(self.path + '/' + name, ('# ' + name + '\n临时合成规划，不是正式小说。\n').encode())

    def prepare(self, number=1, request=None):
        request = request or f'synthetic-cn-request-{number:04}'
        b = self.book.begin(request, f'合成章{number}')
        raw = self.book.read(b['file_path']).decode()
        prose = chr(0x4e00 + number) * 6000
        self.book.write(b['file_path'], raw.replace(START + END, START + prose + END).encode())
        summaries = self.book.read(self.path + '/99-章节摘要.md')
        self.book.write(self.path + '/99-章节摘要.md', summaries + f'\n## 第{number:02}章\n临时合成事件后果。\n'.encode())
        self.book.write(self.path + f'/98-编辑意见/第{number:02}章.md', '临时合成审读，不是文学验证。'.encode())
        return b

    def finish(self, number=1):
        b = self.prepare(number)
        self.book.assess(b['plan_sha256'], 'ready')
        return self.book.adopt(b['plan_sha256'], b['request_id'])

    def test_original_architecture_and_derived_reader_view(self):
        self.finish()
        m, p, _ = self.book.snapshot()
        self.assertEqual(p['chapters'][0]['status'], 'completed')
        self.assertEqual(p['chapters'][1]['status'], 'pending')
        self.assertTrue(self.book.path(m['projectPath'] + '/00-人物档案.md').exists())
        state = self.book.data('book/state.json')
        self.assertTrue(state['view_only'])
        self.assertEqual(state['schema'], 'cn-gpt-reading-view')
        self.assertEqual(self.book.data('online/index.json')['progress']['actual_han'], 6000)

    def test_same_day_requests_resume_then_next_and_retries_are_idempotent(self):
        b = self.prepare()
        resumed = self.book.begin('synthetic-cn-new-request', '不同标题')
        self.assertEqual(resumed['status'], 'resume')
        self.assertEqual(resumed['request_id'], b['request_id'])
        self.book.assess(b['plan_sha256'], 'ready')
        self.book.adopt(b['plan_sha256'], b['request_id'])
        self.assertEqual(self.book.adopt(b['plan_sha256'], b['request_id'])['status'], 'already_completed')
        self.assertEqual(self.book.begin(b['request_id'], '旧标题')['status'], 'already_completed')
        self.assertEqual(self.book.begin('synthetic-cn-request-0002', '第二章')['chapter'], 2)

    def test_edit_after_review_and_wrong_baseline_never_adopt(self):
        b = self.prepare(); self.book.assess(b['plan_sha256'], 'ready')
        name = b['file_path']; raw = self.book.read(name)
        self.book.write(name, raw.replace('丁'.encode(), '戊'.encode()))
        self.book.write(name, self.book.read(name) + '\n备注变更。'.encode())
        with self.assertRaisesRegex(Problem, '材料有变'):
            self.book.adopt(b['plan_sha256'], b['request_id'])
        with self.assertRaisesRegex(Problem, '计划已变'):
            self.book.adopt('a' * 64, b['request_id'])
        self.assertEqual(self.book.verify()['chapters'], 0)

    def test_all_frozen_materials_and_canonical_title_are_verified(self):
        self.finish(); m, p, _ = self.book.snapshot(); c = p['chapters'][0]
        paths = [m['projectPath'] + '/' + c['filePath'], c['recordPath']]
        record = self.book.data(c['recordPath'])
        paths.extend(item['path'] for item in record['attachments'].values())
        for path in paths:
            original = self.book.read(path)
            with self.subTest(path=path):
                self.book.write(path, original + b'changed')
                with self.assertRaises((Problem, json.JSONDecodeError)):
                    self.book.verify()
                self.book.write(path, original)
        p['chapters'][0]['title'] = '偷偷改标题'
        self.book.write(self.path + '/' + PLAN, json_bytes(p))
        with self.assertRaises(Problem): self.book.verify()

    def test_state_adopted_before_view_failure_retries_repair_projection(self):
        b = self.prepare(); self.book.assess(b['plan_sha256'], 'ready')
        original_markdown = self.book.read(b['file_path'])
        with patch.object(self.book, 'views', side_effect=OSError('synthetic interruption')):
            with self.assertRaises(OSError): self.book.adopt(b['plan_sha256'], b['request_id'])
        self.assertEqual(self.book.verify()['chapters'], 1)
        adopted = self.book.snapshot()[1]['chapters'][0]
        record = self.book.data(adopted['recordPath'])
        self.assertEqual(self.book.read(record['attachments']['markdown']['path']), original_markdown)
        self.assertEqual(len(self.book.read(record['attachments']['text']['path']).decode()), 6000)
        self.assertEqual(self.book.data('online/index.json')['progress']['adopted_chapters'], 0)
        self.book.begin(b['request_id'], '合成章1')
        self.assertEqual(self.book.data('online/index.json')['progress']['adopted_chapters'], 1)

    def test_crash_before_plan_adoption_does_not_create_a_formal_chapter(self):
        b = self.prepare(); self.book.assess(b['plan_sha256'], 'ready')
        with patch.object(self.book, 'save_plan', side_effect=OSError('synthetic interruption')):
            with self.assertRaises(OSError): self.book.adopt(b['plan_sha256'], b['request_id'])
        self.assertEqual(self.book.verify()['chapters'], 0)
        self.book.adopt(b['plan_sha256'], b['request_id'])
        self.assertEqual(self.book.verify()['chapters'], 1)

    def test_orphan_markdown_cannot_be_claimed_with_a_different_title(self):
        self.book.write(self.path + '/第01章-另一个旧标题.md', b'orphan')
        with self.assertRaisesRegex(Problem, '未绑定'):
            self.book.begin('synthetic-orphan-new-request', '新标题')

    def test_missing_plan_is_not_rebuilt_from_existing_chapters(self):
        self.prepare(); self.book.path(self.path + '/' + PLAN).unlink()
        with self.assertRaisesRegex(Problem, '计划丢失'):
            self.book.create(self.meta['repository'], self.meta['branch'], self.meta['novelName'], self.meta['platform'])

    def test_body_range_excludes_notes_and_bad_title_is_rejected(self):
        b = self.prepare(); self.book.write(b['file_path'], self.book.read(b['file_path']) + ('备注' * 8000).encode())
        self.book.assess(b['plan_sha256'], 'ready')
        self.assertEqual(self.book.adopt(b['plan_sha256'], b['request_id'])['han'], 6000)

    def test_incomplete_materials_and_fake_ready_cannot_bypass_validation(self):
        b = self.prepare()
        for invalid in [b'\xff', b' ', '仅有十来个字。'.encode()]:
            with self.subTest(invalid=invalid):
                old = self.book.read(b['file_path'])
                self.book.write(b['file_path'], invalid)
                with self.assertRaises((Problem, UnicodeDecodeError)):
                    self.book.assess(b['plan_sha256'], 'ready')
                self.book.write(b['file_path'], old)
        self.assertEqual(self.book.verify()['chapters'], 0)

    def test_prior_summary_is_append_only_and_retry_limit_is_real(self):
        self.finish(); b = self.prepare(2)
        path = self.path + '/99-章节摘要.md'; original = self.book.read(path)
        self.book.write(path, original.replace('临时合成事件'.encode(), '改写过去事件'.encode()))
        with self.assertRaisesRegex(Problem, '不能回改'):
            self.book.assess(b['plan_sha256'], 'ready')
        self.book.write(path, original)
        for n in range(3):
            self.book.write(b['file_path'], self.book.read(b['file_path']) + f'\n第{n}次备注修改'.encode())
            a = self.book.assess(self.book.snapshot()[2], 'revise')
            same = self.book.assess(a['planSha256'], 'revise')
            self.assertEqual(same, a)
        self.assertEqual(self.book.snapshot()[1]['chapters'][1]['retryCount'], 3)
        self.book.write(b['file_path'], self.book.read(b['file_path']) + b'last')
        with self.assertRaisesRegex(Problem, '3轮'):
            self.book.assess(self.book.snapshot()[2], 'revise')

    def test_verify_and_begin_reject_changed_frozen_summary_before_new_work(self):
        self.finish()
        summary = self.path + '/99-章节摘要.md'
        original = self.book.read(summary)
        self.book.write(summary, original.replace('临时合成事件'.encode(), '错误改写历史'.encode()))
        with self.assertRaisesRegex(Problem, '摘要不能回改'):
            self.book.verify()
        with self.assertRaisesRegex(Problem, '摘要不能回改'):
            self.book.begin('synthetic-summary-request-0002', '第二章')
        self.assertEqual(self.book.snapshot()[1]['chapters'][1]['status'], 'pending')
        self.book.write(summary, original + '\n## 待续说明\n只追加当前候选的记录。\n'.encode())
        self.assertEqual(self.book.verify()['chapters'], 1)

    def test_short_draft_revision_is_counted_and_cannot_be_adopted(self):
        b = self.prepare()
        original = self.book.read(b['file_path'])
        self.book.write(b['file_path'], original.replace(('丁' * 6000).encode(), ('丁' * 5000).encode()))
        a = self.book.assess(b['plan_sha256'], 'revise')
        self.assertEqual(self.book.snapshot()[1]['chapters'][0]['retryCount'], 1)
        self.assertEqual(self.book.assess(a['planSha256'], 'revise'), a)
        with self.assertRaisesRegex(Problem, '5500—6500'):
            self.book.assess(a['planSha256'], 'ready')
        with self.assertRaisesRegex(Problem, '5500—6500'):
            self.book.adopt(a['planSha256'], b['request_id'])
        self.book.write(b['file_path'], original)
        self.book.assess(a['planSha256'], 'ready')
        self.assertEqual(self.book.adopt(a['planSha256'], b['request_id'])['han'], 6000)

    def test_missing_current_summary_can_be_returned_for_revision(self):
        b = self.prepare()
        self.book.write(self.path + '/99-章节摘要.md', '尚未完成本章摘要。\n'.encode())
        a = self.book.assess(b['plan_sha256'], 'revise')
        self.assertEqual(self.book.snapshot()[1]['chapters'][0]['retryCount'], 1)
        with self.assertRaisesRegex(Problem, '摘要缺少'):
            self.book.assess(a['planSha256'], 'ready')

    def test_150_chapters_keep_original_prefix_and_only_finish_at_the_end(self):
        m, p, _ = self.book.snapshot()
        first = p['chapters'][0]
        p['chapters'] = [{**first, 'chapterNumber': n, 'title': f'待定第{n}章'} for n in range(1, 151)]
        p['totalChapters'] = 150; self.book.write(self.path + '/' + PLAN, json_bytes(p))
        prefix = None
        for n in range(1, 151):
            self.finish(n)
            if n == 1: prefix = self.book.read(self.book.snapshot()[1]['chapters'][0]['recordPath'])
        m, p, _ = self.book.snapshot()
        self.assertEqual(p['status'], 'completed')
        self.assertEqual(self.book.verify()['chapters'], 150)
        self.assertEqual(prefix, self.book.read(p['chapters'][0]['recordPath']))


if __name__ == '__main__': unittest.main()
