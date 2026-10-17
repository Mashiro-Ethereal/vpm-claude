# tan2026dopamine — Robo-Dopamine: General Process Reward Modeling for High-Precision Robotic Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；CVPR 2026（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2512.23703)；[书目正式版本](https://openaccess.thecvf.com/content/CVPR2026/papers/Tan_General_Process_Reward_Modeling_for_Robotic_Reinforcement_Learning_CVPR_2026_paper.pdf)。版本：[Submitted on 29 Dec 2025]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/tan2026dopamine.web.txt](_sources/tan2026dopamine.web.txt)。

- 原文问题：通用step-aware multi-view process reward与不改目标的shaping。
- 原文方法/输入/监督：3400+小时dataset，step reward discretization、多视角fusion；Dopamine-RL使用policy-invariant shaping。
- 原文摘要报告的验证：摘要报告single expert trajectory适配，150真机rollouts从近0到95%。
- 阅读者判断/待核细节：庞大预训练与one-shot域适配均为预算；理论终态/在线条件需全文。
- 与基础工作的关系：直接覆盖PRM4RL的视觉化+PBRS，必须识别实质差异。原arXiv标题已是Robo-Dopamine。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2512.23703v1](https://arxiv.org/html/2512.23703v1)。实际范围：§3.1.1–2、3.2.2、4.2–3，未全部证明附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/tan2026dopamine.full.reading.txt](_sources/tan2026dopamine.full.reading.txt)。

正文证据与阅读判断：humanmultiviewstagekeyframe、35Msamples3400h100ktrajectories，startgoalbeforeafter有符号hop、incremental/forward/backwardfusion、oneshotadapt。r_gold+γΦ'−Φ；真实r_gold阈值Φ≥.95用模型替true success，PBRS只保持此基底reward（不能额外保证true task）。10sim8real/CalQLhumanintheloop；Table4Insert19/20ID→15/20object，Circuit20→17；Table5full85/noPBRS41.3/nooneshot63.2。视觉progress+方向+PBRS已覆盖，固定势/终止边界为标准条件。
