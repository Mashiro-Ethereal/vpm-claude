# liu2026mlref

## 选择性精读：模块信用与训练代价（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2608.18827v1)，实际读§4–5正文；技术补充未取得，故公式细节仅到正文叙述。保存 full.web.txt/full_part2.web.txt。

**方法。** 持久模块池，允许add/delete/modify/rewrite；每轮3池变体，按相对历史最优的性能阈值过滤再合并，同名保留较好，否则rollback。模块信用结合LLM判断和训练奖励序列与任务性能曲线的滞后Pearson/时间差分相关，EMA后归一化，UCB选模块并给线性权重。相关信用不是因果贡献证明。

**预算与结果。** §5.1：9迭代×3变体×3独立完整流程，并选最佳流程，约81候选训练；Eureka80、RF80。每候选3000epoch，最后从零20000epoch×5seed。Table2操控平均0.708 vs Eureka0.664/RF0.651，最高单任务仅2/10；归一化运动3.288 vs2.625，主要Franka改善0.997vs0.701，不是逐任务胜出。Table3消融三任务；§5.3报告完整版验证最优在最终测试仍最优，消融常不保持。Fig2横轴各自迭代进度归一化，不能作总时间比较。

**关联。** 持久模块池、训练诊断信用、稳定回退均已覆盖。“低成本指标预测最终训练”有验证-测试一致性先例，但未提供全候选跨任务预测误差。对RF无semantic guidance的Table1分类不应照抄：RF有设计思路和自验证。

**标题**：MLREF: Efficient Module Reuse for Reward Design in Reinforcement Learning via Large Language Models

**书目登记**：Chenglin Liu; Xun Wang; Ruishuo Chen; Zhuoran Li; Longbo Huang；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2608.18827)。版本记录：[Submitted on 19 Aug 2026]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：整段奖励改写难持久保留有效模块，优化振荡。

**原文方法/输入监督**：持久module pool是优化对象；线性模块组合、反思、混合credit、merge/rollback。

## 初筛记录：摘要证据

摘要：17任务，locomotion25.2%、manipulation6.6%提升；正文明确比较RF-Agent。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：模块credit是经验估计，独立贡献可能受模块耦合；不预设减少RL次数。

**阅读者推断/关联**：直接覆盖奖励模块池与定向复用；后续需要实质不同问题。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/liu2026mlref.abs.web.txt`（若首轮批量来源为 `liu2026mlref.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
