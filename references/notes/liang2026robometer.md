# liang2026robometer — Robometer: Scaling General-Purpose Robotic Reward Models via Trajectory Comparisons

阅读日期：2026-10-06。书目年份/venue：2026；Robotics: Science and Systems XXII（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2603.02115)；[书目正式版本](https://arxiv.org/pdf/2603.02115)。版本：[Submitted on 2 Mar 2026 ( ), last revised 13 May 2026 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/liang2026robometer.web.txt](_sources/liang2026robometer.web.txt)。

- 原文问题：成功progress与跨轨迹偏好联合学习general reward。
- 原文方法/输入/监督：intra progress anchor+same-task intertrajectory preference，RBM-1M超过百万轨迹含real/augmented failure。
- 原文摘要报告的验证：多个benchmark/realworld与downstreamrobot learning。
- 阅读者判断/待核细节：偏好来源和失败类型须正文；已经明确处理failure/suboptimal大数据。
- 与基础工作的关系：不能声称reward模型都只学成功轨迹或无全局失败约束。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2603.02115v2](https://arxiv.org/html/2603.02115v2)。实际范围：III-A–C、IV-Q3、V，未全附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/liang2026robometer.full.reading.txt](_sources/liang2026robometer.full.reading.txt)。

正文证据与阅读判断：RBM1M 21embodiments1Mepisodes含mixedfailed/human/robot/sim；Qwen3VL4B causal8frameprog tokens+pref token，10bin progress timeinterpolation+success+preference，不是stateonly。IVQ3真实DSRL explicitsuccess自动termination20→85%≤45min/10ksteps，stageinference分解20→70%，20eval。100trajectory/7taskfailuredetectionF1 .81 vsRR.74，包含irreversible、stall/nonterminal。V明确force/graspstability/compliance视觉可见前不能识别，longhistoryeventmemory限制。已覆盖失败/causalhistory/terminaldetector/真实selflearning，但未给policyconditioned可达概率。
