import {parseRepository} from './hub-core.mjs';
export function cnPrompt(repository,{platform='',preferences='',mode='new'}={}){
 const repo=parseRepository(repository);
 if(['xiaoshuov5','xs-ku','xs-gl','xiaishuo-zuozong'].includes(repo.name.toLowerCase()))throw new Error('请填写独立的小说仓库。');
 if(platform.length>80||preferences.length>1200)throw new Error('平台或偏好过长。');
 if(mode==='continue')return `接管B/CN-GPT小说：${repo.url}\n读取实际默认分支、最新HEAD、AGENTS.md、GPT_WORKFLOW.md、cn-project.json和原项目02-写作计划.json。先核对engine=cn-novelist-gpt；若是A/V6或其他书，恢复其原流程，不覆盖部署。\n按vendor/chinese-novelist原项目清单A—D与GPT适配映射执行。已有未完成稿先接续原请求与目标，按约6000汉字完成本章写作、审读、最多3轮返修、摘要、采用冻结和GitHub保存。正文与本章材料变化后重新assess，verify/index后提交并回读固定新提交的原计划、正文、冻结记录和阅读视图，再交付实际字数及提交链接。每次完成一章，同天不限章数，已完成章只读，不创建日程，不请求模型API，不登记平台发布或承诺签约。`;
 return `请依据我附加的《初始化系统包_CN-GPT_对照版.zip》1.0.1，实际部署并接管独立新小说。\n【唯一小说仓库】${repo.url}\n【平台】${JSON.stringify(platform.trim()||'未选，先让我选择')}\n【偏好】${JSON.stringify(preferences.trim()||'暂无')}\n\n使用B/CN-GPT上游架构，engine=cn-novelist-gpt，不加载A版novel.py或CRAFT替代。先读AGENTS.md、GPT_WORKFLOW.md和UPSTREAM_CHANGES.md，运行python3 tools/cn_project.py package-check，核对CN_INIT_MANIFEST.json；读目标实际默认分支、HEAD与目录，确认无作品才部署。已有人物/章节或其他引擎则恢复原书，不覆盖或迁移。\n按原项目Phase0偏好与恢复→Phase1三层定位/标题→Phase2人物/大纲/文风/原JSON写作计划→Phase3逐章A—D清单→Phase4校验执行。你处理研究、工具、写作、审读和GitHub保存，我只选平台、选题并确认首次开始。默认150章，每章正文5500—6500汉字。收到开始写才写首章，以后下一章直接完成一个目标；同天不限章数。采用前完成审读绑定，采用后Markdown和摘要前缀冻结。\n02-写作计划.json是唯一主状态，book/state.json和online/index仅是派生阅读视图。每批保存保留base tree、父提交与预期HEAD，非强制更新，冲突重读，超时先回读。只有固定新提交的原计划、正文、冻结记录和阅读索引匹配才说已保存。使用当前GPT会话所选模型，初始化包不能强制切换型号或思考档位；不配置模型API、不自行建日程或投稿、不承诺签约。`;
}
