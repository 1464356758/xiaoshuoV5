import {GitHubClient,loadBook,parseRepository,sha256,canonicalJSON} from './hub-core.mjs';
const ENGINE='cn-novelist-gpt',UPSTREAM='507d41567925eab520ad459db08fda83813e8051';
const DOCS=['00-人物档案.md','01-大纲.md','03-文风基准.md','99-章节摘要.md'];
const START='<!-- CN_BODY_START -->\n',END='\n<!-- CN_BODY_END -->';
const need=(ok,message)=>{if(!ok)throw new Error(message);};
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const han=s=>{let n=0;for(const x of s){const c=x.codePointAt(0);if(c>=0x3400&&c<=0x4dbf||c>=0x4e00&&c<=0x9fff||c>=0x20000&&c<=0x323af)n++;}return n;};

export async function loadCN(repository,{client=new GitHubClient(repository),branch=''}={}){
 const book=await loadBook(client,branch),s=book.state;
 need(book.manifest.engine===ENGINE&&s?.schema==='cn-gpt-reading-view'&&s.view_only===true,'这不是B/CN-GPT小说，请使用它原来的系统入口。');
 const m=await client.readJSON('cn-project.json',book.snapshot.commit);
 need(m.hash===s.cn_project_sha256&&m.data?.engine===ENGINE&&m.data.upstreamCommit===UPSTREAM&&m.data.bookId===book.manifest.book.id,'B作品身份或来源绑定不符。');
 need(typeof m.data.projectPath==='string'&&m.data.projectPath.startsWith('chinese-novelist/')&&s.cn_plan_path===m.data.projectPath+'/02-写作计划.json','B原项目目录不符。');
 const raw=await client.readJSON(s.cn_plan_path,book.snapshot.commit),p=raw.data;
 need(raw.hash===s.cn_plan_sha256&&p?.engine===ENGINE&&p.bookId===m.data.bookId&&p.projectPath===m.data.projectPath&&p.novelName===m.data.novelName,'阅读视图落后于B写作计划，请GPT运行index并保存。');
 need(book.manifest.book.title===m.data.novelName&&book.manifest.book.platform===m.data.platform&&parseRepository(m.data.repository).key===client.repo.key&&book.manifest.source.branch===m.data.branch,'B计划、仓库或书目资料不符。');
 need(Array.isArray(p.chapters)&&p.chapters.length===p.totalChapters&&Number.isInteger(p.totalChapters)&&p.totalChapters>=1&&p.totalChapters<=2000&&p.writingMode==='serial'&&p.minWordsPerChapter===5500&&p.maxWordsPerChapter===6500,'B写作规格不符。');
 const requests=new Set();let unfinished=false,active=0,total=0,count=0;
 for(const [i,c] of p.chapters.entries()){
  need(c.chapterNumber===i+1&&['pending','in_progress','failed','completed'].includes(c.status),'B章序或状态不符。');
  if(c.status!=='completed'){
   unfinished=true;if(c.status!=='pending'){need(active===0&&i===count,'B有多个未完成目标。');active++;}continue;
  }
  need(!unfinished,'B存在越章采用。');
  const v=book.manifest.chapters[i];
  need(v&&v.number===c.chapterNumber&&v.title===c.title&&v.sha256===c.textSha256&&hash(c.recordSha256)&&hash(c.markdownSha256)&&hash(c.textSha256)&&hash(c.assessedPlanSha256)&&v.han_count===c.wordCount&&c.wordCountPass===true&&c.wordCount>=5500&&c.wordCount<=6500,'B正式章与原计划不一致。');
  need(v.text_path===`book/chapters/CH${String(i+1).padStart(3,'0')}_${c.textSha256}.txt`&&typeof c.requestId==='string'&&/^[A-Za-z0-9_.:-]{8,180}$/.test(c.requestId)&&!requests.has(c.requestId),'B正文路径或请求身份不符。');
  requests.add(c.requestId);total+=c.wordCount;count++;
 }
 need(count===book.manifest.chapters.length&&total===book.manifest.progress.actual_han&&p.totalChapters===book.manifest.progress.target_chapters&&6000*p.totalChapters===book.manifest.progress.target_han,'B进度统计不符。');
 need(['planning','in_progress','completed'].includes(p.status)&&(p.status==='completed')===(!unfinished),'B全书完成状态不符。');
 return {...book,client,cnMetadata:m.data,cnPlan:p};
}

export async function readCNChapter(book,number,{now=new Date()}={}){
 const {client,cnMetadata:m,cnPlan:p,snapshot}=book,c=p.chapters[number-1];
 need(c?.status==='completed'&&c.chapterNumber===number,'该章尚未采用。');
 need(c.recordPath===`${m.projectPath}/99-冻结记录/${c.recordSha256}.json`,'B冻结记录路径不符。');
 const raw=await client.readJSON(c.recordPath,snapshot.commit),r=raw.data;
 const expected=Object.fromEntries(Object.entries(c).filter(([k])=>!['recordPath','recordSha256'].includes(k)));
 need(raw.hash===c.recordSha256&&r?.engine===ENGINE&&r.bookId===m.bookId&&canonicalJSON(r.chapter)===canonicalJSON(expected)&&r.previousRecordSha256===(p.chapters[number-2]?.recordSha256??null),'B冻结章绑定或历史链不符。');
 need(Number.isFinite(Date.parse(c.frozenAt))&&Date.parse(c.frozenAt)<=new Date(now).valueOf()+60000,'B冻结时间不符。');
 need(r.attachments&&Object.keys(r.attachments).sort().join('|')===[...DOCS,'markdown','text','editorial','assessment'].sort().join('|'),'B冻结材料不完整。');
 const materials=Object.fromEntries(await Promise.all(Object.entries(r.attachments).map(async([key,item])=>{
  need(hash(item.sha256)&&item.path===`${m.projectPath}/99-冻结记录/objects/${item.sha256}.txt`,'B快照路径不符。');
  const file=await client.readFile(item.path,snapshot.commit);need(file.hash===item.sha256&&file.text.trim(),'B冻结材料缺失或被改动。');return [key,file];
 })));
 const assessment=JSON.parse(materials.assessment.text);
 need(assessment.engine===ENGINE&&assessment.decision==='ready'&&assessment.reviewer==='same-context-model'&&assessment.chapter===number&&assessment.planSha256===c.assessedPlanSha256&&assessment.hashes.markdown===c.markdownSha256&&assessment.hashes.text===c.textSha256,'B审稿未绑定正文。');
 for(const name of [...DOCS,'editorial'])need(assessment.hashes[name]===r.attachments[name].sha256,'B资料与审读版本不符。');
 need(r.attachments.markdown.sha256===c.markdownSha256&&r.attachments.text.sha256===c.textSha256,'B原稿不可变副本与正式章不符。');
 const [md,txt]=await Promise.all([client.readFile(m.projectPath+'/'+c.filePath,snapshot.commit),client.readFile(book.manifest.chapters[number-1].text_path,snapshot.commit)]);
 need(md.hash===c.markdownSha256&&md.text.startsWith(`# 第${String(number).padStart(2,'0')}章：${c.title}\n`),'B原Markdown被改动。');
 need(md.text.split(START).length===2&&md.text.split(END).length===2,'B正文标记不唯一。');
 const start=md.text.indexOf(START)+START.length,end=md.text.indexOf(END);need(end>=start,'B正文标记顺序不符。');
 const prose=md.text.slice(start,end);
 need(await sha256(prose)===c.textSha256&&txt.hash===c.textSha256&&txt.text===prose&&han(prose)===c.wordCount,'B原正文、阅读副本或字数不符。');
 return {text:prose,title:c.title,number,han:c.wordCount,frozen_at:c.frozenAt,commit:snapshot.commit};
}
