# Using Reward Machines for High-Level Task Specification and Decomposition in Reinforcement Learning

引用键：icarte2018。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://proceedings.mlr.press/v80/icarte18a/icarte18a.pdf)。
- 版本、发表状态与实际范围：正式ICML2018；实际读摘要、§3 RM/乘积MDP、§4 QRM及Theorem4.1/DQRM、§5.1–5.4实验。书目所列年份：2018；venue：ICML 2018 / PMLR 80（除明确写已核验者，书目状态不视为独立确认）。
- WHY：把奖励内部结构提供给策略学习。。
- HOW：RM显式表示非Markov奖励；所有RM状态的子策略利用同条环境转移并行off-policy更新。
- WHAT：tabular在无穷数据/探索条件下最优；Office/Minecraft/continuousWaterWorld改善学习。
- 假设、监督与输入：预给事件词汇与labeling函数；乘积(s,u)；WaterWorld是位置速度向量、非像素。
- 验证依据：§5控制共享网络架构；30runs discrete，continuous多地图；DQRM胜options但没有其tabular理论保证。
- 边界：预给RM与事件接口；局部options最优不等于全局任务最优。
- 关联（阅读者推断）：序列、分支、部分序和历史任务状态均为既有表达能力。
