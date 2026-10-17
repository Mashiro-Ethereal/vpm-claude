# WoMAP: World Models For Embodied Open-Vocabulary Object Localization

Yin et al.；arXiv:2506.01600，2025。补充检索，2026-10-06。

- 来源：[作者项目与摘要](https://robot-womap.github.io/)、[预印本](https://arxiv.org/abs/2506.01600)。
- 实际阅读：作者项目页完整摘要、方法概要、实验和泛化说明；未精读论文正文，不据此确认正式发表。
- 方法：用 Gaussian Splatting 的真实—仿真—真实流程生成观察，开放词汇检测器蒸馏稠密奖励，潜在世界模型预测动作后的状态与奖励来做主动目标定位。
- 验证：项目页说明 7 个 PB/GS 环境、TidyBot 上每个真实任务 20 次试验，共 3 任务，并考察光照、背景与新指令。未复核论文中的逐项表格。
- 边界与联系：主动视角、语言任务、世界模型和奖励已经有组合实例；主要目标是定位物体，不是识别任务是否已完成或决定何时为训练策略验证奖励。
