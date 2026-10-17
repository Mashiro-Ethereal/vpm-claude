# Constraint-Aware Zero-Shot Vision-Language Navigation in Continuous Environments

- 作者：Kehan Chen, Dong An, Yan Huang, Rongtao Xu, Yifei Su, Yonggen Ling, Ian Reid, Liang Wang。
- 发表：作者代码库标注TPAMI 2025；DOI 10.1109/TPAMI.2025.3594204。
- 来源：[作者代码库](https://github.com/Chenkehan21/CA-Nav-code)、[原文v3](https://arxiv.org/html/2412.10137v3)。读取日2026-10-06；DOI直连本次失败。
- 阅读范围：摘要、§III方法、§IV-B/C比较及消融、Table I–III；未完整精读补充材料与真机部分。作为期刊契合与邻接任务实例，不作为机械臂奖励方法的直接效果证据。

**原文。** CA-Nav将连续视觉语言导航写为子指令约束依次满足的问题：CSM追踪对象、地点、方向约束；CVM生成视觉价值图。依赖RGB-D、里程计、目标检测/VQA和已有基础模型。R2R-CE、RxR-CE比较与消融支持约束管理和价值地图作用；成功率与路径效率并非一致改善，输入视角也影响可比性。

**阅读者推断。** “语言分解+视觉条件检测+价值图”的一般组合已有TPAMI实例。拟研究视觉进度奖励需要证明新的表示或学习机制，不能仅把该组合从导航搬到操作。其导航价值图用于决策，与在固定RL策略接口下学习奖励的研究对象不同。
