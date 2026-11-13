import assert from 'node:assert/strict';
import {readFile,writeFile,unlink} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import vm from 'node:vm';

const [mode,web,root]=process.argv.slice(2),base=pathToFileURL(web+'/');
const hub=await import(new URL('hub-core.mjs',base));
const prompts=await import(new URL('prompts.mjs',base));
const json=p=>readFile(root+'/'+p,'utf8').then(JSON.parse);
const client=new hub.GitHubClient('https://github.com/example/synthetic-release',{
 preferGit:false,
 fetcher:async value=>{
  const u=new URL(value);
  if(u.hostname==='api.github.com'&&u.pathname.includes('/commits/'))return new Response(JSON.stringify({sha:'a'.repeat(40)}));
  const prefix='/example/synthetic-release/'+'a'.repeat(40)+'/';
  if(u.hostname==='raw.githubusercontent.com'&&u.pathname.startsWith(prefix)){
   const path=decodeURIComponent(u.pathname.slice(prefix.length));
   try{return new Response(await readFile(root+'/'+path));}catch(e){if(e.code==='ENOENT')return new Response('',{status:404});throw e;}
  }
  return new Response('',{status:404});
 }
});

if(mode==='protected'){
 for(const repo of ['XS-GL','XS-KU.git','xiaoshuoV5','xiaishuo-ZUOZONG'])
  assert.throws(()=>hub.newBookPrompt({repository:'https://github.com/1464356758/'+repo}));
 assert.match(hub.newBookPrompt({repository:'https://github.com/example/synthetic-new-book'}),/synthetic-new-book/);
}else if(mode==='bytes'){
 const book=await hub.loadBook(client,'main'),chapter=book.manifest.chapters[0];
 assert.equal(await hub.readFormalChapter(client,book,chapter),await readFile(root+'/'+chapter.text_path,'utf8'));
}else if(mode==='attachments'){
 const book=await hub.loadBook(client,'main'),c=book.state.chapters['1'];
 const record=await json('book/'+c.record_path);
 await unlink(root+'/'+record.attachments.memory);
 await assert.rejects(()=>hub.readFormalChapter(client,book,book.manifest.chapters[0]));
}else if(mode==='title'){
 const manifest=await json('online/index.json');manifest.chapters[0].title='与正式状态不同的标题';
 await writeFile(root+'/online/index.json',JSON.stringify(manifest));
 await assert.rejects(()=>hub.loadBook(client,'main'));
}else if(mode==='pending'){
 const state=await json('book/state.json');
 const entry={id:'synthetic-release',repository_url:'https://github.com/example/synthetic-release',branch:'main',book_id:state.book_id,title:state.title,enabled:true,effective_from:'2026-11-01',expected_time:'09:00',grace_minutes:0};
 const result=await hub.inspectBook(entry,{client,now:new Date('2026-11-14T02:00:00Z')});
 assert.equal(result.status,'updated',JSON.stringify(result));
 assert.match(result.reason,/草稿|接续|未完成/);
}else if(mode==='orphan'){
 await unlink(root+'/book/work/CH002/task.json');
 const state=await json('book/state.json');
 const result=await hub.inspectExecution({repository_url:'https://github.com/example/synthetic-release',branch:'main',book_id:state.book_id},{client,now:new Date('2026-11-14T02:00:00Z')});
 assert.equal(result.status,'unknown',JSON.stringify(result));
 assert.match(result.reason,/草稿|任务/);
}else if(mode==='manual'){
 const source=await readFile(new URL('hub.js',base),'utf8');
 const fn=source.slice(source.indexOf('function updateWritingPrompt('),source.indexOf('function openWritingPrompt('));
 for(const [mode,time,disabled] of [['manual','',false],['scheduled','',true],['scheduled','09:00',false]]){
  const fields=new Map(),get=id=>{if(!fields.has(id))fields.set(id,{value:'',textContent:'',disabled:false});return fields.get(id);};
  get('writingMode').value=mode;get('writingTime').value=time;
  const book={id:'synthetic',title:'临时测试',expected_time:'09:00'};
  const context={...prompts,$:get,selectedBook:()=>book,promptBookId:'synthetic',writingPrompt:()=> '临时测试指令',config:{repository_url:'https://github.com/example/manager'},state:{registry:{books:[book]}},legacy:{},executionTicket:0,executionBusy:false};
  vm.runInNewContext(fn+'\nupdateWritingPrompt();',context);
  assert.equal(get('copyWritingPrompt').disabled,disabled,mode+' '+time);
 }
}else throw new Error('Unknown synthetic test mode');
console.log('PASS '+mode);
