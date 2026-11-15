import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from build_release import build
from cn_project import Project, DOCS, START, END, package_check


class PackageTests(unittest.TestCase):
    def test_repeatable_package_contains_original_architecture_without_book_identity(self):
        with tempfile.TemporaryDirectory(prefix='cn-bundle-') as temp:
            out=Path(temp)/'out';a=build(out);raw=(out/'初始化系统包_CN-GPT_对照版.zip').read_bytes()
            (out/'web/obsolete.js').write_text('obsolete')
            b=build(out);self.assertEqual(raw,(out/'初始化系统包_CN-GPT_对照版.zip').read_bytes())
            self.assertFalse((out/'web/obsolete.js').exists());self.assertEqual(a,b)
            unpack=Path(temp)/'unpack'
            with zipfile.ZipFile(out/'初始化系统包_CN-GPT_对照版.zip') as z:
                self.assertNotIn('cn-project.json',z.namelist());self.assertFalse(any(p.startswith('book/') for p in z.namelist()))
                z.extractall(unpack)
            self.assertEqual(package_check(unpack)['engine'],'cn-novelist-gpt')
            upstream=json.loads((ROOT/'UPSTREAM.json').read_text())
            for name,meta in upstream['files'].items():
                self.assertEqual(hashlib.sha256((unpack/'vendor/chinese-novelist'/name).read_bytes()).hexdigest(),meta['sha256'])

    def test_source_and_unowned_output_are_not_overwritten(self):
        with self.assertRaises(ValueError):build(ROOT)
        with tempfile.TemporaryDirectory(prefix='cn-unowned-') as temp:
            out=Path(temp);(out/'web').mkdir();p=out/'web/user.txt';p.write_text('keep')
            with self.assertRaises(ValueError):build(out)
            self.assertEqual(p.read_text(),'keep')

    def test_a_entry_and_download_and_b_package_match_worker_routes(self):
        with tempfile.TemporaryDirectory(prefix='cn-worker-test-') as temp:
            out=Path(temp)/'out';build(out)
            script=ROOT/'tests/worker-test.mjs'
            r=subprocess.run(['node',str(script),str(out)],text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)


class FrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='cn-generated-front-');cls.addClassCleanup(cls.temp.cleanup)
        cls.out=Path(cls.temp.name)/'release';build(cls.out)

    def run_case(self,mode):
        with tempfile.TemporaryDirectory(prefix='cn-front-fixture-') as temp:
            b=Project(temp);b.create('https://github.com/example/synthetic-cn-front','main','临时合成B小说','测试',2)
            m,_,_=b.snapshot();path=m['projectPath']
            for name in DOCS[:3]:b.write(path+'/'+name,('临时合成'+name).encode())
            t=b.begin('synthetic-front-request-0001','临时一')
            prose='\ufeff'+('合成小说测试正文。\r\n'*750) if mode=='bytes' else '甲'*6000
            b.write(t['file_path'],b.read(t['file_path']).decode().replace(START+END,START+prose+END).encode())
            b.write(path+'/99-章节摘要.md',(b.read(path+'/99-章节摘要.md').decode()+'\n## 第01章\n合成摘要。\n').encode())
            b.write(path+'/98-编辑意见/第01章.md','合成审读，不是文学验证。'.encode())
            b.assess(t['plan_sha256'],'ready');b.adopt(t['plan_sha256'],t['request_id'])
            r=subprocess.run(['node',str(ROOT/'tests/frontend-test.mjs'),mode,str(self.out/'web'),temp],text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_valid_canonical_markdown_and_all_snapshots_are_readable(self):self.run_case('valid')
    def test_bom_crlf_body_is_verified_without_normalization(self):self.run_case('bytes')
    def test_changed_plan_cannot_be_hidden_behind_old_index(self):self.run_case('stale')
    def test_missing_snapshot_is_rejected(self):self.run_case('missing')
    def test_exported_text_tampering_is_rejected(self):self.run_case('body')
    def test_index_title_tampering_is_rejected(self):self.run_case('title')
    def test_prompts_use_b_architecture_and_protect_system_repositories(self):self.run_case('prompt')


if __name__=='__main__':unittest.main()
