# Reward Evolution with Graph-of-Thoughts: A Bi-Level Language Model Framework for Reinforcement Learning

Yao et al.；arXiv:2509.16136，2025。补充检索，2026-10-06。

- 来源：[作者预印本摘要](https://arxiv.org/abs/2509.16136)。
- 实际阅读：完整摘要；未读取完整方法/实验，不确认正式录用。
- 问题/方法：任务拆成文本属性图，用 VLM 分析策略视频，再由 LLM 迭代生成奖励；图结构推理与视觉行为反馈组合。
- 验证：摘要给出 10 个 RoboGen 和 4 个 ManiSkill2 任务比较；本轮不引用未核对的增幅作定量证据。
- 边界与联系：进一步说明“RF-Agent 加任务图和视觉反思”的组合级新颖性很弱。它是否处理历史义务与重复状态不能据摘要判断。
