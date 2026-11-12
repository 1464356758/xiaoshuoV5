"""All books in these tests are explicitly synthetic and temporary."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from novel import Book, Problem, digest, han, encoded, VERSION, SCHEMA


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.b = Book(self.tmp.name)
        self.b.init("https://github.com/example/synthetic-novel", title="合成测试", platform="测试平台")
        self.b.atomic("book/plan.md", "测试计划，只用于临时自动验证。".encode())

    def ready(self, request="synthetic-request-0001"):
        t = self.b.begin(request)
        base = self.b.work_path(t["number"])
        self.b.atomic(base + "/draft.txt", ("合成测试正文。\n" * 1000).encode())
        self.b.atomic(base + "/editorial.md", "合成测试意见，不是文学评价。".encode())
        self.b.atomic(base + "/memory.md", "合成测试记忆，不是真实作品事实。".encode())
        self.b.assess(t["base_state_sha256"], "ready")
        return t

    def freeze(self, t):
        return self.b.freeze(t["base_state_sha256"], t["request_id"], "合成测试章")

    def test_same_day_three_chapters_and_retry(self):
        for n in range(1, 4):
            t = self.ready(f"synthetic-request-{n:04}")
            self.assertEqual(self.freeze(t)["number"], n)
            self.assertEqual(self.freeze(t)["status"], "already_frozen")
            self.assertEqual(self.b.begin(t["request_id"])["status"], "already_frozen")
        self.assertEqual(self.b.verify()["chapters"], 3)

    def test_resume_preserves_content_and_request(self):
        t = self.ready()
        again = self.b.begin("different-request-0002")
        self.assertEqual(again["request_id"], t["request_id"])
        self.assertEqual(again["status"], "resume")
        self.assertTrue(self.b.read("book/work/CH001/draft.txt"))

    def test_revision_conflict_keeps_original(self):
        t = self.ready()
        original = self.b.read("book/state.json")
        with self.assertRaises(Problem):
            self.b.freeze("0" * 64, t["request_id"], "测试")
        self.assertEqual(original, self.b.read("book/state.json"))

    def test_review_tied_to_all_four_inputs(self):
        t = self.ready()
        for path in ["book/work/CH001/draft.txt", "book/work/CH001/editorial.md", "book/work/CH001/memory.md", "book/plan.md"]:
            old = self.b.read(path)
            self.b.atomic(path, old + "改".encode())
            with self.assertRaises(Problem):
                self.freeze(t)
            self.b.atomic(path, old)
        self.freeze(t)

    def test_revise_and_short_prose_do_not_freeze(self):
        t = self.ready()
        self.b.assess(t["base_state_sha256"], "revise")
        with self.assertRaises(Problem):
            self.freeze(t)
        self.b.atomic("book/work/CH001/draft.txt", "测试短稿".encode())
        with self.assertRaises(Problem):
            self.b.assess(t["base_state_sha256"], "ready")

    def test_frozen_prose_memory_and_history_are_checked(self):
        first = self.freeze(self.ready())
        self.freeze(self.ready("synthetic-request-0002"))
        for path in ["book/" + first["text_path"], self.b.json("book/" + first["record_path"])["attachments"]["memory"]]:
            old = self.b.read(path)
            self.b.atomic(path, old + b"changed")
            with self.assertRaises(Problem):
                self.b.verify()
            self.b.atomic(path, old)
        self.assertEqual(self.b.verify()["chapters"], 2)

    def test_crash_before_state_write_adopts_nothing(self):
        t = self.ready()
        original = self.b.atomic
        def fail(name, data):
            if name == "book/state.json":
                raise OSError("synthetic crash")
            original(name, data)
        with patch.object(self.b, "atomic", side_effect=fail), self.assertRaises(OSError):
            self.freeze(t)
        self.assertEqual(self.b.verify()["chapters"], 0)
        self.assertEqual(self.freeze(t)["number"], 1)

    def test_crash_after_state_write_is_idempotent(self):
        t = self.ready()
        with patch.object(self.b, "_index", side_effect=OSError("synthetic index crash")), self.assertRaises(OSError):
            self.freeze(t)
        self.assertEqual(self.b.verify()["chapters"], 1)
        self.assertEqual(self.freeze(t)["status"], "already_frozen")
        self.assertEqual(self.b.json("online/index.json")["progress"]["adopted_chapters"], 1)

    def test_no_overwrite_and_path_escape(self):
        with self.assertRaises(Problem):
            self.b.init("https://github.com/example/synthetic-novel")
        with self.assertRaises(Problem):
            self.b.read("../escape")
        self.b.immutable("book/objects/test.txt", b"original")
        with self.assertRaises(Problem):
            self.b.immutable("book/objects/test.txt", b"changed")

    def test_os_lock_releases_after_process_exit(self):
        code = "from novel import Book; import sys; b=Book(sys.argv[1]);\nwith b.lock(): print('locked', flush=True); sys.stdin.read()"
        child = subprocess.Popen([sys.executable, "-c", code, self.tmp.name], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        self.assertEqual(child.stdout.readline().strip(), "locked")
        with self.assertRaises(Problem):
            self.b.begin("synthetic-lock-test")
        child.kill()
        child.wait()
        child.stdin.close()
        child.stdout.close()
        self.assertEqual(self.b.begin("synthetic-lock-test")["status"], "new")

    def test_empty_package_manifest_rejected(self):
        self.b.atomic('INIT_MANIFEST.json', encoded({'version':VERSION,'engine':SCHEMA,'files':{}}))
        with self.assertRaises(Problem):
            self.b.package_check()

    def test_pending_target_must_match_next_chapter(self):
        t = self.ready()
        t['number'] = 9
        self.b.atomic('book/work/CH001/task.json', encoded(t))
        with self.assertRaises(Problem):
            self.b.begin('another-synthetic-request')

    def test_missing_memory_attachment_rejected(self):
        c = self.freeze(self.ready())
        r = self.b.json('book/' + c['record_path'])
        r['attachments'].pop('memory')
        path = self.b.object(encoded(r), 'json')
        s = self.b.state()
        s['chapters']['1'].update(record_path=path.removeprefix('book/'), record_sha256=digest(encoded(r)))
        self.b.atomic('book/state.json', encoded(s))
        with self.assertRaises(Problem):
            self.b.verify()

    def test_orphan_draft_blocks_new_identity(self):
        self.ready()
        self.b.path('book/state.json').unlink()
        with self.assertRaises(Problem):
            self.b.init('https://github.com/example/synthetic-novel')

    def test_index_uses_one_state_snapshot(self):
        before = self.b.state_hash()
        verify = self.b.verify
        def intervening_write(*args, **kwargs):
            result = verify(*args, **kwargs)
            s = self.b.state()
            s['title'] = '另一快照'
            self.b.atomic('book/state.json', encoded(s))
            return result
        with patch.object(self.b, 'verify', side_effect=intervening_write):
            index = self.b.index()
        self.assertEqual(index['source']['state_sha256'], before)

    def test_context_uses_one_state_snapshot(self):
        before = self.b.state_hash()
        verify = self.b.verify
        def intervening_write(*args, **kwargs):
            result = verify(*args, **kwargs)
            s = self.b.state()
            s['title'] = '另一快照'
            self.b.atomic('book/state.json', encoded(s))
            return result
        with patch.object(self.b, 'verify', side_effect=intervening_write):
            context = self.b.context()
        self.assertEqual(context['state_sha256'], before)

    def test_parallel_freeze_and_retry_adopt_once(self):
        t = self.ready()
        args = [sys.executable, str(ROOT/'novel.py'), '--root', self.tmp.name, 'freeze', '--expect', t['base_state_sha256'], '--request', t['request_id'], '--title', '合成并发章']
        jobs = [subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        results = [(job, job.communicate(timeout=15)) for job in jobs]
        self.assertTrue(any(job.returncode == 0 for job, _ in results))
        for job, (out, err) in results:
            if job.returncode == 0:
                self.assertIn(json.loads(out)['status'], {'frozen','already_frozen'})
            else:
                self.assertIn('另一个保存操作正在执行', err)
        self.assertEqual(self.b.verify()['chapters'], 1)
        self.assertEqual(self.freeze(t)['status'], 'already_frozen')

    def test_complete_150_chapters_without_rewriting_prefix(self):
        first = None
        for n in range(1, 151):
            t = self.ready(f'synthetic-long-run-{n:04}')
            c = self.freeze(t)
            if first is None:
                first = (c['text_path'], self.b.read('book/'+c['text_path']))
        self.assertEqual(self.b.verify()['chapters'], 150)
        self.assertEqual(self.b.read('book/'+first[0]), first[1])
        self.assertEqual(self.b.json('online/index.json')['task']['phase'], 'COMPLETE')
        with self.assertRaises(Problem):
            self.b.begin('synthetic-chapter-overflow')

    def test_malformed_assessment_never_advances_state(self):
        t = self.ready()
        name = 'book/work/CH001/assessment.json'
        a = self.b.json(name)
        a['schema'] = 'corrupted-assessment'
        self.b.atomic(name, encoded(a))
        with self.assertRaises(Problem):
            self.freeze(t)
        self.assertEqual(self.b.state()['revision'], 0)


if __name__ == "__main__":
    unittest.main()
