# Dynamics-Aware Comparison of Learned Reward Functions

引用键：wulfe2022dard。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/pdf/2201.10081)。
- 版本、发表状态与实际范围：PDF页眉PublishedICLR2022（书目arXiv遗漏）；实际读摘要、§4 Eq3 transform、§5实验/限制、附录模型误差讨论被正文引用部分。书目所列年份：2022；venue：arXiv（除明确写已核验者，书目状态不视为独立确认）。
- WHY：EPIC会访问不可实现转移导致OOD误差。。
- HOW：转移模型条件下一步采样canonicalization，避免EPIC任意不物理state对；保持势差不变。
- WHAT：BouncingBalls/Reacher上true和learnedmodel预测rewardpolicyreturn。
- 假设、监督与输入：有transitionmodel/referenceR/覆盖actions；learned模型低维one-step较准确。
- 验证依据：正文识别Reacherreward敏感导致模型false-equivalence；非全视觉高维结果。
- 边界：一项混合transition仍不严格in-distribution；小步长smoothreward所有近邻相似时对噪声敏感。
- 关联（阅读者推断）：可检验选取行为测试/后继信息帮助RFsearch，但单纯dynamics-awareoffline距离已旧。
