#!/usr/bin/env python3
"""重建V4.6的五个组件及完整交付包；不操作现有小说。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "system_templates/v4.6"
sys.path.insert(0, str(TEMPLATE / "tools"))
import build_web_package
from release_source_guard import assert_clean_source


def build(out_dir):
    out = Path(out_dir).resolve(); out.mkdir(parents=True, exist_ok=True)
    version = assert_clean_source(ROOT, ["system_templates/v4.6", "tools/build_v46_release.py", "release_checks/V4.6.json", "release_checks/python-v46.log", "release_checks/node-v46.log"])
    components = build_web_package.build(TEMPLATE, out)
    profile = json.loads((TEMPLATE / "reference_library/XS-KU.json").read_text())
    validation = json.loads((ROOT / "release_checks/V4.6.json").read_text())
    config = json.loads((TEMPLATE / "project_config.json").read_text())
    manifest = {"format": "novel-system-release-v1", "system_version": config["system_version"], "patch_version": config.get("patch_version"), "workspace_version": config["workspace_version"],
                "source": {"repository_url": "https://github.com/1464356758/xiaoshuoV5", "commit": version,
                           "template_path": "system_templates/v4.6"}, "reference_library": profile["origin"],
                "indexed": profile["indexed"], "declared_study_scope": profile["declared_study_scope"],
                "validation": validation, "components": {}}
    for name, item in components.items():
        path = Path(item["path"])
        manifest["components"][name] = {"filename": path.name, "size_bytes": path.stat().st_size,
                                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    (out / "交付清单.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    instructions = '''小说库与创作系统 V4.6.1 · XS-KU 实库修正版

开始一本新书：只需把“初始化系统包.zip”交给新的GPT工作聊天，并提供独立的新书GitHub仓库链接。包内《启动新书.txt》已填写XS-KU绑定；GPT负责部署、查库、阅读、选题、规划、写作与审读，你只选择平台、选题并授权开始写。

五个组件：
1. 初始化系统包.zip：空的新书系统，已绑定XS-KU，不含旧作品身份、章节或任务。
2. 小说参考库初始化包.zip：用于另建参考库或按文件更新工具。XS-KU已经初始化，不能用空包清空或重建它。
3. 个人管理端部署包.zip：工作台1.4.7，带V4.6新书指令及两种初始化包下载。
4. 代发端部署包.zip：只读阅读与复制正式章节，不写小说。
5. 管理仓库初始化包.zip：空的多书清单。

写作怎样用上小说库：按当前难题检索→实际回读原文→提炼适用写法→任务书写明本书人物、办法及代价→写完整章→用本章证据核对效果和原创性→原有审核通过才冻结。查不到教材时继续读候选原文并补建记录。

参考库本次索引171份原文、168组书名作者、74608个网页阅读单元。首批教材12条来自6本书的开篇9个单元；其余按任务实际阅读。索引不等于通读，也不是模型参数训练。签约结果仍须实际投稿验证。

旧作品的冻结正文与事实记录继续只读，不用空包覆盖已有小说。包内不含模型API密钥，不会自动建立计划或投稿。网页部署包已重建，原有在线网址是否升级另据真实部署记录；本次没有更改既有网站。

V4.6.1复查修复了教材路径校验、备份工具缺失、旧书说明混入空包、未跟踪源文件混入发布包四类问题。

复现命令、实际源码提交与测试结果见交付清单.json。每个组件内也有文件哈希清单。
'''
    (out / "先读我.txt").write_text(instructions)
    bundle = out / "小说库与创作系统_V4.6.zip"
    files = [Path(value["path"]) for value in components.values()] + [out / "交付清单.json", out / "先读我.txt"]
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == 7
        for item in manifest["components"].values():
            assert hashlib.sha256(archive.read(item["filename"])).hexdigest() == item["sha256"]
    return {"path": str(bundle), "bytes": bundle.stat().st_size,
            "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(), "source": manifest["source"],
            "reference_library": manifest["reference_library"], "validation": validation}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True)
    print(json.dumps(build(parser.parse_args().out_dir), ensure_ascii=False, indent=2))
