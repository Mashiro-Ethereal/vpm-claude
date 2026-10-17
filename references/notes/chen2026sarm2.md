# chen2026sarm2 — SARM2: Multi-Task Stage Aware Reward Modeling for Self Improving Robotic Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2606.10305)；[书目正式版本](https://arxiv.org/pdf/2606.10305)。版本：[Submitted on 9 Jun 2026]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/chen2026sarm2.web.txt](_sources/chen2026sarm2.web.txt)。

- 原文问题：multi-task stage reward推动自主rollout改进VLA。
- 原文方法/输入/监督：action primitive stage estimator+MMoE value head；SPIRAL on-policy reward learning。
- 原文摘要报告的验证：10-task reward benchmark，MSE降80%；Folding Shorts58→100%、Whiteboard50→90%。
- 阅读者判断/待核细节：stage和reward标签预算、SPIRAL是否完整online RL须正文。
- 与基础工作的关系：已覆盖stage+跨task reward+真机自改进，须区分更强问题。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2606.10305v1](https://arxiv.org/html/2606.10305v1)。实际范围：§3方法、4.2Table2；6.14未完整读。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/chen2026sarm2.full.reading.txt](_sources/chen2026sarm2.full.reading.txt)。

正文证据与阅读判断：21taskagnosticprimitives+null、200h100tasks精选66h；3views/proprio/tasktext+6framecausal/firstanchor/rewind，MMoE targetnormalizedremainingsteps −(T−t)/T。SPIRAL denseTD3+MCsparse residualRL、约100弱policyrollout一次humanannotadapt RM2然后loop。Realshorts670eps20h/whiteboard530eps10h；3roundTable2 flat12/12crumple8/12、whiteboard18/20 mean.975 vsRobometer10/12、5/12、13/20 .888，表注不同reward与rolloutepisodes。已覆盖remainingsteps/realonpolicyfailureadaptation；remainingtime不自动policycompletionprobability，非无human预算开始。
