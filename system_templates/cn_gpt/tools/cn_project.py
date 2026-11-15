#!/usr/bin/env python3
"""GPT/GitHub adapter for the upstream 02-写作计划.json; no model calls."""
import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

VERSION = '1.0.0'
ENGINE = 'cn-novelist-gpt'
UPSTREAM = '507d41567925eab520ad459db08fda83813e8051'
PLAN = '02-写作计划.json'
DOCS = ['00-人物档案.md', '01-大纲.md', '03-文风基准.md', '99-章节摘要.md']
START, END = '<!-- CN_BODY_START -->\n', '\n<!-- CN_BODY_END -->'
PACKAGE_FILES = {'AGENTS.md', 'GPT_WORKFLOW.md', 'README.md', 'UPSTREAM_CHANGES.md',
                 'UPSTREAM.json', 'A_BASELINE.json', '启动CN新书.txt', 'tools/cn_project.py'}


class Problem(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise Problem(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def han(text):
    return sum(0x3400 <= ord(c) <= 0x4dbf or 0x4e00 <= ord(c) <= 0x9fff
               or 0x20000 <= ord(c) <= 0x323af for c in text)


def repository(value):
    value = value.strip().rstrip('/')
    if value.lower().endswith('.git'):
        value = value[:-4]
    need(bool(re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value)), '请提供GitHub仓库首页')
    need(value.split('/')[-1].lower() not in {'xiaoshuov5', 'xs-ku', 'xs-gl', 'xiaishuo-zuozong'}, '系统、教材和管理仓库不能作小说目标')
    need(all(p not in {'.', '..'} for p in value.split('/')[-2:]), '仓库路径无效')
    return value


def branch(value):
    need(bool(re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_./-]{0,199}', value)) and value != 'HEAD'
         and '..' not in value and '//' not in value and not value.endswith(('/', '.'))
         and all(not p.startswith('.') and not p.endswith('.lock') for p in value.split('/')), '请核实实际默认分支')
    return value


def clean_title(value):
    need(isinstance(value, str) and value.strip() and len(value) <= 120 and not any(ord(c) < 32 for c in value), '章节标题无效')
    return value.strip()


def chapter_name(number, title):
    name = re.sub(r'[^\w\u3400-\u9fff-]', '_', clean_title(title))[:80]
    return f'第{number:02}章-{name}.md'


def body(markdown):
    need(markdown.count(START) == 1 and markdown.count(END) == 1, '章节须有唯一CN正文起止标记')
    start = markdown.index(START) + len(START)
    end = markdown.index(END)
    need(end >= start, '正文标记顺序错误')
    return markdown[start:end].encode()


class Project:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def path(self, name):
        need(isinstance(name, str) and name and not Path(name).is_absolute() and '\\' not in name
             and all(p and p not in {'.', '..'} for p in name.split('/')), '非法项目路径')
        p = self.root / name
        need(p.resolve().is_relative_to(self.root), '路径不能越过小说目录')
        return p

    def read(self, name):
        return self.path(name).read_bytes()

    def data(self, name):
        value = json.loads(self.read(name))
        need(isinstance(value, dict), name + '应为JSON对象，未重建状态')
        return value

    def write(self, name, raw, immutable=False):
        p = self.path(name)
        if immutable and p.exists():
            need(p.read_bytes() == raw, '冻结对象冲突：' + name)
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix='.cn-', dir=p.parent)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(raw); f.flush(); os.fsync(f.fileno())
            os.replace(temp, p)
            directory = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    @contextlib.contextmanager
    def lock(self):
        import fcntl
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / '.cn.lock').open('a') as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as e:
                raise Problem('另一保存操作正在执行，请稍后重读') from e
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def metadata(self):
        m = self.data('cn-project.json')
        need(m.get('engine') == ENGINE and m.get('upstreamCommit') == UPSTREAM, '不是本CN-GPT项目，不能混用引擎')
        need(bool(re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}', m['bookId'])), '作品身份无效')
        repository(m['repository']); branch(m['branch'])
        need(m['projectPath'].startswith('chinese-novelist/'), '缺少上游项目目录')
        self.path(m['projectPath'])
        return m

    def snapshot(self):
        m = self.metadata(); raw = self.read(m['projectPath'] + '/' + PLAN)
        p = json.loads(raw)
        need(isinstance(p, dict) and p.get('engine') == ENGINE and p.get('bookId') == m['bookId']
             and p.get('projectPath') == m['projectPath'] and p.get('novelName') == m['novelName'], '写作计划与作品身份不符')
        need(type(p.get('totalChapters')) is int and 1 <= p['totalChapters'] <= 2000
             and isinstance(p.get('chapters'), list) and len(p['chapters']) == p['totalChapters'], '章节规划数量不符')
        need(p.get('writingMode') == 'serial' and p.get('minWordsPerChapter') == 5500
             and p.get('maxWordsPerChapter') == 6500, 'GPT适配版规格不符')
        unfinished = False; active = 0
        for number, c in enumerate(p['chapters'], 1):
            need(c.get('chapterNumber') == number and c.get('status') in {'pending', 'in_progress', 'failed', 'completed'}, '章序或状态无效')
            need(type(c.get('retryCount')) is int and 0 <= c['retryCount'] <= 3, '返修计数无效')
            if c['status'] == 'completed':
                need(not unfinished, '不能越过未完成章采用后章')
            else:
                unfinished = True
                if c['status'] != 'pending':
                    need(active == 0 and all(x['status'] == 'completed' for x in p['chapters'][:number-1]), '同时存在多个开写目标')
                    active += 1
            if c['status'] != 'pending':
                need(c['filePath'] == chapter_name(number, c['title'])
                     and bool(re.fullmatch(r'[A-Za-z0-9_.:-]{8,180}', c.get('requestId', ''))), '章节文件或请求身份无效')
        need(p.get('status') in {'planning', 'in_progress', 'completed'}
             and (p['status'] == 'completed') == (not unfinished), '全书状态与实际章节不符')
        return m, p, sha(raw)

    def save_plan(self, m, p):
        p['updatedAt'] = now()
        self.write(m['projectPath'] + '/' + PLAN, json_bytes(p))

    def create(self, repo, target_branch, title, platform, chapters=150):
        repo, target_branch = repository(repo), branch(target_branch)
        need(title.strip() and len(title) <= 120 and platform.strip() and len(platform) <= 80
             and 1 <= chapters <= 2000, '请先选题和平台，章数为1—2000')
        with self.lock():
            if self.path('cn-project.json').exists():
                m = self.metadata()
                need((m['repository'], m['branch'], m['novelName'], m['platform']) == (repo, target_branch, title.strip(), platform.strip()), '已有作品，不能换身份重建')
            else:
                need(not any(self.path(n).exists() for n in ['book', 'vault', 'project_config.json', 'chinese-novelist']), '已有作品或旧系统，不覆盖部署')
                ident = str(uuid.uuid4()); stamp = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime('%Y%m%d-%H%M%S')
                slug = re.sub(r'[^\w\u3400-\u9fff-]', '_', title)[:40]
                m = {'engine': ENGINE, 'version': VERSION, 'upstreamCommit': UPSTREAM, 'bookId': ident,
                     'repository': repo, 'branch': target_branch, 'novelName': title.strip(), 'platform': platform.strip(),
                     'projectPath': f'chinese-novelist/{stamp}-{slug}-{ident[:8]}', 'createdAt': now()}
                self.write('cn-project.json', json_bytes(m))
            path = m['projectPath']
            if not self.path(path + '/' + PLAN).exists():
                need(not list(self.path(path).glob('第*章-*.md')), '计划丢失但已有章节，请从Git历史恢复，未追认完成')
                p = {'version': 1, 'engine': ENGINE, 'bookId': m['bookId'], 'novelName': m['novelName'], 'projectPath': path,
                     'totalChapters': chapters, 'minWordsPerChapter': 5500, 'maxWordsPerChapter': 6500,
                     'createdAt': m['createdAt'], 'updatedAt': now(), 'status': 'planning', 'writingMode': 'serial',
                     'chapters': [{'chapterNumber': n, 'title': f'待定第{n}章', 'filePath': '', 'status': 'pending',
                                   'wordCount': None, 'wordCountPass': None, 'retryCount': 0} for n in range(1, chapters + 1)]}
                self.write(path + '/' + PLAN, json_bytes(p))
            for name in DOCS:
                if not self.path(path + '/' + name).exists():
                    text = '# ' + name[3:-3] + '\n\n' + ('<!-- CN_PENDING -->\n请按原项目模板完成此文件。\n' if name != '99-章节摘要.md' else '按章保存事件后果、人物处境、知情与未了事项。\n')
                    self.write(path + '/' + name, text.encode())
            if not self.path('user-preferences.json').exists():
                self.write('user-preferences.json', json_bytes({'version': 1, 'preferences': {'favoriteGenres': [], 'preferredPerspective': '', 'preferredTone': '', 'dislikes': []}}))
            ignore = self.read('.gitignore').decode() if self.path('.gitignore').exists() else ''
            missing = [s for s in ['.cn.lock', '__pycache__/', '*.pyc'] if s not in ignore.splitlines()]
            if missing:
                self.write('.gitignore', (ignore + ('\n' if ignore and not ignore.endswith('\n') else '') + '\n'.join(missing) + '\n').encode())
            self.views()
            return self.context()

    def verify(self):
        m, p, baseline = self.snapshot(); previous = None; requests = set()
        for c in p['chapters']:
            if c['status'] != 'completed':
                continue
            raw = self.read(c['recordPath']); r = json.loads(raw)
            need(sha(raw) == c['recordSha256'] and c['recordPath'] == m['projectPath'] + '/99-冻结记录/' + c['recordSha256'] + '.json', '冻结记录被改动')
            expected = {k: v for k, v in c.items() if k not in {'recordPath', 'recordSha256'}}
            need(r.get('engine') == ENGINE and r.get('bookId') == m['bookId'] and r['chapter'] == expected
                 and r['previousRecordSha256'] == previous and c['requestId'] not in requests, '冻结绑定或请求历史不符')
            requests.add(c['requestId'])
            markdown = self.read(m['projectPath'] + '/' + c['filePath'])
            need(markdown.decode().startswith(f"# 第{c['chapterNumber']:02}章：{c['title']}\n"), '冻结Markdown标题不符')
            plain = body(markdown.decode('utf-8'))
            need(sha(markdown) == c['markdownSha256'] and sha(plain) == c['textSha256'] and han(plain.decode()) == c['wordCount']
                 and 5500 <= c['wordCount'] <= 6500 and c['wordCountPass'] is True, '已完成章节被改动或字数不符')
            need(set(r['attachments']) == set(DOCS + ['markdown', 'text', 'editorial', 'assessment']), '冻结资料缺失')
            for item in r['attachments'].values():
                need(item['path'] == m['projectPath'] + '/99-冻结记录/objects/' + item['sha256'] + '.txt'
                     and sha(self.read(item['path'])) == item['sha256'], '冻结资料快照被改动')
            a = json.loads(self.read(r['attachments']['assessment']['path']))
            need(a['decision'] == 'ready' and a['reviewer'] == 'same-context-model' and a['chapter'] == c['chapterNumber']
                 and a['planSha256'] == c['assessedPlanSha256'] and a['hashes']['markdown'] == c['markdownSha256']
                 and a['hashes']['text'] == c['textSha256'], '审稿未绑定正式正文')
            for key in DOCS + ['editorial']:
                need(a['hashes'][key] == r['attachments'][key]['sha256'], '审读资料绑定不符')
            need(r['attachments']['markdown']['sha256'] == c['markdownSha256']
                 and r['attachments']['text']['sha256'] == c['textSha256'], '原稿不可变副本与正式章不符')
            previous = c['recordSha256']
        return {'status': 'integrity_ok', 'chapters': len(requests), 'plan_sha256': baseline, 'book_id': m['bookId']}

    def context(self):
        self.verify(); m, p, baseline = self.snapshot()
        target = next((c for c in p['chapters'] if c['status'] != 'completed'), None)
        return {'engine': ENGINE, 'project': m, 'plan_sha256': baseline, 'target': target,
                'read_paths': [m['projectPath'] + '/' + n for n in DOCS], 'status': p['status']}

    def begin(self, request, title):
        need(bool(re.fullmatch(r'[A-Za-z0-9_.:-]{8,180}', request)), '需要本次真实生成的稳定请求编号')
        with self.lock():
            self.verify(); m, p, baseline = self.snapshot()
            old = next((c for c in p['chapters'] if c.get('requestId') == request and c['status'] == 'completed'), None)
            if old:
                self.views(); return {'status': 'already_completed', 'chapter': old['chapterNumber']}
            c = next((c for c in p['chapters'] if c['status'] != 'completed'), None)
            need(c, '全书目标已完成')
            for name in DOCS[:3]:
                raw = self.read(m['projectPath'] + '/' + name).decode()
                need(raw.strip() and '<!-- CN_PENDING -->' not in raw, '先完成上游人物档案、大纲和文风基准：' + name)
            if c['status'] == 'pending':
                c['title'] = clean_title(title); c['filePath'] = chapter_name(c['chapterNumber'], c['title'])
                need(not list(self.path(m['projectPath']).glob(f"第{c['chapterNumber']:02}章-*.md")), '发现未绑定的章节文件，先恢复原计划，不能认领旧稿')
                c.update(status='in_progress', requestId=request, startedAt=now(), startPlanSha256=baseline)
                p['status'] = 'in_progress'; self.save_plan(m, p)
                result = 'new'
            else:
                result = 'resume'
            chapter = m['projectPath'] + '/' + c['filePath']
            if not self.path(chapter).exists():
                self.write(chapter, (f"# 第{c['chapterNumber']:02}章：{c['title']}\n\n## 本章概要\n\n## 正文\n" + START + END + '\n\n## 章节备注\n').encode())
            self.views()
            return {'status': result, 'chapter': c['chapterNumber'], 'request_id': c['requestId'], 'file_path': chapter, 'plan_sha256': self.snapshot()[2]}

    def current(self, expected):
        m, p, baseline = self.snapshot(); need(baseline == expected, '计划已变，请重读，不覆盖其他结果')
        c = next((c for c in p['chapters'] if c['status'] != 'completed'), None)
        need(c and c['status'] in {'in_progress', 'failed'}, '先begin接续当前目标')
        return m, p, c

    def materials(self, m, c):
        path = m['projectPath']; markdown = self.read(path + '/' + c['filePath'])
        need(markdown.decode().startswith(f"# 第{c['chapterNumber']:02}章：{c['title']}\n"), '章节Markdown标题与计划不符')
        files = {'markdown': markdown, 'text': body(markdown.decode('utf-8'))}
        files.update({n: self.read(path + '/' + n) for n in DOCS})
        files['editorial'] = self.read(path + f"/98-编辑意见/第{c['chapterNumber']:02}章.md")
        need(all(v.decode('utf-8').replace('\ufeff', '').strip() and b'<!-- CN_PENDING -->' not in v for v in files.values()), '正文或规划/审读材料尚未完成')
        need(5500 <= han(files['text'].decode()) <= 6500, '正文应为5500—6500汉字，概要和备注不计入')
        need(len(files['editorial'].decode()) <= 3000, '编辑意见只保留具体问题、修改与风险')
        need(bool(re.search(r'^## 第0*' + str(c['chapterNumber']) + r'章(?:[：:\s]|$)', files['99-章节摘要.md'].decode(), re.M)), '章节摘要缺少当前章记录')
        if c['chapterNumber'] > 1:
            prior = self.snapshot()[1]['chapters'][c['chapterNumber'] - 2]
            record = self.data(prior['recordPath'])
            old_summary = self.read(record['attachments']['99-章节摘要.md']['path'])
            need(files['99-章节摘要.md'].startswith(old_summary), '已完成章摘要不能回改；本章前向追加处理')
        return files

    def assess(self, expected, decision):
        need(decision in {'ready', 'revise'}, '审读结论无效')
        with self.lock():
            self.verify(); m, p, c = self.current(expected); files = self.materials(m, c)
            hashes = {k: sha(v) for k, v in files.items()}; path = m['projectPath'] + f"/98-编辑意见/第{c['chapterNumber']:02}章.assessment.json"
            if self.path(path).exists():
                old = self.data(path)
                if old.get('hashes') == hashes and old.get('decision') == decision and old.get('planSha256') == expected:
                    return old
            if decision == 'revise':
                need(c['retryCount'] < 3, '已达3轮返修，保留未完成与问题，不能强行采用')
                c['retryCount'] += 1; c['status'] = 'failed'; self.save_plan(m, p); expected = self.snapshot()[2]
            a = {'engine': ENGINE, 'chapter': c['chapterNumber'], 'decision': decision, 'reviewer': 'same-context-model',
                 'planSha256': expected, 'hashes': hashes, 'assessedAt': now(), 'note': '模型审读不是独立读者或签约认证'}
            self.write(path, json_bytes(a)); return a

    def adopt(self, expected, request):
        with self.lock():
            self.verify(); m, p, baseline = self.snapshot()
            for c in p['chapters']:
                if c['status'] == 'completed' and c.get('requestId') == request:
                    self.views(); return {'status': 'already_completed', 'chapter': c['chapterNumber']}
            m, p, c = self.current(expected); need(c['requestId'] == request, '请求与目标章不符')
            files = self.materials(m, c); a_path = m['projectPath'] + f"/98-编辑意见/第{c['chapterNumber']:02}章.assessment.json"
            a_raw = self.read(a_path); a = json.loads(a_raw)
            need(a.get('engine') == ENGINE and a.get('reviewer') == 'same-context-model' and a.get('decision') == 'ready'
                 and a.get('chapter') == c['chapterNumber'] and a.get('planSha256') == expected
                 and a.get('hashes') == {k: sha(v) for k, v in files.items()}, '审读后材料有变或仍待修订，请重新审读')
            attachments = {}
            for key, raw in {**files, 'assessment': a_raw}.items():
                name = m['projectPath'] + '/99-冻结记录/objects/' + sha(raw) + '.txt'
                self.write(name, raw, immutable=True); attachments[key] = {'path': name, 'sha256': sha(raw)}
            c.update(status='completed', wordCount=han(files['text'].decode()), wordCountPass=True,
                     markdownSha256=sha(files['markdown']), textSha256=sha(files['text']), frozenAt=now(), assessedPlanSha256=expected)
            prior = p['chapters'][c['chapterNumber'] - 2].get('recordSha256') if c['chapterNumber'] > 1 else None
            r = {'engine': ENGINE, 'bookId': m['bookId'], 'chapter': dict(c), 'attachments': attachments, 'previousRecordSha256': prior}
            raw = json_bytes(r); name = m['projectPath'] + '/99-冻结记录/' + sha(raw) + '.json'
            self.write(name, raw, immutable=True); c.update(recordPath=name, recordSha256=sha(raw))
            p['status'] = 'completed' if all(x['status'] == 'completed' for x in p['chapters']) else 'in_progress'
            self.save_plan(m, p)  # The upstream writing plan is the sole adoption point.
            self.views()
            return {'status': 'completed', 'chapter': c['chapterNumber'], 'han': c['wordCount'], 'book_id': m['bookId']}

    def views(self):
        self.verify(); m, p, baseline = self.snapshot(); chapters = []; state_chapters = {}
        for c in p['chapters']:
            if c['status'] != 'completed':
                continue
            plain = body(self.read(m['projectPath'] + '/' + c['filePath']).decode())
            path = f"book/chapters/CH{c['chapterNumber']:03}_{c['textSha256']}.txt"
            self.write(path, plain, immutable=True)
            item = {'number': c['chapterNumber'], 'title': c['title'], 'han_count': c['wordCount'], 'sha256': c['textSha256'], 'text_path': path, 'publication_status': 'unconfirmed'}
            chapters.append(item); state_chapters[str(c['chapterNumber'])] = {'number': c['chapterNumber'], 'title': c['title'], 'text_sha256': c['textSha256'], 'text_path': path[5:], 'record_path': c['recordPath'], 'record_sha256': c['recordSha256'], 'frozen_at': c['frozenAt']}
        active = next((c for c in p['chapters'] if c['status'] != 'completed'), None)
        state = {'schema': 'cn-gpt-reading-view', 'view_only': True, 'book_id': m['bookId'], 'chapters': state_chapters,
                 'cn_plan_path': m['projectPath'] + '/' + PLAN, 'cn_plan_sha256': baseline, 'cn_project_sha256': sha(self.read('cn-project.json'))}
        raw = json_bytes(state); self.write('book/state.json', raw)
        index = {'schema_version': 1, 'engine': ENGINE, 'initialized': True, 'book': {'id': m['bookId'], 'title': m['novelName'], 'platform': m['platform']},
                 'progress': {'adopted_chapters': len(chapters), 'actual_han': sum(x['han_count'] for x in chapters), 'target_chapters': p['totalChapters'], 'target_han': 6000*p['totalChapters']},
                 'task': {'phase': 'COMPLETE' if not active else 'WRITING' if active['status'] != 'pending' else 'WAITING_NEXT' if chapters else 'PLANNING', 'label': 'CN-GPT上游写作计划', 'next_action': '读取GPT_WORKFLOW.md'},
                 'source': {'repository_url': m['repository'], 'branch': m['branch'], 'state_sha256': sha(raw)}, 'chapters': chapters, 'generated_at': p['updatedAt']}
        self.write('online/index.json', json_bytes(index)); return index


def package_check(root):
    b = Project(root); m = b.data('CN_INIT_MANIFEST.json')
    need(m.get('engine') == ENGINE and m.get('version') == VERSION and isinstance(m.get('files'), dict), 'CN初始化包版本不匹配')
    u = b.data('UPSTREAM.json'); need(u['commit'] == UPSTREAM and len(u['files']) == 22
                                    and 'references/flows/chapter-checklist.md' in u['files'], '上游固定版本或运行文件不完整')
    need(set(m['files']) == PACKAGE_FILES | {'vendor/chinese-novelist/' + n for n in u['files']}, 'CN包清单不完整')
    for name, expected in m['files'].items():
        need(sha(b.read(name)) == expected, '初始化文件缺失或被改动：' + name)
    for name, meta in u['files'].items():
        need(sha(b.read('vendor/chinese-novelist/' + name)) == meta['sha256'], '上游原文被改动：' + name)
    return {'status': 'package_ok', 'engine': ENGINE, 'version': VERSION, 'upstream_commit': UPSTREAM}


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--root', default='.')
    sub = p.add_subparsers(dest='command', required=True)
    create = sub.add_parser('create'); create.add_argument('--repository', required=True); create.add_argument('--branch', required=True)
    create.add_argument('--title', required=True); create.add_argument('--platform', required=True); create.add_argument('--chapters', type=int, default=150)
    begin = sub.add_parser('begin'); begin.add_argument('--request', required=True); begin.add_argument('--title', required=True)
    assess = sub.add_parser('assess'); assess.add_argument('--expect', required=True); assess.add_argument('--decision', choices=['ready', 'revise'], required=True)
    adopt = sub.add_parser('adopt'); adopt.add_argument('--expect', required=True); adopt.add_argument('--request', required=True)
    for cmd in ['status', 'context', 'verify', 'index', 'package-check']:
        sub.add_parser(cmd)
    a = p.parse_args(); b = Project(a.root)
    try:
        if a.command == 'create': result = b.create(a.repository, a.branch, a.title, a.platform, a.chapters)
        elif a.command == 'begin': result = b.begin(a.request, a.title)
        elif a.command == 'assess': result = b.assess(a.expect, a.decision)
        elif a.command == 'adopt': result = b.adopt(a.expect, a.request)
        elif a.command == 'package-check': result = package_check(a.root)
        elif a.command == 'index':
            with b.lock(): result = b.views()
        elif a.command in {'status', 'context'}: result = b.context()
        else: result = b.verify()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (Problem, OSError, KeyError, TypeError, AttributeError, UnicodeDecodeError, json.JSONDecodeError) as e:
        p.exit(1, '未完成：' + str(e) + '\n')


if __name__ == '__main__':
    main()
