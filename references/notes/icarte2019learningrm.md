# Learning Reward Machines for Partially Observable Reinforcement Learning

引用键：icarte2019learningrm。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://proceedings.neurips.cc/paper/2019/file/532435c44bec236b471a47a88d63513d-Paper.pdf)。
- 版本、发表状态与实际范围：正式NeurIPS2019；实际读摘要、§3/§4.1–4.3 perfectRM与必要目标、§5在线更新、§6实验、§7反例/限制。书目所列年份：2019；venue：NeurIPS 2019（除明确写已核验者，书目状态不视为独立确认）。
- WHY：POMDP中学习有用记忆而非用户给RM。。
- HOW：Tabu search找压缩抽象后继预测集合的RM；未见后继触发新搜索，改图后重新学策略。
- WHAT：perfectRM让(o,u)满足POMDP后继分布充分性；三gridPOMDP近最优。
- 假设、监督与输入：已给有限高层property detectors；抽象轨迹；完美RM存在依赖有限可达belief等条件。
- 验证依据：三域5%动作随机变化；RM30runs，递归/LSTM基线也有labeling输出；§4目标必要而非充分。
- 边界：概率变化而可行后继不变时预测集合目标辨不出充分历史；跨RM反事实经验仍可能偏。
- 关联（阅读者推断）：同一观测不同任务历史、在线改RM、压缩记忆都已覆盖；视觉事件弱监督和组合泛化需另证明。
