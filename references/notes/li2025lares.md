# li2025lares

## 选择性精读：共享经验、持续训练与候选选择（第二轮）
来源：[NeurIPS正式PDF](https://papers.neurips.cc/paper_files/paper/2025/file/21b5d3a17aa5525f30bfd2bc59ac3a48-Paper-Conference.pdf)，实际读§4–5、附录B.1/B.2与参数分析片段；保存 deep_part2/3、detail、exp/exp2、appendix.detail.web.txt。定位用节/表而非未预检本地页码。

**方法。** 候选各自actor/critic；所有策略交互进共享replay，各转移存所有奖励。新奖励重标缓冲，非elite从elite策略及Q继承，按缓冲均值尺度调奖励且加参数距离约束。Thompson依真实成功/失败更新Beta，决定下一策略交互；奖励进化后重置选择器。属于真实训练响应后的在线预算分配，非静态离线效用预测。

**实验预算。** §5.1每任务总1Msteps（MetaWorld/运动）或2M（ManiSkill/MinAtar），5独立run，群体5，5轮含初始化；有专家初始化时另保留专家个体。MetaWorld12+ManiSkill4+MinAtar4；无初始化5MetaWorld+2运动。Table2无初始化5操作皆100%，Table3Ant4.44/Humanoid3.42 vsEureka1.49/2.02（速度）；不可与RF不同训练设置直接比。Fig6去尺度/参数约束崩溃，Fig5去TS交互也下降。附录B保留每转移必要变量以重标；不能默认纯像素replay已能执行状态程序奖励。

**关联。** 共享replay、重标奖励、elite初始化、短训练响应和持续奖励搜索均已实现；若提出此架构须将新意落到预测目标、有效条件与持出泛化，并计GPU更新成本而非只环境步数。

**标题**：LaRes: Evolutionary Reinforcement Learning with LLM-based Adaptive Reward Search

**书目登记**：Pengyi Li; Hongyao Tang; Jinbin Qiao; Yan Zheng; Jianye Hao；2025；NeurIPS 2025。

**实际读取来源**：[原始来源](https://papers.neurips.cc/paper_files/paper/2025/hash/21b5d3a17aa5525f30bfd2bc59ac3a48-Abstract-Conference.html)。版本记录：原始来源见保存片段；正式版本状态按来源确认，不从书目标题推断。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：ERL只探索策略参数，未充分利用奖励搜索。

**原文方法/输入监督**：LLM奖励群体+共享replay（每transition含所有reward），更新后relabel；Thompson elite选择，reward scaling/参数约束。

## 初筛记录：摘要证据

NeurIPS正式摘要：initialized/noninitialized均改善样本效率和终点表现。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：共享缓冲离策略RL条件与奖励更新稳定性需全文。

**阅读者推断/关联**：直接覆盖策略/奖励共同进化、缓冲复用和collapse处理。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/li2025lares.abs.web.txt`（若首轮批量来源为 `li2025lares.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
