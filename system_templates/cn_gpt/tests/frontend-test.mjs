import assert from 'node:assert/strict';
import {readFile,writeFile,unlink} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const [mode,web,root]=process.argv.slice(2),base=pathToFileURL(web+'/');
const {GitHubClient}=await import(new URL('hub-core.mjs',base));
const {loadCN,readCNChapter}=await import(new URL('cn-loader.mjs',base));
const {cnPrompt}=await import(new URL('cn-prompts.mjs',base));
const json=p=>readFile(root+'/'+p,'utf8').then(JSON.parse);
const client=new GitHubClient('https://github.com/example/synthetic-cn-front',{preferGit:false,fetcher:async value=>{
 const u=new URL(value);
 if(u.hostname==='api.github.com'&&u.pathname.includes('/commits/'))return new Response(JSON.stringify({sha:'a'.repeat(40)}));
 const prefix='/example/synthetic-cn-front/'+'a'.repeat(40)+'/';
 if(u.hostname==='raw.githubusercontent.com'&&u.pathname.startsWith(prefix)){
  try{return new Response(await readFile(root+'/'+decodeURIComponent(u.pathname.slice(prefix.length))))}catch(e){if(e.code==='ENOENT')return new Response('',{status:404});throw e;}
 }
 return new Response('',{status:404});
}});
const load=()=>loadCN(client.repo.url,{client,branch:'main'});
if(mode==='prompt'){
 for(const repo of ['XS-KU.git','XS-GL','xiaoshuoV5','xiaishuo-ZUOZONG'])assert.throws(()=>cnPrompt('https://github.com/1464356758/'+repo));
 const text=cnPrompt(client.repo.url);assert.match(text,/CN_INIT_MANIFEST/);assert.match(text,/02-写作计划.json/);assert.match(text,/逐章A—D/);assert.match(text,/5500—6500/);
 assert.match(cnPrompt(client.repo.url,{mode:'continue'}),/B\/CN-GPT/);
}else if(mode==='stale'){
 const m=await json('cn-project.json'),path=m.projectPath+'/02-写作计划.json',p=await json(path);p.chapters[1].title='远端新规划';await writeFile(root+'/'+path,JSON.stringify(p));
 await assert.rejects(load,/落后/);
}else if(mode==='title'){
 const p=await json('online/index.json');p.chapters[0].title='虚假的阅读标题';await writeFile(root+'/online/index.json',JSON.stringify(p));await assert.rejects(load);
}else{
 const book=await load();
 if(mode==='missing'){
  const r=await json(book.cnPlan.chapters[0].recordPath);await unlink(root+'/'+r.attachments['03-文风基准.md'].path);await assert.rejects(()=>readCNChapter(book,1));
 }else if(mode==='body'){
  await writeFile(root+'/'+book.manifest.chapters[0].text_path,'已被改动。');await assert.rejects(()=>readCNChapter(book,1));
 }else{
  const c=await readCNChapter(book,1);assert.equal(c.han,6000);assert.equal(c.text,await readFile(root+'/'+book.manifest.chapters[0].text_path,'utf8'));
 }
}
