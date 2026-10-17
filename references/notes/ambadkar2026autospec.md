# Automating the Refinement of Reinforcement Learning Specifications

引用键：ambadkar2026autospec。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2512.01047v2)。
- 版本、发表状态与实际范围：arXiv v2，正式ICLR2026 proceedings已核；实际读§2/3方法/定理、§4全部实验、附录A4限制。书目所列年份：2026；venue：ICLR 2026（除明确写已核验者，书目状态不视为独立确认）。
- WHY：正确但粗规范仍使RL难学。。
- HOW：失败edge policies的成功/失败轨迹做Seq/Add/Past/Or refinements，以修改reach/avoid/前驱集合/替代路径提高规范可学性。
- WHAT：每个找到的refined规范满足原spec(soundness)；rooms与Panda障碍到达实验。
- 假设、监督与输入：给SpectRL DAG、RL算法、success阈值；需要成功轨迹以建convexhull，1000rollout/edge估计。
- 验证依据：5seeds; systematicDiRL可得轨迹，LSTS全失败则不能refine；sound不完整且不保证最紧refinement。
- 边界：refined⇒original是子集而非任务等价，不保留全部原最优策略；无视觉grounding/操作关系恢复验证。
- 关联（阅读者推断）：根据行为失败在线/迭代修任务图已覆盖；RF-Agent改结构须有别于这套规范修订。
