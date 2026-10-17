# Know Where You’re Uncertain When Planning with Multimodal Foundation Models: A Formal Framework

Bhatt et al.；MLSys 2025。补充检索，2026-10-06。

- 来源：[正式论文](https://proceedings.mlsys.org/paper_files/paper/2025/file/703f727ec10190b2fddcf8e24f52df48-Paper-Conference.pdf)、[作者代码](https://github.com/uncertainty-in-planning/uncertainty-in-planning.github.io)。保存 PDF 和文本。
- 实际阅读：摘要、§3–4 定义与框架浏览、§5.1–5.2 细读、§6.2–6.3 与 Table 2；未逐项核验附录或理论证明。
- 问题：多模态规划中的感知不确定性和决策不确定性如何分别估计与干预。
- 方法：利用校准数据和 conformal 思路估计感知不确定性，通过形式规格相关的 FMDP 估计计划符合要求的程度；低感知置信度触发旋转相机、换视角或等待重观测；另筛选数据微调计划模型。
- 实验证据：LLaVA-1.5-7B，CARLA 和真实驾驶/地面机器人相关场景；读取了 50 个真实测试场景及主动观察、微调比较。核心报告包括置信/不确定性指标与规格满足概率，不是长程操纵 RL 的样本效率。
- 边界：§5.1 以感知阈值触发观察，没有把每种观察的资源代价及其改变训练/控制结果的价值作为核心优化对象。校准论断也受数据条件约束，本笔记没有独立证明其保证。
- 对本项目的判断：仅按奖励不确定性触发多看一眼已有强近邻；若考虑主动奖励验证，应比较该类阈值方法，并区分信息增益与实际任务收益。
