"""Literal locator integration and read-only guarantees, using synthetic books."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from novel import Book, han

PHRASE='他把那封尚未拆开的信压在杯底，直到灯熄灭也没有再看门口。'


class ProseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='v63-synthetic-repeat-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.book=Book(self.root)
        self.book.init('https://github.com/example/synthetic-prose',title='临时合成',platform='测试')
        self.book.atomic('book/plan.md','临时合成计划。'.encode())
        t=self.book.begin('synthetic-prose-0001')
        body=PHRASE+'\n'+'甲'*(6000-han(PHRASE))
        for name,value in [('draft.txt',body),('editorial.md','临时合成意见。'),('memory.md','临时合成记忆。')]:
            self.book.atomic('book/work/CH001/'+name,value.encode())
        self.book.assess(t['base_state_sha256'],'ready')
        self.frozen=self.book.freeze(t['base_state_sha256'],t['request_id'],'合成一')
        self.book.begin('synthetic-prose-0002')
        self.draft=self.root/'book/work/CH002/draft.txt'

    def run_check(self,*args,ok=True):
        before={p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file()}
        r=subprocess.run([sys.executable,str(ROOT/'tools/prose_check.py'),'--root',str(self.root),*args],text=True,capture_output=True)
        after={p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after,'检查程序不能写入、修复或删除任何小说文件')
        if ok:
            self.assertEqual(r.returncode,0,r.stderr)
            return json.loads(r.stdout)
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(r.stdout)
        return r.stderr

    def test_cross_chapter_and_intra_draft_locations_are_real(self):
        self.draft.write_text('不同的新场景。\n  '+PHRASE+'\n'+PHRASE.replace('信','信 ')+'\n尾声。')
        r=self.run_check();self.assertEqual(r['candidate_count'],1)
        c=r['candidates'][0];self.assertEqual((c['draft_count'],c['prior_count']),(2,1))
        self.assertEqual(c['draft_locations'][0]['line'],2)
        self.assertEqual(c['draft_locations'][0]['column'],3)
        self.assertEqual(c['prior_locations'][0]['chapter'],1)
        self.assertEqual(c['prior_locations'][0]['line'],1)
        self.assertEqual(c['prior_locations'][0]['path'],'book/'+self.frozen['text_path'])
        self.assertEqual(r['status'],'candidates_only')

    def test_short_dialogue_is_not_flagged_and_zero_is_not_a_quality_pass(self):
        self.draft.write_text('“我知道。”\n“我知道。”\n'+ '乙'*100)
        r=self.run_check();self.assertEqual(r['candidate_count'],0)
        self.assertEqual(r['status'],'candidates_only')
        self.assertIn('无候选不表示无问题',r['limits'])

    def test_limit_preserves_total_and_all_matches_remain_advisory(self):
        phrases=[PHRASE.replace('信',word) for word in ['信','纸','图']]
        self.draft.write_text('\n'.join(phrases*6))
        r=self.run_check('--limit','2')
        self.assertEqual((r['candidate_count'],len(r['candidates']),r['omitted_candidates']),(3,2,1))
        self.assertTrue(all(c['draft_count']==6 for c in r['candidates']))
        self.assertEqual(len(r['candidates'][0]['draft_locations']),4)

    def test_tampered_frozen_body_is_never_used_as_a_clean_reference(self):
        self.draft.write_text(PHRASE)
        self.book.path('book/'+self.frozen['text_path']).write_text('已被改动。')
        self.assertIn('被改动',self.run_check(ok=False))

    def test_missing_task_and_invalid_utf8_do_not_modify_or_rebind_work(self):
        self.draft.write_bytes(b'\xff')
        self.assertIn('utf-8',self.run_check(ok=False))
        (self.draft.parent/'task.json').unlink()
        self.assertIn('匹配任务',self.run_check(ok=False))


if __name__=='__main__':unittest.main()
