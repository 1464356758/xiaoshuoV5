"""Generated production modules with real CLI output and an offline GitHub fixture."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_release import build
from novel import Book


class FrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='v6-frontend-release-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.web = Path(cls.temp.name)/'release'
        build(cls.web)

    def check(self, mode, *, chapters=1, pending=False, raw_bytes=False):
        with tempfile.TemporaryDirectory(prefix='v6-synthetic-web-book-') as root:
            b=Book(root)
            with patch('novel.utc', return_value='2026-11-14T01:00:00+00:00'):
                b.init('https://github.com/example/synthetic-release',title='临时合成小说',platform='测试')
                b.atomic('book/plan.md','临时合成计划。'.encode())
                for n in range(1,chapters+1):
                    t=b.begin(f'synthetic-web-request-{n:04}')
                    work=b.work_path(n)
                    text=('\ufeff' if raw_bytes else '')+('合成测试正文。'+ ('\r\n' if raw_bytes else '\n'))*1000
                    for name,value in [('draft.txt',text),('editorial.md','临时合成意见。'),('memory.md',f'第{n}章临时记忆。')]:
                        b.atomic(work+'/'+name,value.encode())
                    b.assess(t['base_state_sha256'],'ready')
                    b.freeze(t['base_state_sha256'],t['request_id'],f'合成测试{n}')
                if pending:
                    t=b.begin('synthetic-web-pending')
                    b.atomic(b.work_path(t['number'])+'/draft.txt','临时未完稿。'.encode())
            result=subprocess.run(['node',str(ROOT/'tests/frontend-release.mjs'),mode,str(self.web/'web'),root],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_exact_utf8_bom_and_crlf_survive_reading(self):
        self.check('bytes',raw_bytes=True)

    def test_reading_old_chapter_checks_real_memory_file(self):
        self.check('attachments',chapters=2)

    def test_index_title_must_match_formal_state(self):
        self.check('title')

    def test_today_update_survives_starting_next_draft(self):
        self.check('pending',pending=True)

    def test_orphan_draft_is_not_reported_as_completed(self):
        self.check('orphan',pending=True)

    def test_manual_continuation_does_not_need_a_schedule_time(self):
        self.check('manual')

    def test_manager_repository_is_not_a_new_book_target(self):
        self.check('protected')
