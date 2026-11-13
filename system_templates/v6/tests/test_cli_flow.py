"""Offline release rehearsal: shipped ZIP, real CLI, two local Git writers."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from build_release import build


class CliFlowTests(unittest.TestCase):
    def test_shipped_package_checkpoint_conflict_resume_freeze_and_readback(self):
        with tempfile.TemporaryDirectory(prefix='v6-offline-rehearsal-') as temp:
            root=Path(temp);out=root/'release';build(out)
            a=root/'writer-a';a.mkdir()
            with zipfile.ZipFile(out/'初始化系统包.zip') as z:z.extractall(a)
            def run(cwd,*args,ok=True):
                result=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
                if ok:self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                else:self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
                return result
            def cli(cwd,*args,ok=True):
                result=run(cwd,sys.executable,'novel.py',*args,ok=ok)
                return json.loads(result.stdout) if ok else result
            def identity(cwd):
                run(cwd,'git','config','user.name','Synthetic release test')
                run(cwd,'git','config','user.email','synthetic@example.invalid')
            def commit(cwd,message):
                run(cwd,'git','add','.')
                run(cwd,'git','commit','-m',message)
            remote=root/'remote.git'
            run(root,'git','init','--bare','--initial-branch=serial/main',str(remote))
            run(a,'git','init','--initial-branch=serial/main');identity(a)
            run(a,'git','remote','add','origin',str(remote))
            self.assertEqual(cli(a,'package-check')['version'],'6.2.1')
            cli(a,'init','--repository','https://github.com/example/synthetic-rehearsal','--branch','serial/main')
            cli(a,'configure','--title','临时合成作品','--platform','测试')
            (a/'book/plan.md').write_text('临时合成计划，非正式小说。\n')
            task=cli(a,'begin','--request','synthetic-rehearsal-0001')
            work=a/'book/work/CH001'
            (work/'draft.txt').write_text('合成测试正文。\n'*400)
            (work/'editorial.md').write_text('临时待续位置：此处继续。')
            cli(a,'index');commit(a,'Synthetic half-draft checkpoint')
            run(a,'git','push','-u','origin','serial/main')
            b=root/'writer-b';run(root,'git','clone',str(remote),str(b));identity(b)
            resumed=cli(b,'begin','--request','synthetic-rehearsal-new-request')
            self.assertEqual(resumed['status'],'resume')
            self.assertEqual(resumed['request_id'],task['request_id'])
            self.assertEqual((b/'book/work/CH001/draft.txt').read_bytes(),(work/'draft.txt').read_bytes())
            (b/'README.md').write_text((b/'README.md').read_text()+'\nSynthetic unrelated note.\n')
            commit(b,'Synthetic concurrent note');run(b,'git','push')
            (work/'draft.txt').write_text('合成测试正文。\n'*1000)
            (work/'editorial.md').write_text('临时合成审读；没有文学验证。')
            (work/'memory.md').write_text('第一章临时合成记忆。')
            cli(a,'assess','--expect',task['base_state_sha256'],'--decision','ready')
            frozen=cli(a,'freeze','--expect',task['base_state_sha256'],'--request',task['request_id'],'--title','合成第一章')
            self.assertEqual(frozen['status'],'frozen')
            commit(a,'Synthetic chapter adoption')
            run(a,'git','push',ok=False)
            # Preserve both writers; this local replay is not a GitHub deployment.
            run(a,'git','pull','--rebase');run(a,'git','push')
            replay=cli(a,'begin','--request',task['request_id'])
            self.assertEqual(replay['status'],'already_frozen')
            second=cli(a,'begin','--request','synthetic-rehearsal-0002')
            self.assertEqual(second['number'],2)
            commit(a,'Synthetic same-day next chapter');run(a,'git','push')
            readback=root/'readback';run(root,'git','clone',str(remote),str(readback))
            self.assertEqual(cli(readback,'verify')['chapters'],1)
            self.assertIn('Synthetic unrelated note.',(readback/'README.md').read_text())
            self.assertEqual((readback/'book/state.json').read_bytes(),(a/'book/state.json').read_bytes())
            self.assertEqual((readback/'online/index.json').read_bytes(),(a/'online/index.json').read_bytes())
            index=json.loads((readback/'online/index.json').read_text())
            self.assertEqual(index['task']['phase'],'WRITING')
            self.assertEqual(index['chapters'][0]['han_count'],6000)


if __name__=='__main__':unittest.main()
