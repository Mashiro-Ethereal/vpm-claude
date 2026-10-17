# Reward Machine Inference for Robotic Manipulation

引用键：baert2024rminference。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2412.10096v1)。
- 版本、发表状态与实际范围：arXiv v1 preprint；实际读摘要、§3全方法/§4 learning、§5.1设置与部分结果。书目所列年份：2024；venue：arXiv preprint; related IBRL@RLC 2025 workshop version（除明确写已核验者，书目状态不视为独立确认）。
- WHY：从视觉示范直接学RM。。
- HOW：ResNet50视觉embedding，DBSCAN驻留密集簇为subgoal，原型事件抽象演示inferRM；RMstate策略输入下一goal prototype。
- WHAT：robosuiteFranka五桌面任务无需预给事件/图。
- 假设、监督与输入：全可观测frontcrop图供label、topdown图供像素Q；每任务调DBSCAN/阈值；1–6条覆盖可行顺序的algorithmicexpert演示。
- 验证依据：10runs，主要totalreward/placementdistance；论文泛称人类demo但此实验实际algorithmicexpert。
- 边界：当前prototype抽象不自动保证POMDP历史充分；没有欠覆盖失败状态/未见历史义务的实证。
- 关联（阅读者推断）：视觉自动RM强近邻，不能把视觉自动离散结构当新颖点；与GCR/TDM组合须强对比。
