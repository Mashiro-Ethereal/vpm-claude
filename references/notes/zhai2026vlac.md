# zhai2026vlac — A Vision-Language-Action-Critic Model for Robotic Real-World Reinforcement Learning

阅读日期：2026-10-06。书目年份/venue：2026；arXiv; ICML 2026 author-reported（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2509.15937)；[书目正式版本](https://arxiv.org/pdf/2509.15937)。版本：[Submitted on 19 Sep 2025]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/zhai2026vlac.web.txt](_sources/zhai2026vlac.web.txt)。

- 原文问题：联合action/critic生成dense progress delta和done。
- 原文方法/输入/监督：InternVL、pairwise observations+language；human/robot与negative/mismatched samples，reject irrelevance/regression/stagnation；graded HITL。
- 原文摘要报告的验证：4真机task约30→90%/200episodes；HITL再改善50%sample效率至100%。
- 阅读者判断/待核细节：HITL和replay是监督/交互预算；已经考虑失败/回退，需核对delta目标。
- 与基础工作的关系：最直接的视觉pairwise增量reward与真机RL近邻。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2509.15937v1](https://arxiv.org/html/2509.15937v1)。实际范围：§3.1.1、3.2、4.6–4.7，未全附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/zhai2026vlac.full.reading.txt](_sources/zhai2026vlac.full.reading.txt)。

正文证据与阅读判断：成功高效demo、signedpairwise temporalprogress，pixelsmallchange置0、forward/reversegroup、mismatchzero、completionhead、one-shotref；同VLMactorcritic+PPO。真实4tasksTable3baseline90/80/80/100%（10eval），humaninterventionvariants及多robot。§3.2明确offlinehumanreplay、失败reset-return和guidedexploration，不能当无human自主。所谓critic的progress输出与实际PPO Vhead不同；已有signedtransition+success+真实online。
