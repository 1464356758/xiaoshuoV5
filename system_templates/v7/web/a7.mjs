const reserved = new Set(['xs-ku','xs-gl','xiaoshuov5','xiaishuo-zuozong']);
export function promptFor(value, mode) {
  const url = new URL(value.trim());
  if (url.protocol !== 'https:' || url.hostname !== 'github.com' || url.port || url.username ||
      url.password || url.search || url.hash) throw new Error('请填写 GitHub 仓库首页的 HTTPS 链接。');
  const path = url.pathname.replace(/\/$/, '').replace(/\.git$/i, '');
  const match = path.match(/^\/([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+)$/);
  if (!match || reserved.has(match[2].toLowerCase())) throw new Error('请填写这本小说自己的独立仓库。');
  const address = 'https://github.com' + path;
  if (mode === 'resume') return '接管本书 ' + address + '。获取仓库实际默认分支，核对 book_id、书名、edition=novel-a7 和本书登记的 version，读取该书 WORKFLOW.md、正式状态和在途草稿。先恢复原任务，已完成的工作按远端实际结果处理。若版本不同，请按原版本接管。';
  return '请按随附的《初始化系统包_A版_V7.0.zip》部署独立新书，清单版本应为 7.0.1。唯一新书仓库为 ' + address + ' 。先读包内 AGENTS.md、WORKFLOW.md 和实际默认分支，发现已有作品就按其原系统接续。使用 1464356758/XS-KU 的实际原文。由你执行工具，我选平台、选题并确认“开始写”。之后每次“下一章”完成写作、审核、必要返修、冻结、GitHub 提交和固定提交回读。不自动定时或投稿。';
}
if (typeof document !== 'undefined') {
  const el = id => document.getElementById(id);
  const reset = () => { el('result').hidden = true; el('prompt').value = ''; el('status').textContent = ''; };
  el('repo').addEventListener('input', reset);
  el('mode').addEventListener('change', reset);
  el('launch').addEventListener('submit', event => {
    event.preventDefault();
    reset();
    try {
      el('prompt').value = promptFor(el('repo').value, el('mode').value);
      el('result').hidden = false;
      el('prompt').focus();
    } catch {
      el('status').textContent = '请输入独立小说仓库的 GitHub 首页；系统母版和参考库仅供读取。';
    }
  });
  el('copy').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(el('prompt').value);
      el('status').textContent = '指令已复制。';
    } catch {
      el('prompt').focus(); el('prompt').select();
      el('status').textContent = '已选中指令，可长按复制。';
    }
  });
}
