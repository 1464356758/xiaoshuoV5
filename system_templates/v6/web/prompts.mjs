const TEMPLATE='https://github.com/1464356758/xiaoshuoV5';
const LIBRARY='https://github.com/1464356758/XS-KU';
export function startPrompt(repo,platform,preferences){return `请用随附的《初始化系统包.zip》V6.1，从空仓库部署一部新小说。你负责文件、研究、写作、编辑与保存，我只选平台、选题和确认开始。
唯一小说仓库：${repo}
系统来源：${TEMPLATE}/tree/main/system_templates/v6（只读参考）
小说参考库：${LIBRARY}（读取实际默认分支与当前目录）
平台：${platform||'尚未指定，先让我选平台'}
作者偏好：${JSON.stringify(preferences||'暂无')}

解压后读AGENTS.md、WORKFLOW.md、CRAFT.md，运行python3 novel.py package-check；核对INIT_MANIFEST.json的version为6.1.0。读取目标仓库实际默认分支与最新HEAD。已有作品就恢复它的原有状态，禁止覆盖部署或迁移；只有空新书仓库才执行novel.py init并生成新身份，实际部署后提交与回读。
选定平台后核查当前官方规则与近期榜单，给5—8个原创选题，停在等我选择。选题已定就建立book/plan.md，包含角色世界、全书阶段路线、前五章和近期安排；用configure设置身份。收到“开始写”才写首章，以后“下一章”直接完成一章。
每章约6000汉字（5500—6500），默认150章。前五章先整体设计，每章给不同体验并逐章累计审读；人物要有欲望、误判与选择，不能章章重复报价、确认、收款、交接。带问题实际读XS-KU原文，学习选择、反应、情绪兑现和承接，记录真实范围，不照搬连续情节。
每轮按读→构思→写→改→存执行，正文与简短编辑意见、章后记忆落盘，assess绑定实际版本，freeze定稿，verify与index后同批提交GitHub并回读核验。文件检查不等于小说好看；模型自审不冒充独立读者或平台签约。
同一天不限章数，同请求重试接续原章，有草稿先续完。冻结章只读，不创建定时任务，不调用模型API，不自动登记平台发布。只有远端正文、状态和哈希匹配后才说已保存。`;}

function continueRules(entry){return `接管《${entry.title}》：${entry.repository_url}
读取仓库实际默认分支、最新HEAD和AGENTS.md，核对作品身份${entry.book_id||'以当前正式状态为准'}。
如果state.schema是novel-v6，按WORKFLOW.md运行status/context/verify，回读最新章全文、章后记忆、计划及本章涉及的旧章。调用begin，同请求用原编号重试；已有草稿接续原目标。写完整约6000汉字（5500—6500），前五章累计审读，以后每五章全文回看；做具体编辑返修和章后记忆，assess→freeze→verify→index，连同实际正文一起提交GitHub并远端回读。
如果是旧版书，按本书原引擎继续，不覆盖安装V6，不重置身份、正文或现有任务记录。
本次持续执行到目标一章冻结并真实保存。同一天不限章数；已有未完成章先完成它，已完成的同请求只核验。已冻结章只读。不要让我填写JSON或反复要求冻结，不编造提交或平台发布，不保证签约。`;}
export function continuePrompt(entry,{scheduled=false}={}){
 if(!scheduled)return continueRules(entry)+'\n现在继续下一章，不创建或修改定时日程。';
 return `为本书创建或更新唯一每日写作任务：每天北京时间（Asia/Shanghai）${entry.expected_time}。先按仓库、book_id和已有任务ID查找；已有复用，不另建。核对实际任务ID、时区、启用状态及反馈位置，未知字段标未验证。此处是我对定时配置的明确请求。\n\n长期任务内容：\n${continueRules(entry)}\n每次真实触发推进一章，允许同一天另行手动续写；同一触发重试接续原目标。任务平台显示完成不能代替远端章节验证。`;
}
