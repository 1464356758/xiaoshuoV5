# 上游架构保留与GPT适配边界

上游：PenglongHuang/chinese-novelist-skill，master，507d41567925eab520ad459db08fda83813e8051，MIT。vendor下22个运行相关文本文件逐字节保留（SKILL、LICENSE、全部references与原Node脚本）；不包括宣传图片、赞助配置和README。原文件哈希在UPSTREAM.json，未将它们改写成V6.3。

## 保留

- Phase0偏好与中断恢复；Phase1三层定位/标题；Phase2人物、大纲、文风及章节规划；Phase3清单A—D；Phase4校验与最多3轮返修。
- chinese-novelist/时间-作品目录、user-preferences.json、00人物、01大纲、02计划、03文风、99摘要，以及逐章Markdown。
- 原字段和状态pending/in_progress/failed/completed；角色、情节结构、对白、钩子、细节扩写等仍查上游guides。

## 适配

| 原宿主或默认行为 | GPT/GitHub版执行方式 |
| --- | --- |
| AskUserQuestion、Read/Edit/Write | 可用的GPT提问、文件与Python工具；已有信息走原快捷入口，不重复问 |
| skillBaseDir绝对安装路径 | 包内vendor/chinese-novelist，不安装个人技能或要求电脑装Claude |
| Node脚本默认3000字、可选批量模式 | Python正文区5500—6500汉字，当前GPT逐章串行；同天不限章数 |
| 一次循环自动写完整本 | 每个作者下一章指令推进一章；需要连续多章由作者另行明确指定 |
| 完稿后修复所有章节 | 每章采用前完成校验；采用后的章节和摘要前缀只读，未来计划可改 |
| 失败3轮后仍可全书completed | 保留真实failed，不追认完成；全部章采用后才全书completed |
| 仅本地文件进度 | 原02计划仍是唯一主状态；附加请求/哈希绑定、操作系统短锁、GitHub预期HEAD保存与回读 |
| Markdown标题/概要/备注参与字数 | 用唯一正文标记提取可发布小说文字，其他内容不计入 |

对外阅读兼容层派生book/state.json、book/chapters/CHxxx_哈希.txt和online/index.json。它不执行写作、不取代原02计划，也没有伪装成novel-v6；B阅读页将核对原计划及冻结记录后展示章节。

CNOCTAVE派生版没有混入本B包。作者当前需要A/B两套系统，B采用上次评分更高的主项目；以后若明确比较派生版，应再建独立C版，不能悄悄改变本B试验基线。

A/V6.3来源、目录树与包哈希保存在A_BASELINE.json。本轮不修改其代码、初始化包或默认网页。实际同模型/同题材对照仍受题目与人工干预影响，不能只因其中一本签约就断言另一系统永远较差。
