# zakka2022xirl — XIRL: Cross-embodiment Inverse Reinforcement Learning

阅读日期：2026-10-06。书目年份/venue：2022；CoRL 2021 / PMLR 164（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2106.03911)；[书目正式版本](https://proceedings.mlr.press/v164/zakka22a/zakka22a.pdf)。版本：[Submitted on 7 Jun 2021 ( ), last revised 13 Dec 2021 (this version, v3)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/zakka2022xirl.web.txt](_sources/zakka2022xirl.web.txt)。

- 原文问题：跨具身视频学习可迁移奖励。
- 原文方法/输入/监督：多专家具身同任务示范，TCC训练进度表征；当前到goal embedding负距离作为RL奖励。
- 原文摘要报告的验证：XIRL报告新具身迁移及人类视频到仿真robot的样本效率。
- 阅读者判断/待核细节：专家示范及目标latent提供约束，未见行为下进度可靠性需另证。
- 与基础工作的关系：视觉势、阶段结构和跨具身不是新空白；与显式状态程序进度不同。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2106.03911v3](https://arxiv.org/html/2106.03911v3)。实际范围：§3–5，未全部附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/zakka2022xirl.full.reading.txt](_sources/zakka2022xirl.full.reading.txt)。

正文证据与阅读判断：同task多个embodiment成功video，无actionlabels，TCCcyclealignment，假定semantictemporalcorrespondence；goal平均末frameembedding，directreward负squaredL2/κ。X-MAGICAL4embodiment留一SAC5seed50eval。真实humanvideos用于simStatePusher，非realrobotonline；§5.4已展示failedcollisionpartialreward。不能称早期全不会处理失败，也不能保证任意domain/多解/robotvalue。
