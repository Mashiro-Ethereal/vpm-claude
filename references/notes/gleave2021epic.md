# Quantifying Differences in Reward Functions

引用键：gleave2021epic。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2006.13900v3)。
- 版本、发表状态与实际范围：arXiv v3/ICLR2021；实际读摘要、§4 canonicalization/Proposition4.2/Theorem4.9、§6.3与附录compute-cost片段。书目所列年份：2021；venue：ICLR 2021（除明确写已核验者，书目状态不视为独立确认）。
- WHY：评价奖励混淆奖励错误和策略优化失败。。
- HOW：消去PBRS势后对canonicalreward做Pearsondistance，保持正scale/shift不变。
- WHAT：无需trainpolicy评reward，覆盖条件下bound最优policyregret；PointMaze未见wall布局预测transfer性能。
- 假设、监督与输入：至少能queryreferenceR与candidaterewards；coverageD覆盖候选policyoccupancy；可query不可能transition。
- 验证依据：正文PointMaze实验；approxEPIC17s对照policy数小时为其特定域成本，不是通用加速倍数。
- 边界：缺referencegoldR、coverage或离线不可能states的learnedreward可靠性时不自动成立。
- 关联（阅读者推断）：RF-Agent若仅新增离线rewardmetric必须解释超过既有behavioralregret预测方法。
