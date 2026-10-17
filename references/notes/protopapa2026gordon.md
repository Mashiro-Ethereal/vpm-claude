# GORDON: Graph-based Object-centric Rewards for Decomposition of Long-Horizon Manipulation

引用键：protopapa2026gordon。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2608.03753v1)。
- 版本、发表状态与实际范围：arXiv v1 preprint；实际读摘要、§III全部方法、§IV-A实验/§IV-B消融、§V讨论。书目所列年份：2026；venue：arXiv（除明确写已核验者，书目状态不视为独立确认）。
- WHY：视觉示范奖励易受背景/机器人运动影响。。
- HOW：bbox/语义物体图Transformer，活动加权且maskrobot；TCC+重建训练，负final-embedding距离+goalclassifier bonus；从reward梯度切阶段学分策略。
- WHAT：ManiSkill长任务高成功，提供视觉图奖励、自动阶段发现/策略组合与appearance/noise消融。
- 假设、监督与输入：ManiSkill用simulator annotated2D/3D boxes、class及robotidentity；每task25action-free demos；5seed16eval。
- 验证依据：LongAvg74.4 vs同体系decomposed oracle49.0；RoboHorizon结果取已发表benchmark，不是全部同训练公平对照。
- 边界：奖励不是PBRS；活动object一旦激活persist，顺序分策略与motionplanner拼接；检测真实部署非当前实证。
- 关联（阅读者推断）：图+视觉+自动阶段奖励+RL已被覆盖。需要低权限感知、历史/回退与同控制器对照而非拼装。
