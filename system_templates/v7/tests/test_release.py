"""Exercise the shipped files, not an installed engine. All books and prose here are synthetic."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE))
from build_release import build


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class Release(unittest.TestCase):
    def setUp(self):
        clean = tempfile.TemporaryDirectory()
        self.addCleanup(clean.cleanup)
        self.temp = Path(clean.name)
        self.root = self.temp / "book"
        archive = self.temp / "a.zip"
        build(archive)
        with zipfile.ZipFile(archive) as z:
            z.extractall(self.root)
        self.assertEqual(self.command("package-check")["status"], "package_ok")
        self.command("init","--branch","trunk","--repository","https://github.com/example-fiction/synthetic")
        self.command("configure","--platform","合成渠道","--title","合成流程书")

    def command(self, *args, ok=True, text=False):
        p = subprocess.run([sys.executable, "novel.py", *map(str,args)], cwd=self.root,
                           text=True, encoding="utf-8", capture_output=True)
        if not ok:
            self.assertNotEqual(p.returncode,0,(args,p.stdout))
            return p.stderr
        self.assertEqual(p.returncode,0,(args,p.stderr))
        return p.stdout if text else json.loads(p.stdout)

    def source(self, i, bad=False, first=2, last=3):
        sample = self.temp / f"ref{i}.txt"
        raw = f"合成作品{i}\r\n<p>甲怕失去一件东西。</p><p>乙作了一个新决定{i}。</p>".encode()
        sample.write_bytes(raw)
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        opts = ["--file",sample,"--blob",("a"*40 if bad else blob),"--first",first,"--last",last]
        if bad or last>3:
            return self.command("excerpt",*opts,ok=False)
        self.assertIn("乙作了一个新决定",self.command("excerpt",*opts,text=True))
        return self.command("sample",*opts,"--commit","c"*40,"--source-path",f"合成{i}.txt",
                            "--family",f"group{i}","--lesson","选择带来实际后果","--limit","用于临时测试")

    def prepare_opening(self):
        self.source(1)
        self.source(2)
        path = self.root / "book/opening"
        for key,char in (("a","甲"),("b","乙")):
            (path / f"{key}.txt").write_text((char+"合成试写场面。")*35)
        (path / "choice.md").write_text("合成测试选择第一份，因它首先交代人物具体的取舍。")
        return self.command("audition","--pick","a","--window",10000,"--author-started","--basis","合成窗口")

    def start(self,n):
        result = self.command("begin","--request",f"synthetic-{n}")
        return self.root / f"book/work/CH{n:03}", result["base_state_sha256"]

    def materials(self,n,w):
        h = "零一二三四五六七八九"[n]
        early = "第"+h+"次有人把来信递到了她的手里。"
        late = "第"+h+"次邮车停下她终于收到了回信。"
        draft = early + "\n\n" + ("春" * 2800) + "窗台上还放着那只杯子。" + ("秋"*2850) + "\n" +late
        (w / "draft.txt").write_text(draft)
        (w / "editorial.md").write_text("合成测试的同一上下文编辑说明。")
        (w / "memory.md").write_text("合成测试的当章事实。")
        (self.root / "book/plan.md").write_text("合成故事的未来安排。")
        read = {"verdict":"ready","friction":{"quote":"窗台上还放着那只杯子","why":"合成慢段"},
                "payoff":{"quote":late,"why":"合成结果"},"next":"合成的后继疑问"}
        if n==1:
            read["front"] = {"quote":early,"why":"第一场已有困境"}
        else:
            prev = "零一二三四五六七八九"[n-1]
            read["previous"] = {"quote":"第"+prev+"次邮车停下她终于收到了回信","why":"上一结果促成这章的选择"}
        if n==2:
            read["window"] = {"promise":{"chapter":1,"quote":"第一次有人把来信递到了她的手里","why":"困境可见"},
                              "delivery":{"chapter":2,"quote":early,"why":"合成兑现"}}
        save_json(w/"reading.json",read)
        return read

    def freeze(self,n,w,baseline):
        self.command("assess","--expect",baseline,"--decision","ready")
        return self.command("freeze","--expect",baseline,"--request",f"synthetic-{n}","--title",f"合成章{n}")

    def test_scope_and_reproducible_release(self):
        a = self.temp/"one.zip"
        b = self.temp/"two.zip"
        self.assertEqual(build(a),build(b))
        for marker in ("cn-project.json","project_config.json","book/drafts/old.txt"):
            d = self.temp/marker.replace("/","-")
            p = d/marker
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text("保留")
            self.command("--root",d,"init","--repository","https://github.com/example-fiction/fresh","--branch","trunk",ok=False)
            self.assertEqual(p.read_text(),"保留")
        d=self.temp/"empty"
        self.command("--root",d,"init","--repository","https://github.com/1464356758/XS-KU","--branch","main",ok=False)
        st=self.root/"book/state.json"; data=json.loads(st.read_text()); del data["edition"];data["version"]="6.3.0";save_json(st,data)
        self.command("begin","--request","other-engine",ok=False)

    def test_source_bytes_ranges_and_distinct_premises(self):
        self.command("begin","--request","not-started",ok=False)
        self.source(1,bad=True)
        self.source(1,last=99)
        self.prepare_opening()
        path=self.root/"book/opening"
        shutil.copyfile(path/"a.txt",path/"b.txt")
        self.command("audition","--pick","a","--window",10000,"--author-started","--basis","测试",ok=False)
        self.command("configure","--title","别的书","--platform","合成渠道",ok=False)
        d=self.command("status")["state"]
        p=self.root/d["opening_path"];p.write_bytes(p.read_bytes()+b" ")
        self.command("verify",ok=False)

    def test_revise_and_retry(self):
        self.prepare_opening()
        w,s=self.start(1);(w/"draft.txt").write_text("只写了一半");(w/"editorial.md").write_text("待改")
        self.assertEqual(self.command("begin","--request","another-request")["request_id"],"synthetic-1")
        for m in range(4):
            (w/"draft.txt").write_text("少量合成正文"+str(m))
            for retry in range(2):
                a=self.command("assess","--decision","revise","--expect",s)
                self.assertEqual(len(a["returned_drafts"]),min(3,m+1))
                self.assertEqual(a["decision"],"revise" if m<3 else "blocked")
        self.command("freeze","--expect",s,"--request","synthetic-1","--title","示例",ok=False)

    def test_window_anchors_snapshot_and_old_chapters(self):
        self.prepare_opening()
        w,s=self.start(1);r=self.materials(1,w)
        wrong={**r,"front":{"quote":r["payoff"]["quote"],"why":"在章末"}}
        save_json(w/"reading.json",wrong)
        self.command("assess","--expect",s,"--decision","ready",ok=False)
        save_json(w/"reading.json",r);self.command("assess","--expect",s,"--decision","ready")
        r["next"]="改了方案";save_json(w/"reading.json",r)
        self.command("freeze","--expect",s,"--request","synthetic-1","--title","合成章1",ok=False)
        c=self.freeze(1,w,s)
        w,s=self.start(2);r=self.materials(2,w)
        partial=self.command("packet",text=True)
        self.assertEqual(sum("\u4e00"<=c<="\u9fff" for c in partial),10000+4) # two chapter headings
        self.assertNotIn(r["payoff"]["quote"],partial)
        r["window"]["delivery"]["quote"]=r["payoff"]["quote"];save_json(w/"reading.json",r)
        self.command("assess","--decision","ready","--expect",s,ok=False)
        r["window"]["delivery"].update(chapter=3,quote="第三次有人把来信递到了她的手里。")
        save_json(w/"reading.json",r)
        self.assertIn("缺少窗口内的原文章号", self.command("assess","--decision","ready","--expect",s,ok=False))
        self.materials(2,w);self.freeze(2,w,s)
        old=self.root/"book"/c["text_path"];old.write_bytes(old.read_bytes()+b"!")
        self.command("verify",ok=False)
        self.command("begin","--request","synthetic-3",ok=False)

    def test_five_chapters_and_remote_readback(self):
        def git(*args, cwd=None):
            return subprocess.run(["git",*map(str,args)],cwd=cwd or self.root,check=True,
                                  capture_output=True).stdout.decode().strip()
        self.prepare_opening()
        bare=self.temp/"bare.git"; clone=self.temp/"readback"
        git("init","--bare","--initial-branch=trunk",bare)
        git("init","--initial-branch=trunk");git("config","user.name","Synthetic fixture");git("config","user.email","fixture@example.invalid")
        git("remote","add","origin",bare);git("add",".");git("commit","-m","synthetic initializer");git("push","origin","trunk")
        for n in range(1,7):
            w,s=self.start(n);self.materials(n,w)
            if n==6: (w/"reading.json").unlink()
            frozen=self.freeze(n,w,s)
            self.assertEqual(self.command("begin","--request",f"synthetic-{n}")["status"],"already_frozen")
            self.assertEqual(self.command("freeze","--expect",s,"--request",f"synthetic-{n}","--title","合成章")["text_sha256"],frozen["text_sha256"])
            git("add",".");git("commit","-m",f"synthetic {n}");git("push","origin","trunk")
        head=git("rev-parse","HEAD")
        git("clone",bare,clone)
        self.assertEqual(git("rev-parse","HEAD",cwd=clone),head)
        result=json.loads(subprocess.check_output([sys.executable,"novel.py","verify"],cwd=clone))
        self.assertEqual(result["chapters"],6)
        idx=json.loads((clone/"online/index.json").read_text())
        self.assertEqual(idx["source"]["state_sha256"],sha((clone/"book/state.json").read_bytes()))
        for entry in idx["chapters"]:
            self.assertEqual(sha((clone/entry["text_path"]).read_bytes()),entry["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
