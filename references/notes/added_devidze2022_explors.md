# Exploration-Guided Reward Shaping for Reinforcement Learning under Sparse Rewards

Devidze, Kamalaruban, Singla；NeurIPS 2022。补充检索，2026-10-06。

- 来源：[正式论文](https://proceedings.neurips.cc/paper_files/paper/2022/file/266c0f191b04cbbbe529016d0edc847e-Paper-Conference.pdf)。已保存 PDF 和文本。
- 实际阅读：正式来源摘要、引言、§2 和 §3.2 方法片段；未精读完整实验/证明，属方法初筛。
- 问题：完全自监督的内在奖励学习在极稀疏任务中仍缺乏探索信号。
- 方法：联合探索奖励和按外在任务收益学习的内在奖励，交替更新奖励与策略；从 LIRPG 的高层元梯度推导更广泛学习器适用的更新。
- 实验声称与边界：论文在特殊链式 MDP 给理论分析，并在稀疏/噪声环境实验；本轮未独立复核这些表格数值。
- 对本项目的判断：早期成功为零时，短期任务收益可能无法评价奖励候选，这个冷启动问题已有专门研究。方向若用短期学习效用选奖励，要比较探索覆盖的作用，不能假定少量训练总能产生有信息的成功率。
