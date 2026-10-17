# hu2024scaffolder

## 选择性精读：感知限制下的训练信号
来源：[arXiv v1](https://arxiv.org/html/2405.14853v1)，实际读§3–4；保存 deep.web.txt与scaffolder_method.deep.web.txt。
**方法。** DreamerV3另建特权world model，通过transdecoder和目标posterior在特权模型内想象目标策略；critic同时接两种latent，改进reward/return预测；特权探索策略与目标策略1:1收集，目标表示辅助重构特权信息。不强迫blind目标策略模仿全观测teacher。
**证据。** S3十任务多种目标/特权传感器，Fig6聚合弥补目标到特权策略79%差距、8/10学习更快；250k–5M样本与某些100M基线比较，不能当成完全同预算纯算法因果优势。Fig8四任务不同成分重要性不同。部署无需训练特权输入并不证明任务信息凭空可恢复；某些任务靠主动获取或鲁棒行为。
**关联。** 奖励质量之外，learner、观测、critic/model决定有限预算学习，支持效用目标有条件性。用户无力触觉的条件可选择visual/proprio任务，不能借blind-touch实验推断相同收益。

**标题**：Privileged Sensing Scaffolds Reinforcement Learning

**书目登记**：Edward S. Hu; James Springer; Oleh Rybkin; Dinesh Jayaraman；2024；ICLR 2024。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2405.14853)。版本记录：[Submitted on 23 May 2024]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：训练期有辅助传感器，部署只简单观测。

**原文方法/输入监督**：privileged sensing输入critic、worldmodel、reward estimator等辅助模块，保持actor部署接口。

## 初筛记录：摘要证据

ICLR2024摘要：S3十模拟传感任务，多数接近test-timeprivileged策略。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：需要训练辅助传感器；不可把无部署privileged等同无训练privileged。

**阅读者推断/关联**：挑战必须训练视觉reward才能得到视觉policy的主张。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/hu2024scaffolder.abs.web.txt`（若首轮批量来源为 `hu2024scaffolder.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
