"""Release regressions: only synthetic books inside temporary directories."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from novel import Book, Problem, digest, encoded


def example(root):
    b = Book(root)
    b.init('https://github.com/example/synthetic-release', title='合成验收', platform='测试平台')
    b.atomic('book/plan.md', '临时合成计划。'.encode())
    t = b.begin('synthetic-release-request')
    work = b.work_path(1)
    for name, text in [('draft.txt', '合成测试正文。\n' * 1000), ('editorial.md', '临时合成意见。'), ('memory.md', '临时合成记忆。')]:
        b.atomic(work + '/' + name, text.encode())
    b.assess(t['base_state_sha256'], 'ready')
    return b, t


class ReleaseTests(unittest.TestCase):
    def test_setup_rejects_unusable_branch_before_creating_state(self):
        for branch in ['bad branch', 'main//chapter', '.hidden', 'foo.lock/chapter', 'HEAD']:
            with self.subTest(branch=branch), tempfile.TemporaryDirectory() as root:
                b = Book(root)
                with self.assertRaises(Problem):
                    b.init('https://github.com/example/synthetic-release', branch=branch)
                self.assertFalse(b.path('book/state.json').exists())

    def test_repository_suffix_cannot_bypass_protected_targets(self):
        for url in ['https://github.com/1464356758/xiaoshuoV5.git', 'https://github.com/1464356758/XS-KU.git']:
            with self.subTest(url=url), tempfile.TemporaryDirectory() as root:
                b = Book(root)
                with self.assertRaises(Problem):
                    b.init(url)
                self.assertFalse(b.path('book/state.json').exists())

    def test_orphan_work_is_not_rebound_to_a_new_request(self):
        with tempfile.TemporaryDirectory() as root:
            b, t = example(root)
            body = b.read('book/work/CH001/draft.txt')
            b.path('book/work/CH001/task.json').unlink()
            with self.assertRaises(Problem):
                b.begin('different-release-request')
            self.assertEqual(b.read('book/work/CH001/draft.txt'), body)
            self.assertFalse(b.path('book/work/CH001/task.json').exists())

    def test_begin_retry_repairs_index_after_adoption_crash(self):
        with tempfile.TemporaryDirectory() as root:
            b, t = example(root)
            with patch.object(b, '_index', side_effect=OSError('synthetic index interruption')):
                with self.assertRaises(OSError):
                    b.freeze(t['base_state_sha256'], t['request_id'], '合成测试章')
            self.assertEqual(b.json('online/index.json')['progress']['adopted_chapters'], 0)
            self.assertEqual(b.begin(t['request_id'])['status'], 'already_frozen')
            self.assertEqual(b.json('online/index.json')['progress']['adopted_chapters'], 1)

    def test_invalid_reviewed_materials_never_advance_state(self):
        cases = [('text', '过短'.encode()), ('review', b' '), ('memory', b'\n'),
                 ('plan', b'\xff'), ('review', ('合' * 3001).encode())]
        for key, value in cases:
            with self.subTest(key=key, size=len(value)), tempfile.TemporaryDirectory() as root:
                b, t = example(root)
                paths = {'text': 'book/work/CH001/draft.txt', 'review': 'book/work/CH001/editorial.md',
                         'memory': 'book/work/CH001/memory.md', 'plan': 'book/plan.md'}
                b.atomic(paths[key], value)
                a = b.json('book/work/CH001/assessment.json')
                a['hashes'][key] = digest(value)
                b.atomic('book/work/CH001/assessment.json', encoded(a))
                before = b.read('book/state.json')
                with self.assertRaises(Problem):
                    b.freeze(t['base_state_sha256'], t['request_id'], '合成测试章')
                self.assertEqual(b.read('book/state.json'), before)

    def test_assessment_must_remain_an_immutable_object(self):
        with tempfile.TemporaryDirectory() as root:
            b, t = example(root)
            c = b.freeze(t['base_state_sha256'], t['request_id'], '合成测试章')
            r = b.json('book/' + c['record_path'])
            r['assessment_path'] = 'book/work/CH001/assessment.json'
            raw = encoded(r)
            path = b.object(raw, 'json')
            state = b.state()
            state['chapters']['1'].update(record_path=path.removeprefix('book/'), record_sha256=digest(raw))
            b.atomic('book/state.json', encoded(state))
            with self.assertRaises(Problem):
                b.verify()

    def test_invalid_json_shape_is_a_readable_cli_error(self):
        with tempfile.TemporaryDirectory() as root:
            b, _ = example(root)
            b.atomic('book/state.json', b'[]\n')
            r = subprocess.run([sys.executable, str(ROOT/'novel.py'), '--root', root, 'status'], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn('未完成', r.stderr)
            self.assertNotIn('Traceback', r.stderr)


if __name__ == '__main__':
    unittest.main()
