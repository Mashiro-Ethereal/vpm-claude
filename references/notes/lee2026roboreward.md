# lee2026roboreward — RoboReward: General-Purpose Vision-Language Reward Models for Robotics

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2601.00675)；[书目正式版本](https://arxiv.org/pdf/2601.00675)。版本：[Submitted on 2 Jan 2026 ( ), last revised 8 Jan 2026 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/lee2026roboreward.web.txt](_sources/lee2026roboreward.web.txt)。

- 原文问题：通用robot reward dataset/benchmark与4B/8B evaluator。
- 原文方法/输入/监督：OXE/RoboArena，counterfactual relabel+temporal clipping产生negative/near-miss；VLM评分。
- 原文摘要报告的验证：8B真实robot RL优于Gemini Robotics-ER1.5，接近human reward。
- 阅读者判断/待核细节：失败多数是augment，而非真实物理恢复；MAE与policy关系须全文核实。
- 与基础工作的关系：reward预测与RL收益可能已有相关分析，不能把该联系为空白。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2601.00675v2](https://arxiv.org/html/2601.00675v2)。实际范围：§3–6、Appendix B.1。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/lee2026roboreward.full.reading.txt](_sources/lee2026roboreward.full.reading.txt)。

正文证据与阅读判断：整episode1–5progress，OXE任务counterfactual/截短+RoboArena organicfails。45072train6232val2831humanverifiedtest、14embodiments22models。§3Fig3确有MAE与RL correlation r=.83：Robomimic Lift/Can/Square，同RM架构不同训练checkpoint+base，DSRL;Fig2 3seed binary/continuous/discrete。真实2tasks20eval base5/10、人75/90、RR8B50/80、Gemini10/45%。RM MAE.665/.906且realpolicyrank一致。不能声称没人检验RMaccuracy-policyrelation；但受控checkpoint与有限tasks关系不保证任意指标/跨域因果改善。
