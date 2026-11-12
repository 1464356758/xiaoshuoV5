const fail=(ok,message)=>{if(!ok)throw new Error(message);};
export function validateV6State(state,manifest){
 if(state.schema!=='novel-v6')return;
 fail(state.book_id===manifest.book.id&&state.revision===manifest.chapters.length,'V6状态与阅读目录不一致。');
 fail(Number.isInteger(state.revision)&&state.revision>=0&&Object.keys(state.chapters).length===state.revision,'V6状态的章序不完整。');
 for(const c of manifest.chapters){const item=state.chapters[String(c.number)];
  fail(item?.number===c.number&&item.text_sha256===c.sha256&&item.han_count===c.han_count&&'book/'+item.text_path===c.text_path&&/^[a-f0-9]{64}$/.test(item.record_sha256)&&item.record_path===`objects/${item.record_sha256}.json`,'V6冻结章目录不完整。');
 }
}
export async function verifyV6Chapter(client,book,chapter){
 const {state,snapshot}=book;if(state.schema!=='novel-v6')return;
 const c=state.chapters[String(chapter.number)],raw=await client.readJSON('book/'+c.record_path,snapshot.commit),r=raw.data;
 fail(raw.hash===c.record_sha256&&r.schema==='novel-v6-chapter'&&r.book_id===state.book_id&&r.number===chapter.number&&r.title===chapter.title&&r.text_sha256===chapter.sha256&&r.text_path===chapter.text_path&&r.request_id===c.request_id&&r.han_count===chapter.han_count&&r.frozen_at===c.frozen_at,'V6冻结记录与正文不匹配。');
 fail(r.previous_record_sha256===(state.chapters[String(chapter.number-1)]?.record_sha256??null),'V6冻结历史不连续。');
 const a=await client.readJSON(r.assessment_path,snapshot.commit);
 fail(a.hash===r.assessment_sha256&&a.data.schema==='novel-v6-assessment'&&a.data.reviewer==='same-context-model'&&a.data.decision==='ready'&&a.data.chapter===chapter.number&&a.data.hashes?.text===chapter.sha256,'V6编辑意见未绑定这个正文版本。');
 fail(Object.keys(r.attachments||{}).sort().join(',')==='memory,plan,review'&&Object.keys(r.hashes||{}).sort().join(',')==='memory,plan,review,text','V6冻结记录缺少记忆或编辑快照。');
 for(const key of ['memory','plan','review'])fail(/^[a-f0-9]{64}$/.test(r.hashes[key])&&r.attachments[key]===`book/objects/${r.hashes[key]}.md`&&a.data.hashes[key]===r.hashes[key],'V6快照版本不符。');
 return r;
}
export async function inspectV6(client,book,{now=new Date()}={}){
 const s=book.state,n=s.revision+1,task=await client.optionalJSON(`book/work/CH${String(n).padStart(3,'0')}/task.json`,book.snapshot.commit);
 if(task){
  fail(task.data.book_id===s.book_id&&task.data.number===n&&task.data.base_state_sha256===book.manifest.source.state_sha256,'V6草稿基线不一致。');
  let draft='';try{draft=(await client.readFile(`book/work/CH${String(n).padStart(3,'0')}/draft.txt`,book.snapshot.commit)).text;}catch(e){if(e.code!=='not_found')throw e;}
  const count=[...draft].filter(c=>/\p{Script=Han}/u.test(c)).length;
  return {status:'pending',label:draft.trim()?'有待接续草稿':'已建立目标，尚未起草',reason:`目标第${n}章，已保存正文约${count}汉字；记录不代表后台仍在运行。`,chapter:n,draft_han:count};
 }
 const c=book.manifest.chapters.at(-1);
 if(!c)return {status:'setup',label:'尚无正式章节',reason:'先完成选题和规划。',chapter:0};
 const record=await verifyV6Chapter(client,book,c);
 for(const key of ['memory','plan','review']){const file=await client.readFile(record.attachments[key],book.snapshot.commit);fail(file.hash===record.hashes[key],'V6章后记忆、计划或编辑快照缺失或被改动。');}
 const when=Date.parse(s.chapters[String(c.number)].frozen_at);
 fail(Number.isFinite(when)&&when<=new Date(now).valueOf()+60000,'V6冻结时间无效。');
 const text=await client.readFile(c.text_path,book.snapshot.commit);
 fail(text.hash===c.sha256,'V6正文哈希不符。');
 return {status:'completed',label:'最新正式章已核验',reason:'正文和冻结记录一致；文学质量与平台发布另行判断。',chapter:c.number,frozen_at:s.chapters[String(c.number)].frozen_at};
}
