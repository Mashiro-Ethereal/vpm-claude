# lv2026viva — ViVa: A Video-Generative Value Model for Robot Reinforcement Learning

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2604.08168)；[书目正式版本](https://arxiv.org/pdf/2604.08168)。版本：[Submitted on 9 Apr 2026 ( ), last revised 5 Jun 2026 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/lv2026viva.web.txt](_sources/lv2026viva.web.txt)。

- 原文问题：以未来物理动态支撑value而非静态VLM。
- 原文方法/输入/监督：pretrained video generator预测未来proprioception+scalar value，时空priors。
- 原文摘要报告的验证：3-task metric evaluation；RECAP平均success80%。
- 阅读者判断/待核细节：proprioception/未来监督及BC/online类别须正文；视频生成成本不可忽略。
- 与基础工作的关系：基于foresight的value路线已覆盖。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2604.08168v2](https://arxiv.org/html/2604.08168v2)。实际范围：§3、4.3、4.5与Table1–6；未完整Appendix。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/lv2026viva.full.reading.txt](_sources/lv2026viva.full.reading.txt)。

正文证据与阅读判断：Wan2.2 videogenerativeprior，current3RGB+proprio jointlyfutureproprio+scalarvalue flowmatching；binaryoutcome监督G=(T−t)/T成功、失败+1，实际cost语义（小更好）而非规范higherbetterV。约20h3taskmix，50heldouteps人工milestone/error。Table1 shirtρ.982（VLM.720），但boxVLM.945高于ViVa.850；eventMS/ES/MDR/ErrorDR单列避免globalcorr掩盖。真实RECAP两round三task90/70/80平均80vsVLM63.3。已覆盖futurephysicaldynamics与失败outcomevalue；不是仅静态进度，生成predictor不等actioncounterfactual价值。
