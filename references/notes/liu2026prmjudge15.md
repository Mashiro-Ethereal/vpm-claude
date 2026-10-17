# PRM-as-a-Judge 1.5: A Toolkit for Robot Process Assessment

引用键：liu2026prmjudge15。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2608.14284v1)。
- 版本、发表状态与实际范围：arXiv v1 preprint；实际读§2.2指标/§3评测与结果、附录C1–C3构造。书目所列年份：2026；venue：arXiv（除明确写已核验者，书目状态不视为独立确认）。
- WHY：过程评估进一步含失败和恢复。。
- HOW：扩展failednear-success FNS、drawdownrecovery DRR、successfulquality SQS，重算公开rolloutjudge曲线。
- WHAT：RoboPulse++700traj275task2244人工Rising/Fallinginterval；提供细粒度失败与恢复审计。
- 假设、监督与输入：默认RoboDopaminejudge，固定发布政策videos，无新的policy训练。
- 验证依据：AppendixC绝对进度无一致groundtruth，故标区间方向；taskentry不是去重distincttaskfamily。
- 边界：DRR是轨迹后验curve回升，不是当前state可恢复概率/行动义务监督；judge误差仍存在。
- 关联（阅读者推断）：‘首次引入恢复评价’不能成立；控制结果预测或干预用途需新增实证。
