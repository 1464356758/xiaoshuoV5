# B / CN-GPT 对照版 1.0.1

这是PenglongHuang/chinese-novelist-skill的GPT与GitHub适配版。保留原项目阶段、逐章清单、指南和文件结构；原文放在vendor/chinese-novelist，固定版本与每文件哈希在UPSTREAM.json。

作者使用方式：新建GPT工作聊天，上传初始化系统包_CN-GPT_对照版.zip，填写独立小说仓库链接。GPT执行核验、部署、规划、写作与保存；选择平台、选题，说开始写，之后直接说下一章。使用当前对话选择的GPT模型，无模型API Key；初始化包不能替你切换模型。

每章正文约6000汉字，同天不限章数，默认150章。计划主状态在chinese-novelist/作品目录/02-写作计划.json，已完成章节Markdown与快照冻结；其他状态为阅读视图，可重建。原项目写作方法与A/V6.3分开，不混装、不迁移已有书。

完整映射见GPT_WORKFLOW.md，适配差异见UPSTREAM_CHANGES.md。这里只提供可运行流程和文件完整性保护，文学效果与是否签约需要真实投稿验证。
