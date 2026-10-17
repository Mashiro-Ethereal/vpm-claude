# Improving the Effectiveness of Potential-Based Reward Shaping in Reinforcement Learning

引用键：muller2025effectivepbrs。阅读日期：2026-10-06。

- 来源：[原始arXiv HTML](https://arxiv.org/html/2502.01307)。
- 版本、发表状态与实际范围：v1正文9页预印本；本子智能体读摘要，主智能体补读§3–5方法/分析与§6.1设置。AAMAS2025 extended abstract为书目关联，不表示本次正文只有扩展摘要。
- WHY：策略不变性为何不必带来有效探索/有限预算收益。
- HOW：分析初Q、外部奖励及势scale/offset与初始化的关系。
- WHAT：相同偏好势的平移会改变学习表现，最优目标等价不能代替学习器分析。
- 假设、监督与输入：固定势、critic初值、外部任务奖励与相应scale/shift。
- 验证依据：摘要提及Gridworld、CartPole、MountainCar；主智能体实际审读§6.1设置，非本子智能体完整实验复核。
- 边界：较小任务，不直接建立跨视觉reward families/tasks/learners的预算收益预测；此后者仍需实验。
- 关联（阅读者推断）：是有限训练收益方向的强基线；简单scale/offset/critic初始化必须控制。“固定Φ最优等价但有限训练不同”本身已经是旧结论。
