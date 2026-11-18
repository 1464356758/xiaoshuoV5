# 小说主系统版本记要

## 2026-11-18 · A 系统 V7.0 开书版

新书可选择 system_templates/v7。初始化包版本 7.0.0，edition=novel-a7，沿用 A 系列阅读格式。使用前两部原作的可回查片段、两种完整起笔与按投稿渠道截取的正文。单聊天完成本章到远端回读。A6.3 与 B1.0.1 继续服务各自原有作品。个人端 A7 路由 /a7.html；发布状态由该站点实际部署记录确认。

历史交接记录如下。

# 小说主：A/B双系统接管状态

2026-11-15（北京时间）。作者要求保留现有6.3，并把外部项目的运行架构独立接入供两部新书对照。本轮不混装、不迁移已有小说，不执行投稿或创建日程。

## A / 小说主V6.3：保留不变

- 源码system_templates/v6，固定来源提交6a9f966f1b852fd1b66c9921bb184e0ef207b715，目录树2f5f96df01bafa325e948ca5e6f2844104b5eee9。本轮没有修改这个目录。
- 原初始化包SHA256：3070d3fbd0d97359ac2257bc957456ea8ed61d79e0c26b92026142b9049b3f38；原完整包SHA256：06911a96e4ad5f72b0cbbbda36382c18dff4147d0b4c46127be5772cca87c615。原Library文件不替换，A首页、指令和默认下载资源保持原内容。
- A仍用WORKFLOW/CRAFT/novel.py和book/state主状态，原42项工程验证与两份未采用五章稿不变。原工作台2.2.0、新书引擎6.3.0不升版。

## B / CN-GPT对照版1.0.1：已接管并修复

- 源码system_templates/cn_gpt，上游为PenglongHuang/chinese-novelist-skill，master固定507d41567925eab520ad459db08fda83813e8051。22份运行文件（SKILL、LICENSE、references、原脚本）逐字节保留于vendor/chinese-novelist，哈希在UPSTREAM.json；CNOCTAVE不混入。
- 保留上游Phase0—4、三层定位、逐章清单A—D、chinese-novelist作品目录、00人物、01大纲、02计划、03文风、99摘要和逐章Markdown。写作唯一主状态是02-写作计划.json，不是A版状态机。
- 新工具tools/cn_project.py只做GPT宿主适配、计数、请求恢复、审读绑定、采用与GitHub阅读投影，无模型API。正文5500—6500汉字，每次下一章完成一个目标，同天不限章数；当前GPT会话模型由作者选择，未知档位不伪造。
- 按共同冻结条件，采用前完成校验；采用点是原02计划本章completed。在此之前保存Markdown、纯正文、规划与编辑资料的不可变快照。已完成章与摘要前缀只读，后续只处理当前候选及未来路线。失败最多3轮仍不追认completed。
- book/state.json、book/chapters和online/index.json为派生阅读视图，可由index修复；不能据此反写原计划。保存到GitHub需实际base tree、预期HEAD、非强制推进与固定新提交回读。
- B有独立初始化包和/cn.html页面，A原资源与默认下载不改。B页负责生成指令及核验原计划、原Markdown、正文与快照后读取正式章。
- 原流程映射见B的GPT_WORKFLOW.md、UPSTREAM_CHANGES.md；对照与开书说明在双系统开书与对照说明.md。工程测试、A保留证明与真实网页发布记录在B的validation目录。

## 下一次接管

先明确作者使用A还是B；作者未选系统时不替换已有书。新开书各用独立仓库、独立GPT聊天及匹配初始包；当前系统母版不是新小说目标。测试只用临时合成数据，生产小说、XS-KU、原管理清单与所有既有任务本轮未改。

A入口：https://novel-workspace-v44.qq1464356758.chatgpt.site/
B入口：https://novel-workspace-v44.qq1464356758.chatgpt.site/cn.html

系统验证仅说明运行与保存范围。未新建真实B小说仓库现场写书，未验证大陆网络或生产登录后全部操作；文学与签约表现待实际创作及平台反馈。

## 2026-11-15本轮实际接管

已读取当前两套初始化包、A完整包、双系统说明、工作台站点资料、GitHub默认分支、固定上游原文与站点绑定。B1.0.1修复摘要冻结前缀漏检和不合格候选无法登记返修的缺口，26项临时合成工程测试通过；上游22文件、A源码树与两包哈希保持不变。下载与入口由既有站点同步；实际部署记录以system_templates/cn_gpt/validation/软件发布.json为准。

本轮不写新书，不改现有小说或XS-KU；后续等待作者提供独立新小说仓库、平台或下一指令。文学与签约仍需实际稿件和投稿反馈。
