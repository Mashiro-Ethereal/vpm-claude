# lee2026rda

## 选择性精读：行为诊断与评价独立性（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2606.01672v1)，实际读§3–5、附录7提示和8修改轨迹片段；保存 deep.web.txt/deep_part2.web.txt。

**方法。** GPT-5分子任务并生成状态奖励；每候选训练后视频按子任务评分及失败原因，选最好、同时修订子任务和奖励。允许warm-start前轮最佳策略。5迭代，ManiSkill每轮4候选/50Msteps，Humanoid每轮8/10Msteps，3seed；文本未明确50M是在每候选还是全轮，预算比较不可擅自补足。

**实验。** §5.2 ManiSkill12任务对齐/成功0.95/0.90 vs Eureka0.87/0.87；Humanoid4任务0.70/0.42，对齐高于Eureka0.47、成功略低。成功是bench指标；对齐由GPT-4.1对5视频各4次五档评分，模型不同于设计者，但仍VLM评价而非独立用户偏好。§5.3Package用躯干推代替双手的真实失败轨迹驱动修订。§5.4子任务反思/视觉分析消融及预算配置两任务3seed。

**关联。** 训练视频诊断→修订进度结构/奖励已直接覆盖；状态代码奖励不等于视觉奖励部署，也没有系统低预算预测最终策略的验证。

**标题**：RDA: Reward Design Agent for Reinforcement Learning

**书目登记**：Hojoon Lee; Ajay Subramanian; Ben Abbatematteo; Vijay Veerabadran; Pedro Matias; Karl Ridgeway; Nitin Kamra；2026；arXiv; RLC 2026 author-reported。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2606.01672)。版本记录：[Submitted on 1 Jun 2026]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：达到终点成功也可能不符合自然语言过程要求。

**原文方法/输入监督**：VLM任务分解、视觉评估轨迹、失败摘要、迭代修订奖励代码。

## 初筛记录：摘要证据

摘要：ManiSkill12桌面+HumanoidBench4全身，成功相当而指令对齐显著更好；arXiv注Accepted RLC26。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：语义评价来源与人工验证需读全文；比终点成功多监督。

**阅读者推断/关联**：直接覆盖行为语义诊断奖励修订，不能视为全新空白。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/lee2026rda.abs.web.txt`（若首轮批量来源为 `lee2026rda.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
