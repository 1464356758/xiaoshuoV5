#!/usr/bin/env python3
"""Package the new kernel; reuse the independent legacy management/reading UI."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile
from novel import VERSION, PACKAGE_FILES, han

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT.parent / "v4.6"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_required(text, old, new):
    if text.count(old) != 1:
        raise ValueError("工作台兼容接口已变化，停止构建：" + old[:90])
    return text.replace(old, new, 1)


def archive(files, output):
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)


def frontend(dist):
    if dist.exists():
        if not (dist.parent / ".v6-build").exists():
            raise ValueError("输出目录已有web且没有本构建器标记，请改用空输出目录")
        shutil.rmtree(dist)
    shutil.copytree(LEGACY / "web/dist", dist, dirs_exist_ok=True)
    for name in ["prompts.mjs", "v6-reader.mjs"]:
        shutil.copyfile(ROOT / "web" / name, dist / name)
    p = dist / "hub-core.mjs"
    s = replace_required(p.read_text(), "HUB_VERSION='1.4.10'", "HUB_VERSION='2.1.2'")
    s = replace_required(s, r"new TextDecoder('utf-8',{fatal:true}).decode(bytes).replace(/\r\n?/g,'\n')", "new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes)")
    s = "import {startPrompt,continuePrompt} from './prompts.mjs';\nimport {validateV6State,verifyV6Chapter,verifyV6Text,inspectV6,v6UpdateStatus} from './v6-reader.mjs';\n" + s
    start, end = s.index("export function newBookPrompt("), s.index("export function checkerPrompt(")
    s = s[:start] + """export function newBookPrompt({repository,platform='',preferences='',management=SYSTEM_REPOSITORY}={}){
 const repo=parseRepository(repository),manager=parseRepository(management);
 fail(!['xiaoshuov5','xs-ku','xs-gl','xiaishuo-zuozong'].includes(repo.name.toLowerCase())&&![SYSTEM_REPOSITORY,TEMPLATE_REPOSITORY,REFERENCE_LIBRARY,manager.url].some(x=>parseRepository(x).key===repo.key),'请填写独立的新书仓库。');
 fail(String(platform).length<=80&&String(preferences).length<=1200,'平台或偏好过长。');
 return startPrompt(repo.url,String(platform).trim(),String(preferences).trim());
}
export function dailyTaskPrompt(entry){return continuePrompt(entry,{scheduled:true});}
export function writingPrompt(entry,management,options={}){return continuePrompt(entry,options);}
export function repairPrompt(entry){return continuePrompt(entry)+'\\n优先检查当前未完成稿，续写同一目标，不创建日程。';}
""" + s[end:]
    s = replace_required(s, "const state=raw.data;fail(", "const state=raw.data;validateV6State(state,manifest);fail(")
    s = replace_required(s, "const file=await client.readFile(chapter.text_path,book.snapshot.commit);", "await verifyV6Chapter(client,book,chapter);const file=await client.readFile(chapter.text_path,book.snapshot.commit);if(book.state.schema==='novel-v6')verifyV6Text(file,chapter);")
    s = replace_required(s, "const day=dayInShanghai(now);\n    const file=", "if(book.state.schema==='novel-v6')return {...result,...await inspectV6(client,book,{now})};\n    const day=dayInShanghai(now);\n    const file=")
    s = replace_required(s, "const active=await client.optionalJSON('book/daily/active.json',base.commit);", """if(book.state.schema==='novel-v6'){
      const v=await inspectV6(client,book,{now});return {...base,...v,status:v6UpdateStatus(v,date)};
    }
    const active=await client.optionalJSON('book/daily/active.json',base.commit);""")
    p.write_text(s)
    p = dist / "hub.js"
    s = "import {writingTimeValid} from './prompts.mjs';\n" + p.read_text()
    s = s.replace("prompts:['日更指令','每天，接着写。','选一本小说和执行时间，生成完整指令，复制到对应 GPT 工作聊天。']", "prompts:['续写指令','接着写下一章。','选择小说，复制指令到本书 GPT 聊天；默认立即续写。']")
    s = replace_required(s, "writingPrompt({...book,expected_time:time},config.repository_url)", "writingPrompt({...book,expected_time:time},config.repository_url,{scheduled:$('writingMode').value==='scheduled'})")
    s = replace_required(s, r"const time=$('writingTime').value,valid=!!book&&/^([01]\d|2[0-3]):[0-5]\d$/.test(time);", "const time=$('writingTime').value,valid=!!book&&writingTimeValid(time,$('writingMode').value==='scheduled');")
    s = s.replace("'每天北京时间 '+time+' · 每次只写一章'", "($('writingMode').value==='scheduled'?'每天北京时间 '+time:'现在续写 · 同天不限章数')+' · 每次完成一章'")
    s = s.replace("$('writingBook').addEventListener('change'", "$('writingMode').addEventListener('change',()=>{$('writingTime').disabled=$('writingMode').value!=='scheduled';updateWritingPrompt();});\n$('writingBook').addEventListener('change'")
    s = s.replace("已复制配置与长期执行指令，请到本书 GPT 工作聊天粘贴并更新原任务。", "指令已复制，请到本书 GPT 工作聊天粘贴执行。")
    s = s.replace("toast('日更指令已复制。')", "toast('续写指令已复制。')")
    s = s.replace("完整日更指令", "完整续写指令").replace("》日更指令", "》续写指令")
    s = s.replace("请选择有效的每天执行时间。", "请选择有效的每日任务时间。")
    s = s.replace("复制后打开本书聊天，粘贴发送；已有任务就更新，不重复创建。", "复制后打开本书聊天，粘贴执行当前指令。")
    s = s.replace("已登记固定反馈对话。后续复用同一个任务，任务绑定以 GPT 实际显示为准。", "已登记本书反馈对话，可打开查看执行结果。")
    p.write_text(s)
    p = dist / "index.html"
    s = p.read_text().replace("工作台 1.4.10 · 写作内核 V4.6", "工作台 2.1.2 · 新书内核 V6.2.1")
    s = s.replace("日更指令", "续写指令").replace("V4.6.4", "V6.2.1")
    s = s.replace("选择小说，生成续写指令", "选择小说，接着写下一章")
    s = s.replace('<label>每天执行时间（北京时间）<input id="writingTime"', '<label>执行方式<select id="writingMode"><option value="manual">现在续写一章</option><option value="scheduled">设置每日任务</option></select></label><label>每日任务时间（北京时间）<input disabled id="writingTime"')
    s = s.replace("复制到本书 GPT 聊天，更新已有每日任务。指令已分开本次配置和长期执行规则；每轮按仓库最新状态推进。", "默认现在续写，同一天不限章数。只有选择“设置每日任务”才生成定时配置；实际写作在本书 GPT 聊天执行。")
    s = s.replace("核对任务编号、启用状态和实际日程，再用章节与回执验收完整日更。", "GPT完成写作、返修、冻结与保存；回来刷新查看正式章节。")
    s = s.replace("配置计划后可在下方核验本日完成证据；需要接续未完成章节时，使用“我的小说 → 更多 → 补更指令”。工具预检通过只证明工具链可用。", "可核验最新正式章及未完成草稿。V6直接核对正文与冻结记录，旧书保持原流程。")
    s = s.replace("每天，接着写。", "接着写下一章。")
    s = s.replace("核对本日写作完成", "核对最新正式章").replace("核验本日完成证据", "核验最新章与草稿")
    s = s.replace("可单独核对正文、冻结和完成回执。不会启动写作，也不改变“今日更新”的查询规则。", "核对最新正文和冻结版本，查看是否有待续草稿；此操作不会启动写作。")
    s = s.replace("已包含每章约6000字、前5章强化、XS-KU参考学习、部署核验和逐章冻结。", "V6：约6000字一章，前五章整体设计，实际审稿后冻结；同天不限章数。")
    p.write_text(s)
    return dist


def build(out):
    if out == ROOT or out.is_relative_to(ROOT) or ROOT.is_relative_to(out):
        raise ValueError("交付输出应位于系统源码目录之外")
    out.mkdir(parents=True, exist_ok=True)
    if (out / "web").exists() and not (out / ".v6-build").exists():
        raise ValueError("输出目录已有web，请使用空目录")
    (out / ".v6-build").touch()
    files = {n: (ROOT / n).read_bytes() for n in sorted(PACKAGE_FILES - {"启动新书.txt"})}
    files["启动新书.txt"] = ("请依据本初始化包，实际部署并接管一部独立的新小说。\n"
        "【唯一新书仓库】在此填写GitHub仓库首页链接\n【平台】未定，由我选择\n【偏好】暂无\n\n"
        "先验证包清单，再读AGENTS.md、WORKFLOW.md、CRAFT.md，检查目标仓库和实际默认分支。"
        "确认空仓库才部署；空仓库没有HEAD时按WORKFLOW初始化首提交，不编造SHA。"
        "发现已有书稿就接续原书，不覆盖或顺带迁移。"
        "你执行文件工具、研究、写作和审核，我只选平台、选题并确认首次开始。"
        "每章约6000汉字，同一天不限章数；以后我说下一章，你接续实际草稿并完成本章返修、冻结、GitHub保存和回读。"
        "使用当前GPT会话，不请求模型API，不自行建定时任务，不替我投稿，不承诺必签。\n").encode()
    files["INIT_MANIFEST.json"] = (json.dumps({"version": VERSION, "engine": "novel-v6", "files": {n: sha(v) for n, v in files.items()}}, ensure_ascii=False, indent=2) + "\n").encode()
    init = out / "初始化系统包.zip"
    archive(files, init)
    dist = frontend(out / "web")
    relay = (LEGACY / "web/server/github-relay.mjs").read_text()
    assets = {}
    types = {".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml", ".webmanifest": "application/manifest+json"}
    for p in sorted(dist.iterdir()):
        if p.suffix in types:
            text = p.read_text()
            if p.suffix == ".html":
                text = text.replace("<head>", '<head><meta name="novel-github-transport" content="relay">', 1)
            assets["/" + p.name] = [types[p.suffix] + "; charset=utf-8", text]
    # Retain the existing reference-library download, independently versioned.
    import sys
    sys.path.insert(0, str(LEGACY / "tools"))
    import make_init_package
    reference = out / "小说参考库初始化包.zip"
    make_init_package.build_library(LEGACY, reference)
    downloads = {"/downloads/novel-init.zip": init, "/downloads/novel-library-init.zip": reference}
    table = {url: {"base64": base64.b64encode(p.read_bytes()).decode(), "sha256": sha(p.read_bytes())} for url, p in downloads.items()}
    wrapper = """
export default {async fetch(request){
 const url=new URL(request.url);
 if(url.pathname==='/api/github')return handleGitHubRelay(request,{allowWrites:true});
 if(!['GET','HEAD'].includes(request.method))return new Response('Method not allowed',{status:405});
 const file=DOWNLOADS[url.pathname];
 if(file)return new Response(request.method==='HEAD'?null:Uint8Array.from(atob(file.base64),c=>c.charCodeAt(0)),{headers:{
  'Content-Type':'application/zip','Content-Disposition':'attachment; filename='+url.pathname.split('/').pop(),
  'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','X-Content-SHA256':file.sha256
 }});
 const asset=ASSETS[url.pathname==='/'?'/index.html':url.pathname];
 if(!asset)return new Response('Not found',{status:404});
 return new Response(request.method==='HEAD'?null:asset[1],{headers:{
  'Content-Type':asset[0],'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
  'X-Frame-Options':'DENY','Permissions-Policy':'camera=(), microphone=(), geolocation=()',
  'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self' https://api.github.com https://raw.githubusercontent.com; img-src 'self' data:; font-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
 }});
}};
"""
    worker = relay + "\nconst ASSETS=" + json.dumps(assets, ensure_ascii=False, separators=(",", ":")) + ";\nconst DOWNLOADS=" + json.dumps(table, separators=(",", ":")) + ";\n" + wrapper
    (out / "worker.mjs").write_text(worker)
    report = {"version": VERSION, "init_sha256": sha(init.read_bytes()), "init_bytes": init.stat().st_size, "kernel_lines": len((ROOT / "novel.py").read_text().splitlines()), "ui_version": "2.1.2", "legacy_ui_source": "system_templates/v4.6/web", "note": "旧版UI与参考库协议复用；写作内核从零编写，不导入旧工作锁"}
    (out / "BUILD.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    bundle = {"初始化系统包.zip": init.read_bytes(), "构建信息.json": (out / "BUILD.json").read_bytes()}
    for folder in ["research", "validation"]:
        for p in sorted((ROOT / folder).rglob("*")):
            if p.is_file():
                bundle[folder + "/" + p.relative_to(ROOT / folder).as_posix()] = p.read_bytes()
    for folder, label, filename in [
        ("opening-five", "V6.1 连续五章独立样稿", "V6.1_连续五章样稿_未采用.txt"),
        ("opening-five-v62", "V6.2 连续五章修订稿", "V6.2_连续五章修订稿_未采用.txt"),
    ]:
        sample_root = ROOT / "validation" / folder
        if not (sample_root / "样稿清单.json").exists():
            continue
        sample = json.loads((sample_root / "样稿清单.json").read_text())
        if [c["chapter"] for c in sample["chapters"]] != list(range(1, 6)):
            raise ValueError("连续五章清单必须按序包含1—5章")
        paragraphs = [label + "｜未采用\n\n本文件是系统验证与编辑练习，不替换XS1冻结章；没有平台签约或真人盲评结果。\n"]
        total = 0
        for c in sample["chapters"]:
            body = (sample_root / f"CH{c['chapter']:03}.txt").read_bytes()
            count = han(body.decode())
            if sha(body) != c["sha256"] or count != c["han"] or not 5500 <= count <= 6500:
                raise ValueError("样稿发生变更，请先更新真实清单")
            total += count
            paragraphs.append(f"第{c['chapter']}章 {c['title']}\n\n{body.decode().strip()}\n")
        if total != sample["total_han"]:
            raise ValueError("样稿总字数与清单不符")
        combined = "\n\n".join(paragraphs).encode()
        (out / filename).write_bytes(combined)
        bundle[filename] = combined
    bundle["使用说明.md"] = ("# 小说主V6重建版\n\n新书使用内含初始化系统包.zip；现有旧书继续原系统，不覆盖安装。\n\n工作台：https://novel-workspace-v44.qq1464356758.chatgpt.site/\n\n源码与复现： https://github.com/1464356758/xiaoshuoV5/tree/main/system_templates/v6\n\n从系统仓库运行python3 system_templates/v6/build_release.py --out 输出目录可重建。工作台界面兼容源仍在v4.6/web，写作核心为新编写的novel.py。\n\nresearch为调研取舍，validation为实际试稿和验证；试稿没有替换XS1冻结章，也未经过平台签约审核。\n").encode()
    archive(bundle, out / "小说主V6_重建版.zip")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    print(json.dumps(build(Path(p.parse_args().out).resolve()), ensure_ascii=False))
