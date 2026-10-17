# Reward Machines for Vision-Based Robotic Manipulation

引用键：camacho2021visionrm。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://www.cs.toronto.edu/~acamacho/papers/cam-var-zen-jai-isc-kal-icra21.pdf)。
- 版本、发表状态与实际范围：正式ICRA2021作者存档PDF；实际读摘要、§III/IV及IV-A、§V/VI方法与实验图。CSV arXiv2012.14464是不同题名五作者早版；正式六作者含Zeng，原书目未改。书目所列年份：2021；venue：ICRA 2021（除明确写已核验者，书目状态不视为独立确认）。
- WHY：像素DQN难学多阶段操作。。
- HOW：演示抽象为planning graph，给定feature detectors；γ^graph-distance势与独立pick/place像素DQN，共享演示回放。
- WHAT：视觉UR5 PyBullet两/三block任务；抽象状态/奖励分别消融，远离目标可回退负奖。
- 假设、监督与输入：硬编码物体/夹持feature；goal可与非goal分辨；RGB320×160、depth校准像素动作。
- 验证依据：实际读Fig2–3与方法；此演示图构造明确presumes task Markovian，非Markov场景引其他方法。
- 边界：不是仅成功演示时间百分比；已支持多路径/状态回退。零最优Q依赖RM边一动作确定转移，不能外推一般连续控制。
- 关联（阅读者推断）：视觉RM+演示结构+势+RL已存在；当前可撤销关系图并非首次。
