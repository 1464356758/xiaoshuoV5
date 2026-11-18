import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const root = new URL('../', import.meta.url);
const source = await readFile(new URL('dist/server/index.js',root),'utf8');
const release = JSON.parse(await readFile(new URL('RELEASE.json',root),'utf8'));
const worker = (await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;
const request = (p, method='GET') => worker.fetch(new Request('https://workspace.invalid'+p,{method}));
const home = await (await request('/')).text();
assert.match(home,/href=".\/a7.html"/);
const page = await (await request('/a7.html')).text();
for (const p of ['/a7.mjs','/a7.css','/downloads/a7-novel-init.zip']) {
  assert.ok(page.includes('.'+p));
  assert.equal((await request(p)).status,200,p);
}
const bytes = Buffer.from(await (await request('/downloads/a7-novel-init.zip')).arrayBuffer());
const head = await request('/downloads/a7-novel-init.zip','HEAD');
const hash = createHash('sha256').update(bytes).digest('hex');
assert.equal(head.headers.get('X-Content-SHA256'),hash);
assert.match(head.headers.get('Content-Disposition'),/V7\.0.zip/);
assert.equal(await head.text(),'');
assert.equal(hash,release.a7_init_package_sha256);
const contents = spawnSync('python3',['-c',
  "import io,sys,zipfile,json,hashlib;z=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()));m=json.loads(z.read('INIT_MANIFEST.json'));assert m['edition']=='novel-a7' and m['version']=='7.0.1';assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in m['files'].items())"
],{input:bytes});
assert.equal(contents.status,0,contents.stderr.toString());
const script = await (await request('/a7.mjs')).text();
const {promptFor} = await import('data:text/javascript;base64,'+Buffer.from(script).toString('base64'));
const demo='https://github.com/example-fiction/test';
assert.match(promptFor(demo,'new'),/初始化系统包_A版_V7.0.zip/);
assert.match(promptFor(demo,'new'),/7\.0\.1/);
assert.match(page,/A 系统 V7\.0\.1/);
assert.match(home,/A 版 V7\.0\.1 开书与下载/);
assert.match(promptFor(demo,'resume'),/novel-a7/);
assert.doesNotMatch(promptFor(demo,'resume'),/version=7\.0/);
for (const bad of ['https://github.com/1464356758/XS-KU','https://github.com/1464356758/xiaoshuoV5','https://example.com/fake/book']) {
  assert.throws(()=>promptFor(bad,'new'));
}
assert.match(await (await request('/prompts.mjs')).text(),/novel-a7/);
console.log('A7 个人端入口、独立仓库、续写指令、下载类型及包指纹核验通过');
