# chen2026topreward — TOPReward: Token Probabilities as Hidden Zero-Shot Rewards for Robotics

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2602.19313)；[书目正式版本](https://arxiv.org/pdf/2602.19313)。版本：[Submitted on 22 Feb 2026 ( ), last revised 22 Jul 2026 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/chen2026topreward.web.txt](_sources/chen2026topreward.web.txt)。

- 原文问题：从VLM内部完成token概率读取dense progress。
- 原文方法/输入/监督：视频prefix+指令；无reward-model训练，完成likelihood而非生成数值。
- 原文摘要报告的验证：130任务/4机器人ManiRewardBench与OXE，success detection、offline reward-weighted BC。
- 阅读者判断/待核细节：验证主要预测及offline BC；概率完成不是必然校准的策略价值，摘要无在线RL证据。
- 与基础工作的关系：训练free reward接口、instruction敏感性和time-index对照已有明确工作。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2602.19313v2](https://arxiv.org/html/2602.19313v2)。实际范围：§3、4.4、5；未完整大基准table。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/chen2026topreward.full.reading.txt](_sources/chen2026topreward.full.reading.txt)。

正文证据与阅读判断：VLM completionTrue tokenlogprob score chronologicalprefix causal；整episode minmax normalization noncausal只offlineVOC/curve，原文明区分。positiveexpΔlogprob权重 β.2cap2，真实SO100 six tasks50demoeachofflinepi0RWBC10eval，部分subtaskscore不是全completionrate。历史prefixprobabilities并非reliable calibratedreachability；template/tokenchoice/perceptionlimits。
