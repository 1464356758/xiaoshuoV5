#!/usr/bin/env python3
"""Build B separately and add B-only routes; A assets/downloads remain byte-identical."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from cn_project import VERSION, ENGINE, PACKAGE_FILES, package_check


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def zip_files(files, path):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, raw)


def build(out):
    out = out.resolve()
    if out == ROOT or out.is_relative_to(ROOT) or ROOT.is_relative_to(out):
        raise ValueError('输出目录应位于B源码之外')
    if (out / 'web').exists() and not (out / '.cn-build').exists():
        raise ValueError('已有未知web目录，请使用空输出目录')
    out.mkdir(parents=True, exist_ok=True)
    (out / '.cn-build').touch()
    upstream = json.loads((ROOT / 'UPSTREAM.json').read_text())
    files = {name: (ROOT / name).read_bytes() for name in PACKAGE_FILES}
    for name, item in upstream['files'].items():
        raw = (ROOT / 'vendor/chinese-novelist' / name).read_bytes()
        if digest(raw) != item['sha256']:
            raise ValueError('上游原文与固定版本不符：' + name)
        files['vendor/chinese-novelist/' + name] = raw
    manifest = {'engine': ENGINE, 'version': VERSION, 'upstream_commit': upstream['commit'],
                'files': {name: digest(raw) for name, raw in files.items()}}
    files['CN_INIT_MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    initial = out / '初始化系统包_CN-GPT_对照版.zip'; zip_files(files, initial)
    with tempfile.TemporaryDirectory(prefix='cn-bundle-check-') as tmp:
        with zipfile.ZipFile(initial) as z:
            z.extractall(tmp)
        package_check(tmp)
    baseline = json.loads((ROOT / 'A_BASELINE.json').read_text())
    with tempfile.TemporaryDirectory(prefix='cn-preserved-a-') as tmp:
        a_out = Path(tmp) / 'a-release'
        subprocess.run([sys.executable, str(ROOT.parent / 'v6/build_release.py'), '--out', str(a_out)], check=True, capture_output=True)
        a_zip = (a_out / '初始化系统包.zip').read_bytes()
        if digest(a_zip) != baseline['initial_package_sha256']:
            raise ValueError('A初始化包发生变化，停止B打包')
        if digest((a_out / '小说主V6_重建版.zip').read_bytes()) != baseline['complete_package_sha256']:
            raise ValueError('A完整包发生变化，停止B打包')
        worker = (a_out / 'worker.mjs').read_text()
        prefix, content = worker.split('\nconst ASSETS=', 1)
        assets_json, content = content.split(';\nconst DOWNLOADS=', 1)
        downloads_json, suffix = content.split(';\n', 1)
        assets, downloads = json.loads(assets_json), json.loads(downloads_json)
        before_assets = dict(assets); before_downloads = dict(downloads)
        for path in sorted((ROOT / 'web').iterdir()):
            types = {'.html': 'text/html', '.mjs': 'text/javascript', '.css': 'text/css'}
            if path.suffix in types:
                text = path.read_text()
                if path.suffix == '.html':
                    text = text.replace('<head>', '<head><meta name="novel-github-transport" content="relay">', 1)
                assets['/' + path.name] = [types[path.suffix] + '; charset=utf-8', text]
        downloads['/downloads/cn-novel-init.zip'] = {'base64': base64.b64encode(initial.read_bytes()).decode(), 'sha256': digest(initial.read_bytes())}
        if any(assets[k] != v for k, v in before_assets.items()) or any(downloads[k] != v for k, v in before_downloads.items()):
            raise ValueError('B覆盖了A入口或下载')
        worker = prefix + '\nconst ASSETS=' + json.dumps(assets, ensure_ascii=False, separators=(',', ':')) + ';\nconst DOWNLOADS=' + json.dumps(downloads, separators=(',', ':')) + ';\n' + suffix
        (out / 'worker.mjs').write_text(worker)
        web = out / 'web'
        if web.exists(): shutil.rmtree(web)
        web.mkdir()
        for url, (_, text) in assets.items():
            (web / url.lstrip('/')).write_text(text)
    info = {'engine': ENGINE, 'version': VERSION, 'upstream_commit': upstream['commit'],
            'initial_sha256': digest(initial.read_bytes()), 'initial_bytes': initial.stat().st_size,
            'worker_sha256': digest(worker.encode()), 'a_initial_sha256': digest(a_zip), 'a_assets_unchanged': True,
            'b_entry': '/cn.html', 'b_download': '/downloads/cn-novel-init.zip'}
    (out / 'BUILD.json').write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n')
    if (ROOT / '双系统开书与对照说明.md').exists():
        (out / '双系统开书与对照说明.md').write_bytes((ROOT / '双系统开书与对照说明.md').read_bytes())
    return info


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--out', required=True)
    print(json.dumps(build(Path(p.parse_args().out)), ensure_ascii=False))
