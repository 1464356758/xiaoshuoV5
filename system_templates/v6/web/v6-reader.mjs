const fail=(ok,message)=>{if(!ok)throw new Error(message);};
const hashOK=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const keysAre=(value,names)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join(',')===names;
const repositoryKey=value=>typeof value==='string'&&/^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/.test(value)?value.replace(/\/$/,'').replace(/\.git$/i,'').toLowerCase():null;
export function countHan(text){let n=0;for(const c of text){const p=c.codePointAt(0);if((p>=0x3400&&p<=0x4DBF)||(p>=0x4E00&&p<=0x9FFF)||(p>=0x20000&&p<=0x323AF))n++;}return n;}
export function validateV6State(state,manifest){
 if(state?.schema!=='novel-v6'&&manifest.engine!=='novel-v6')return;
 fail(state?.schema==='novel-v6'&&state.book_id===manifest.book.id&&/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(state.book_id),'V6状态与阅读目录的作品身份不一致。');
 fail(Number.isInteger(state.revision)&&state.revision>=0&&state.revision<=2000&&state.chapters&&typeof state.chapters==='object'&&!Array.isArray(state.chapters)&&Object.keys(state.chapters).length===state.revision&&manifest.chapters.length===state.revision,'V6状态的章序不完整。');
 fail(Number.isInteger(state.target_chapters)&&state.target_chapters>=state.revision&&state.target_chapters>=1&&state.target_chapters<=2000&&JSON.stringify(state.chapter_han)==='[5500,6500]','V6目标配置无效。');
 fail(manifest.book.title===(state.title||'待选题新书')&&manifest.book.platform===state.platform&&repositoryKey(state.repository_url)&&repositoryKey(state.repository_url)===repositoryKey(manifest.source.repository_url)&&state.branch===manifest.source.branch,'V6作品资料与正式状态不一致。');
 const requests=new Set();let total=0;
 for(const [i,c] of manifest.chapters.entries()){
  const item=state.chapters[String(i+1)];
  fail(c.number===i+1&&item?.number===c.number&&item.title===c.title&&item.text_sha256===c.sha256&&item.han_count===c.han_count&&'book/'+item.text_path===c.text_path&&c.text_path===`book/chapters/CH${String(c.number).padStart(3,'0')}_${c.sha256}.txt`&&hashOK(item.record_sha256)&&item.record_path===`objects/${item.record_sha256}.json`,'V6冻结章目录不完整或与正式标题不一致。');
  fail(typeof item.request_id==='string'&&/^[A-Za-z0-9_.:-]{8,180}$/.test(item.request_id)&&!requests.has(item.request_id)&&hashOK(c.sha256)&&Number.isInteger(c.han_count)&&c.han_count>=5500&&c.han_count<=6500,'V6冻结章字数或请求身份无效。');
  requests.add(item.request_id);total+=c.han_count;
 }
 fail(manifest.progress.adopted_chapters===state.revision&&manifest.progress.actual_han===total&&manifest.progress.target_chapters===state.target_chapters&&manifest.progress.target_han===6000*state.target_chapters,'V6进度统计与正式章节不一致。');
}
export async function verifyV6Chapter(client,book,chapter){
 const {state,snapshot}=book;if(state.schema!=='novel-v6')return;
 const c=state.chapters[String(chapter.number)];fail(c,'V6正式状态缺少这个章节。');
 const raw=await client.readJSON('book/'+c.record_path,snapshot.commit),r=raw.data;
 fail(raw.hash===c.record_sha256&&r?.schema==='novel-v6-chapter'&&r.book_id===state.book_id&&r.number===chapter.number&&r.title===chapter.title&&r.title===c.title&&r.text_sha256===chapter.sha256&&r.text_path===chapter.text_path&&r.request_id===c.request_id&&r.han_count===chapter.han_count&&r.frozen_at===c.frozen_at,'V6冻结记录与正文不匹配。');
 fail(r.previous_record_sha256===(state.chapters[String(chapter.number-1)]?.record_sha256??null),'V6冻结历史不连续。');
 fail(hashOK(r.assessment_sha256)&&r.assessment_path===`book/objects/${r.assessment_sha256}.json`,'V6审读依据没有引用不可变快照。');
 fail(keysAre(r.attachments,'memory,plan,review')&&keysAre(r.hashes,'memory,plan,review,text')&&r.hashes.text===chapter.sha256,'V6冻结记录缺少记忆或编辑快照。');
 const a=await client.readJSON(r.assessment_path,snapshot.commit);
 fail(a.hash===r.assessment_sha256&&a.data?.schema==='novel-v6-assessment'&&a.data.reviewer==='same-context-model'&&a.data.decision==='ready'&&a.data.chapter===chapter.number&&keysAre(a.data.hashes,'memory,plan,review,text'),'V6编辑意见未绑定这个正文版本。');
 for(const key of ['text','memory','plan','review'])fail(hashOK(r.hashes[key])&&a.data.hashes[key]===r.hashes[key],'V6快照版本不符。');
 await Promise.all(['memory','plan','review'].map(async key=>{
  fail(r.attachments[key]===`book/objects/${r.hashes[key]}.md`,'V6附件没有引用不可变快照。');
  const file=await client.readFile(r.attachments[key],snapshot.commit);
  fail(file.hash===r.hashes[key]&&file.text.replace(/\uFEFF/g,'').trim(),'V6章后记忆、计划或编辑快照缺失或被改动。');
  if(key==='review')fail([...file.text].length<=3000,'V6编辑意见超过约定长度。');
 }));
 return r;
}
export function verifyV6Text(file,chapter){fail(file.hash===chapter.sha256&&countHan(file.text)===chapter.han_count,'V6正文哈希或实际字数不符。');}
export async function inspectV6(client,book,{now=new Date()}={}){
 const s=book.state,n=s.revision+1,c=book.manifest.chapters.at(-1);let latest=null;
 if(c){
  await verifyV6Chapter(client,book,c);
  const when=Date.parse(s.chapters[String(c.number)].frozen_at);
  fail(Number.isFinite(when)&&when<=new Date(now).valueOf()+60000,'V6冻结时间无效。');
  verifyV6Text(await client.readFile(c.text_path,book.snapshot.commit),c);
  latest={chapter:c.number,frozen_at:s.chapters[String(c.number)].frozen_at};
 }
 const work=`book/work/CH${String(n).padStart(3,'0')}`,task=await client.optionalJSON(work+'/task.json',book.snapshot.commit);
 let draft='',hasDraft=false;try{draft=(await client.readFile(work+'/draft.txt',book.snapshot.commit)).text;hasDraft=true;}catch(e){if(e.code!=='not_found')throw e;}
 if(task){
  fail(task.data?.book_id===s.book_id&&task.data.number===n&&n<=s.target_chapters&&task.data.base_state_sha256===book.manifest.source.state_sha256&&typeof task.data.request_id==='string'&&/^[A-Za-z0-9_.:-]{8,180}$/.test(task.data.request_id),'V6草稿身份或基线不一致。');
  const count=countHan(draft);
  return {status:'pending',label:draft.trim()?'有待接续草稿':'已建立目标，尚未起草',reason:(latest?`已核验第${latest.chapter}章；`:'')+`目标第${n}章，待续草稿已保存约${count}汉字；记录不代表后台仍在运行。`,chapter:n,draft_han:count,latest_frozen:latest};
 }
 fail(!hasDraft,'发现草稿但缺少对应任务文件，请恢复原任务后再接续。');
 if(!latest)return {status:'setup',label:'尚无正式章节',reason:'先完成选题和规划。',chapter:0,latest_frozen:null};
 return {status:'completed',label:'最新正式章已核验',reason:'正文、冻结与章后快照一致；文学质量与平台发布另行判断。',chapter:c.number,frozen_at:latest.frozen_at,latest_frozen:latest};
}
export function v6UpdateStatus(result,date){
 const when=Date.parse(result.latest_frozen?.frozen_at);
 if(Number.isFinite(when)&&new Date(when+8*3600000).toISOString().slice(0,10)===date)return 'updated';
 return result.status==='completed'?'missing':result.status;
}
