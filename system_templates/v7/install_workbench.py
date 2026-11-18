"""Add the versioned A7 entry to the existing personal workstation Worker."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
from urllib.parse import quote

from build_release import ROOT, build


def patch_table(worker, name, update):
    marker = f"const {name}="
    start = worker.index(marker) + len(marker)
    table, end = json.JSONDecoder().raw_decode(worker[start:])
    update(table)
    value = json.dumps(table, ensure_ascii=False, separators=(",", ":"))
    return worker[:start] + value + worker[start+end:]


def install(checkout, archive, revision):
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("需要版本化源码的实际提交")
    info = build(archive)
    raw = archive.read_bytes()
    route = "/downloads/a7-novel-init.zip"
    filename = "初始化系统包_A版_V7.0.zip"
    def add_assets(assets):
        for name, kind in [("a7.html","text/html"),("a7.css","text/css"),("a7.mjs","text/javascript")]:
            assets["/"+name] = [kind+"; charset=utf-8", (ROOT/"web"/name).read_text()]
        kind, home = assets["/index.html"]
        anchor = '<a class="text-link" href="./reader.html"'
        if 'href="./a7.html"' not in home:
            if home.count(anchor) != 1:
                raise ValueError("需要核对个人端导航位置")
            home = home.replace(anchor, '<a class="text-link" href="./a7.html">A 版 V7.0 开书与下载 ↗</a> '+anchor)
            old = '<a class="text-link" href="./downloads/novel-init.zip"'
            if home.count(old) != 1:
                raise ValueError("需要核对原 A 下载位置")
            home = home.replace(old,'<p><a class="text-link" href="./a7.html">使用 A 系统 V7.0 开新书 ↗</a></p>'+old)
        assets["/index.html"] = [kind,home]
        kind, prompts = assets["/prompts.mjs"]
        original = "如果state.schema是novel-v6"
        if original in prompts:
            prompts = prompts.replace(original, "若 state.edition 是 novel-a7，读取并执行本书 A7 的 WORKFLOW.md。按原请求恢复试写或当前草稿，运行 packet、所需的试读核验、审核冻结及远端回读。若有 cn-project.json，按本书 CN-GPT 原计划接续。\n如果没有 edition 且 state.schema 是 novel-v6")
        if "novel-a7" not in prompts:
            raise ValueError("需要核对个人端续写指令")
        assets["/prompts.mjs"] = [kind,prompts]

    def add_archive(table):
        table[route] = {"sha256":info["sha256"], "base64":base64.b64encode(raw).decode(),
                        "disposition":f"attachment; filename=novel-A-V7.0.zip; filename*=UTF-8''{quote(filename)}"}

    target = checkout/"worker/index.js"
    worker = patch_table(target.read_text(), "ASSETS", add_assets)
    worker = patch_table(worker, "DOWNLOADS", add_archive)
    old = "'Content-Disposition':'attachment; filename='+url.pathname.split('/').pop()"
    if old in worker:
        worker = worker.replace(old,"'Content-Disposition':file.disposition||('attachment; filename='+url.pathname.split('/').pop())")
    if "file.disposition" not in worker:
        raise ValueError("需要核对下载响应")
    target.write_text(worker)
    release_file = checkout/"RELEASE.json"
    release = json.loads(release_file.read_text())
    release.update(a7_engine_version=info["version"], a7_entry="/a7.html", a7_init_package_sha256=info["sha256"],
                   a7_source_commit=revision, a7_source_path="system_templates/v7",
                   generated_worker_sha256=hashlib.sha256(worker.encode()).hexdigest())
    release_file.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n")
    shutil.copyfile(ROOT/"tests"/"check-workbench.mjs", checkout/"scripts"/"verify-a7.mjs")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout",type=Path)
    parser.add_argument("archive",type=Path)
    parser.add_argument("commit")
    a=parser.parse_args()
    install(a.checkout,a.archive,a.commit)
