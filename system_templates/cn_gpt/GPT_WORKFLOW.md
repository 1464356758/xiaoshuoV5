# B版执行流程：原项目架构，GPT执行，GitHub存储

适配版1.0.1；上游固定507d41567925eab520ad459db08fda83813e8051。所有命令由GPT执行，不让作者手工填写JSON。程序使用Python3.10+标准库与Linux文件锁，不调用模型；实际写作使用当前GPT聊天所选模型，型号和思考档位取不到就记未验证。

## 0. 部署、偏好与恢复

先解压并运行`python3 tools/cn_project.py package-check`，核对CN_INIT_MANIFEST.json的engine。读取指定小说仓库的实际默认分支、HEAD与目录，已有cn-project.json就恢复该B书；已有A/V4作品就按原书继续，禁止混装。本包不携带作品身份或样稿。

空新书仓库才放入包文件。原有同名README等初始化说明归档到无冲突路径后再放包内文件，保留其他文件与Git历史；部署后重新package-check。完全空GitHub仓库没有HEAD时，先确认元数据可读且没有分支，再用Contents创建接口写入实际README首提交（branch留空），回读真实默认分支、HEAD、tree再批量增量部署。单次404/409不证明为空；结果不明先回读，不伪造父提交。

阅读上游references/flows/phase0-initialization.md与shared-infrastructure.md，读取user-preferences.json。偏好与选题选择随阶段保存到GitHub；不能仅留在聊天。B版一仓一书，不从其他仓库复制进度。发现写作计划损坏，按真实提交历史恢复，不凭文件存在和字数重建completed。

## 1. 三层定位与标题

按上游phase1-layer1-core、phase1-layer2-customize、phase1-layer3-title执行。保留核心定位（题材/主角/冲突）、深度定制（世界/视角/基调/主题/读者/规模）、标题三层结构。作者已有的信息直接复用，按上游快捷入口合并展示；未提供的规格用已授权默认值整理成建议，不重新问一串重复问题。

平台未选先请作者选；选定后实际核查现行官方投稿/原创/AI辅助要求与近期榜单，记录来源和访问缺口，提出5—8个原创选题供选。选择后由GPT完成其余定位与标题整理。需要教材时实读XS-KU当前默认分支相关原文，在大纲来源区记路径、版本与范围；它只是输入，不导入A版方法卡或存储协议，不复制故事组合和原句。

## 2. 按原项目生成规划文件

读取上游phase2-planning.md及对应guides模板，运行：

```bash
python3 tools/cn_project.py create --repository 实际仓库 --branch 实际默认分支 --title 已选书名 --platform 已选平台
```

create保留同一身份的初始化重试，生成chinese-novelist/时间-书名-身份前缀目录与原项目五类文件。目录内写作主状态仍是02-写作计划.json（原有novelName、projectPath、totalChapters、writingMode、chapters、chapterNumber、filePath、status、wordCount、retryCount字段保留），默认150章、每章约6000字。程序补充请求与冻结绑定，不另建A版正式状态。

用原模板完成00-人物档案.md、01-大纲.md、03-文风基准.md，替换其CN_PENDING标记；99-章节摘要.md保留逐章收尾用途。大纲依原项目提供全章节规划表、悬念线与事实词典；前五章细化，后续可调整未写部分，不把未来安排当既成事实。文风基准段落由GPT原创，不采用未经授权的大段第三方原文。

按上游展示规划摘要：人物、核心冲突、章节路线、视角基调及前五章。作者说开始写即确认执行；此前停在规划，不先写正文。本适配默认serial逐章串行，使用当前GPT一人执行，不询问并行/Teams、不在未知环境派生其他写手。

## 3. 原项目逐章清单A—D

每次开始先status/context/verify，读取原项目references/flows/chapter-checklist.md，按以下映射执行：

**A 写前**：读取02计划对应章、01大纲/设定事实词典、00人物档案、99摘要中上章及回场人物最近记录；必要时回读原文。再读上一章结尾500—800字和03文风基准，承接情绪与知情。首次前五章逐章累计读全部已写开篇，第3/5章定稿前连读；每五章与阶段边界读相应全文。这是共同连载条件，写作方法仍用上游guides。

调用`begin --request 本次实际生成的稳定编号 --title 本章题名`。返回new或resume时只写该目标，resume必须沿用返回的旧请求；already_completed只核验原结果，不顺带写下章。没有每日限额。有未知旧稿不删除，恢复原计划和请求后再接续。

**B 写作**：使用原章节Markdown文件（第01章-标题.md），保留本章概要、正文、章节备注。程序建立唯一CN_BODY_START/END标记；章首引子及全部可发布小说文字写在标记之间，不把概要或备注当正文。依上游chapter-guide、dialogue-writing、hook-techniques等方法写作；不加载A版CRAFT替代它们。总正文5500—6500汉字覆盖上游3000—5000的默认值。约半章同步实际草稿、原计划与简短待续位置；主动中断也保存，下次从真实原稿继续。

**C 审读**：执行原清单的连续性、数字自报、信息边界、节奏、人物、重复解释与表达检查。按正文位置写98-编辑意见/第01章.md，通常400—900字，不超过3000字符，说明主要问题、实际修改、遗留风险与同上下文审读范围。正文结构或事实未成立先返修，最多3轮；仍未解决保留failed，不能强行采用。

**D 收尾**：按上游要求在99-章节摘要.md追加`## 第01章`，约300—500字，记录事件后果、人物知道/误信、公开表态/真实打算/已行动、条件和未了事项；完成章摘要不得回改，后续处理前向追加。更新01大纲的事实/揭示词典；首章采用前用实际候选原文校准03文风基准，不将参考作者句子复制进来。所有本章资料完成后再assess，不能在采用后补写会改变审读版本的资料。

## 4. 原项目校验与GitHub交付

把上游Phase4自动校验移到每章采用之前，保留其逐章检查与最多3轮返修；GPT适配不使用“失败仍全书completed”的兜底。存储工具重新核验实际正文、计划、人物、大纲、文风、摘要和编辑意见，并绑定哈希：

```bash
python3 tools/cn_project.py context
python3 tools/cn_project.py assess --expect 实际plan_sha256 --decision ready
python3 tools/cn_project.py adopt --expect 同一plan_sha256 --request begin返回的原请求
python3 tools/cn_project.py verify
python3 tools/cn_project.py index
```

verify会核对现有摘要保留最近冻结版本的完整前缀，发现旧章摘要被覆盖时先从快照逐字节恢复，不能新开一章绕过。

需要返修先用decision=revise登记实际轮次；字数不足、超长或当前章摘要尚未完成也要登记真实返修，ready/adopt仍须满足全部采用条件。读取返回的planSha256继续；同一结果重试先context，不能重置计数。任何资料改动后重新审读并assess。原文源码的Node字数工具保留作出处，实际计数使用本适配的正文区和Python标准库，不同时混用两种口径。

采用点只有02-写作计划.json本章status变completed；在此之前，原Markdown、纯正文、规划/摘要和审读资料已写入不可变快照。其对应Markdown和99-冻结记录不可改；误损坏时仅从已核验快照或Git历史逐字节恢复原内容，不重新创作旧章。book/state.json、book/chapters和online/index只是兼容阅读视图，丢失或落后用index重建。采用后索引写失败时，同请求重试恢复原结果，不重复采用，也不凭聊天宣称完成。

每批写GitHub前读取实际默认分支最新HEAD，保留base tree、当前HEAD父提交、expected_sha与force=false；不提交锁文件或缓存。冲突先读新提交与差异，保留双方改动，不能只换预期SHA重发旧tree。写请求超时先回读检查是否已成功，不生成新身份或请求重放。不能联网就保留本地草稿并说明尚未远端保存。

回读固定新提交的cn-project.json、02计划、本章Markdown、冻结记录、book/state.json、导出正文与online/index.json，运行verify或逐项哈希核对，才给作者章名、真实字数与提交链接。无需作者再次要求冻结。不登记平台已发布或已签约；投稿由作者决定，结果另存真实反馈。

02计划的status、wordCount、retryCount、requestId与冻结字段由begin/assess/adopt维护；GPT只可编辑未开写条目的规划信息，不按上游宿主示例手动把项目改成validating或completed。上游的阶段职责仍执行，状态写入统一映射到上述命令，避免一次操作既手改状态又调用适配工具。

若上游文件中的原始宿主指令与以上映射冲突，以本文件和作者实际要求为准；其余创作步骤和参考方法保留原项目架构。
