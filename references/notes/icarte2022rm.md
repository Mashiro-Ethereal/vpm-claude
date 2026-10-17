# Reward Machines: Exploiting Reward Function Structure in Reinforcement Learning

引用键：icarte2022rm。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/pdf/2010.03950)。
- 版本、发表状态与实际范围：JAIR2022作者arXiv版本；实际读摘要/定义、§4.2 CRM、§4.4 RS Eq8与Algorithm4、§5实验总结/部分离散实验。书目所列年份：2022；venue：Journal of Artificial Intelligence Research 73:173–208（除明确写已核验者，书目状态不视为独立确认）。
- WHY：RL把奖励当黑箱耗样本。。
- HOW：统一乘积任务状态、反事实经验与层级方法；从把RM当作MDP的价值迭代构造−v*(u)势。
- WHAT：终端势全零；自动shaping在离散有益，在continuous实证没有收益。
- 假设、监督与输入：预给RM、label接口；自动RM-only势不读取环境s/action物理成本。
- 验证依据：实际§5作者实验归纳明确RS并非所有域都增益；未复核每个36页附录结果。
- 边界：抽象最短/价值距离不能自动得出物理可达性；到坏terminal可有正shaping，需看总任务回报。
- 关联（阅读者推断）：RM-only势局限成立，但用物理价值替代已被GCR推进，不能仅添加s宣称新。
