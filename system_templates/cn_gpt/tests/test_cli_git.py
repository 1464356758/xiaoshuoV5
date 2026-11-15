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


class CliGitTests(unittest.TestCase):
    def test_real_zip_cli_checkpoint_restore_conflict_adopt_and_readback(self):
        with tempfile.TemporaryDirectory(prefix='cn-offline-git-') as temp:
            root=Path(temp);out=root/'release';build(out);a=root/'a';a.mkdir()
            with zipfile.ZipFile(out/'初始化系统包_CN-GPT_对照版.zip') as z:z.extractall(a)
            def run(cwd,*args,ok=True):
                r=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
                if ok:self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                else:self.assertNotEqual(r.returncode,0)
                return r
            def cli(cwd,*args):return json.loads(run(cwd,sys.executable,'tools/cn_project.py',*args).stdout)
            def ident(cwd):
                run(cwd,'git','config','user.name','Synthetic CN test');run(cwd,'git','config','user.email','synthetic@example.invalid')
            def commit(cwd,message):
                run(cwd,'git','add','.');run(cwd,'git','commit','-m',message)
            remote=root/'remote.git';run(root,'git','init','--bare','--initial-branch=serial/main',str(remote))
            run(a,'git','init','--initial-branch=serial/main');ident(a);run(a,'git','remote','add','origin',str(remote))
            self.assertEqual(cli(a,'package-check')['engine'],'cn-novelist-gpt')
            (a/'.gitignore').write_text('preserve-original-rule\n')
            c=cli(a,'create','--repository','https://github.com/example/synthetic-cli-cn','--branch','serial/main','--title','临时CLI合成作品','--platform','测试','--chapters','2')
            self.assertIn('preserve-original-rule',(a/'.gitignore').read_text())
            path=c['project']['projectPath']
            for name in ['00-人物档案.md','01-大纲.md','03-文风基准.md']:(a/path/name).write_text('临时合成规划。')
            t=cli(a,'begin','--request','synthetic-cli-request-0001','--title','临时第一章')
            md=a/t['file_path'];template=md.read_text();md.write_text(template.replace('<!-- CN_BODY_START -->\n\n<!-- CN_BODY_END -->','<!-- CN_BODY_START -->\n'+'甲'*3000+'\n<!-- CN_BODY_END -->'))
            cli(a,'index');commit(a,'Synthetic half-draft');run(a,'git','push','-u','origin','serial/main')
            b=root/'b';run(root,'git','clone',str(remote),str(b));ident(b)
            resumed=cli(b,'begin','--request','synthetic-cli-other-trigger','--title','无效新题名')
            self.assertEqual(resumed['status'],'resume');self.assertEqual(resumed['request_id'],t['request_id'])
            self.assertEqual((b/t['file_path']).read_bytes(),md.read_bytes())
            (b/'README.md').write_text((b/'README.md').read_text()+'\nSynthetic unrelated note.\n');commit(b,'Synthetic note');run(b,'git','push')
            md.write_text(template.replace('<!-- CN_BODY_START -->\n\n<!-- CN_BODY_END -->','<!-- CN_BODY_START -->\n'+'甲'*6000+'\n<!-- CN_BODY_END -->'))
            (a/path/'99-章节摘要.md').write_text((a/path/'99-章节摘要.md').read_text()+'\n## 第01章\n临时合成后果。\n')
            edit=a/path/'98-编辑意见';edit.mkdir();(edit/'第01章.md').write_text('临时合成审读，未验证文学质量。')
            cli(a,'assess','--expect',t['plan_sha256'],'--decision','ready')
            self.assertEqual(cli(a,'adopt','--expect',t['plan_sha256'],'--request',t['request_id'])['han'],6000)
            commit(a,'Synthetic adoption');run(a,'git','push',ok=False)
            run(a,'git','pull','--rebase');run(a,'git','push')
            self.assertEqual(cli(a,'adopt','--expect',t['plan_sha256'],'--request',t['request_id'])['status'],'already_completed')
            cli(a,'begin','--request','synthetic-cli-request-0002','--title','第二章');commit(a,'Synthetic next target');run(a,'git','push')
            fresh=root/'fresh';run(root,'git','clone',str(remote),str(fresh))
            self.assertEqual(cli(fresh,'verify')['chapters'],1)
            self.assertEqual((a/path/'02-写作计划.json').read_bytes(),(fresh/path/'02-写作计划.json').read_bytes())
            self.assertIn('Synthetic unrelated note.',(fresh/'README.md').read_text())
            tracked=run(fresh,'git','ls-files').stdout.splitlines();self.assertNotIn('.cn.lock',tracked)
            self.assertFalse(any('__pycache__' in p for p in tracked))


if __name__=='__main__':unittest.main()
