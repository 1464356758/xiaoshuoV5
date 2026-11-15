import {cnPrompt} from './cn-prompts.mjs';
import {loadCN,readCNChapter} from './cn-loader.mjs';
const $=id=>document.getElementById(id);let book=null,ticket=0,current=null;

async function copy(id,status){
 const field=$(id);
 try{await navigator.clipboard.writeText(field.value);$(status).textContent='已复制。';}
 catch{field.focus();field.select();$(status).textContent=document.execCommand('copy')?'已复制。':'请长按文本复制。';}
}
$('generate').addEventListener('click',()=>{
 try{$('prompt').value=cnPrompt($('repo').value,{platform:$('platform').value,preferences:$('preferences').value,mode:$('mode').value});$('copyPrompt').disabled=false;$('promptStatus').textContent='指令已生成，连同B版包发送到本书GPT工作聊天。';}
 catch(e){$('prompt').value='';$('copyPrompt').disabled=true;$('promptStatus').textContent=e.message;}
});
$('copyPrompt').addEventListener('click',()=>copy('prompt','promptStatus'));
$('copyBody').addEventListener('click',()=>copy('body','readStatus'));
const invalidatePrompt=()=>{$('prompt').value='';$('copyPrompt').disabled=true;$('promptStatus').textContent='输入已变化，请重新生成指令。';};
for(const id of ['platform','preferences','mode'])$(id).addEventListener('input',invalidatePrompt);
$('repo').addEventListener('input',()=>{invalidatePrompt();ticket++;book=null;current=null;$('chapters').replaceChildren(new Option('尚未读取'));$('chapters').disabled=true;$('body').value='';$('copyBody').disabled=true;});
async function showChapter(number,seq){
 const chapter=await readCNChapter(book,number);if(seq!==ticket)return;
 current=chapter;$('body').value=chapter.text;$('copyBody').disabled=false;
 $('readStatus').textContent=`已核对原计划、Markdown、正文副本与本章冻结快照：第${chapter.number}章《${chapter.title}》，${chapter.han}汉字。`;
}
$('load').addEventListener('click',async()=>{
 const seq=++ticket;book=null;current=null;$('body').value='';$('copyBody').disabled=true;$('chapters').disabled=true;$('readStatus').textContent='正在读取B版原项目…';
 try{
  const loaded=await loadCN($('repo').value);if(seq!==ticket)return;book=loaded;
  $('chapters').replaceChildren(...book.manifest.chapters.map(c=>new Option(`第${c.number}章 ${c.title}`,String(c.number))));
  if(!book.manifest.chapters.length){$('readStatus').textContent='B版身份与原计划已核对，目前没有采用章节。';return;}
  $('chapters').disabled=false;const number=book.manifest.chapters.at(-1).number;$('chapters').value=String(number);await showChapter(number,seq);
 }catch(e){if(seq===ticket){book=null;$('chapters').replaceChildren(new Option('未能核验'));$('chapters').disabled=true;$('readStatus').textContent='读取未完成：'+e.message;}}
});
$('chapters').addEventListener('change',async()=>{
 if(!book)return;const seq=++ticket;$('body').value='';$('copyBody').disabled=true;$('readStatus').textContent='正在核验本章…';
 try{await showChapter(Number($('chapters').value),seq);}catch(e){if(seq===ticket)$('readStatus').textContent='读取未完成：'+e.message;}
});
