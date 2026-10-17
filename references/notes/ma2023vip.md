# ma2023vip — VIP: Towards Universal Visual Reward and Representation via Value-Implicit Pre-Training

阅读日期：2026-10-06。书目年份/venue：2023；ICLR 2023（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2210.00030)；[书目正式版本](https://openreview.net/pdf?id=YJ7o2wetJ2)。版本：[Submitted on 30 Sep 2022 ( ), last revised 7 Mar 2023 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/ma2023vip.web.txt](_sources/ma2023vip.web.txt)。

- 原文问题：从无动作人类视频学可用于新机器人任务的价值表征。
- 原文方法/输入/监督：以goal-conditioned offline RL的dual value目标自监督训练；输入当前/目标图像，价值隐含在embedding距离中。Ego4D预训练，无新任务微调。
- 原文摘要报告的验证：摘要报告仿真与真机reward-based control，以及少至20条轨迹的真机offline RL。
- 阅读者判断/待核细节：目标图像明确且视频可提供时间结构；静态距离不能自动解释历史依赖或策略可达性。
- 与基础工作的关系：把PRM4RL的程序势替换为学得的视觉势已是既有路径；须精读奖励是否势差及监督预算。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2210.00030v2](https://arxiv.org/html/2210.00030v2)。实际范围：§3–5，真实Table1；未完整证明附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/ma2023vip.full.reading.txt](_sources/ma2023vip.full.reading.txt)。

正文证据与阅读判断：被动humanvideo dualvalue学discountedtemporalgoal-distance，Prop4.1 deterministicdynamics；实现V=−L2distance。reward S(o')−S(o)=rawdistance(1−γ)S'+PBRS，不是purePBRS。FrankaKitchen12×3views，MPPI更强compute可44%mean而base更易rewardexploitation。真实4task约20demosRWRoffline：Table1 VIPRWR100/90/60/90 vsBC50/50/10/20，10eval。humanvalue到robotreachability属泛化假设；‘视觉value替代progress’很早已有。
