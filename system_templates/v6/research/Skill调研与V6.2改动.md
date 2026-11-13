# Skill调研与V6.2改动

核查日期：2026-11-14，北京时间。用户提供的是功能清单截图，没有各项作者/仓库链接；以下记录实际核对的来源，不把同名都当唯一对应，不把GitHub星数当写作成绩。

## 实际来源与取舍

- **oh-story-claudecode**：https://github.com/zenstory-ai/oh-story-claudecode ，main固定至`41a9b6c855d7d29a2bf214b4eefda2b10a0e8afb`。实读`skills/story-long-write/SKILL.md`、`skills/story-long-analyze/SKILL.md`、`skills/story-long-write/references/benchmark-recall.md`、`skills/story-long-write/references/genre-prose-cards/职场婚恋.md`、`skills/story-review/SKILL.md`及`skills/story-setup/references/codex/agents/character-designer.toml`。选取拆文到写前召回、人物目标与声线、表达/用笔/故事分层诊断、有原文依据的问题单。完整MIT许可在随包THIRD_PARTY_NOTICES.md保留。
- 同仓库当前目录核实六个技能：story-long-scan、story-long-analyze、story-long-write、story-deslop、story-review、story-cover；另有character-designer角色定义。未把它们当成七套要分别接管小说状态的系统，也未宣称已安装其插件或运行其审稿助手。
- **skill-from-masters**：https://github.com/GBSOSS/skill-from-masters ，实读版本`c4d27d29bfda00f73c23abd4990f700a6d3df480`的`skill-from-masters/SKILL.md`。借鉴以具体案例、反例和前后对照检验方法的思路；没有复制其完整技能或要求作者重新回答一套问卷。
- **writing-dna-skill**：https://github.com/larashero3-dotcom/writing-dna-skill ，实读版本`1335568bfd1141fc8447caaa812e6119e2d2fbbf`的`SKILL.md`与`LICENSE`。当前公开版是PolyForm Noncommercial；没有将它接入商业写作系统，也不把文章词频、标点和排版比例当长篇小说质量标准。
- chinese-novelist-skill（已读版本`507d41567925eab520ad459db08fda83813e8051`）、novel-creator-skill、webnovel-writer均还包含规划/状态等职责，与本系统现有保存机制重叠。本次没有整体导入其状态库、默认章节字数、自动改旧稿路径或API配置。

这些项目的自述、目录规模和默认评分表只证明提供了相应方法或程序，不构成我们样稿的签约验证。平台标准须另查当前官方要求，不能把第三方“番茄/起点规则”套成七猫官方规则。

## 对现有系统的实际修改

1. 在原WORKFLOW、CRAFT和plan模板内衔接实际精读、短方法卡、当前场景取用与改后回看。方法卡含来源、机制、适用条件、失败边界和不可照搬部分；不增加独立审批状态。
2. 人物从属性标签推进到两场不同处境中的欲望、误判、回避与声线。工作目标与关系压力须在具体决定里相互作用，不要求每章按固定公式制造事故。
3. 审稿先指出正文位置、证据与阅读损失，再按表达、用笔、故事判断最小修改。通常集中处理最严重的1—3处，问题未消失就保持未解决；不设置95分通行线。
4. 续写指令和网页下载同步到6.2.0。novel.py只有版本和包清单变化，保存逻辑未改，仍为391行；约6000汉字、同天不限章数、冻结章只读与单入口执行仍由原实现负责。

## 本次参考库实际阅读

XS-KU默认分支main，HEAD`f978c6d81eabe84267debcbd7499c89d4c9abc2c`。只重新实读以下两部的网页阅读单元1，不冒称整本、前五章或全库已读；原始大文件的来源提交为`90dbe70eec0ffd89b75bf98705bb402fbc6d6b54`。

| 作品 | 当前manifest | 本次单元范围与哈希 |
| --- | --- | --- |
| 封总，太太想跟你离婚很久了·云中觅 | books/cd50e5b371b89bfd6de79dc6_18c14662ee1d.json | 单元1，规范文本字符0—2415，`4acd5c27cadd045f19ae191eb791689a28f754a28a667f1251d5838c9a534f82` |
| 席先生，你被太太踢出局了！·九醉 | books/9b881d90fce415f5cdd83777_619e4e654140.json | 单元1，规范文本字符0—2459，`247346e72cb40a70758f799fc01adb67bbe217e4c83116c9787246d7ee87825e` |

两项签约信息在目录中均为author_reported，具体平台与送审版本未知。前者可观察人物仍希望被回应、尝试失败与决定改变的衔接；后者可观察职业遭遇与亲密关系之间的相互影响。这些是本次阅读推断，不是对它们签约原因的证明。未复制人物组合、受伤/生日等连续事件链或原句。

## 对照验证的范围

旧五章在validation/opening-five保留，新候选在validation/opening-five-v62；没有写入XS1或母版根目录book。实质修改集中在CH003和CH004，CH001、CH005做局部连续性与承接修正，CH002保留原文。逐章字数、哈希和修改依据随新清单及修订记录提供。

本次知道旧稿问题，仍由同一上下文模型改写和审读，属于定向修订。它能展示方法是否落实到具体场景，不能证明独立读者更喜欢、可复制到全部题材或已经达到签约水平。没有真人盲评、投稿或签约结果。
