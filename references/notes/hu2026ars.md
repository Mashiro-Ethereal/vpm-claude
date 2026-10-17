# hu2026ars — ARS: Agentic Reward System for Robot Learning

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2609.34484)；[书目正式版本](https://arxiv.org/pdf/2609.34484)。版本：[Submitted on 28 Sep 2026]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/hu2026ars.web.txt](_sources/hu2026ars.web.txt)。

- 原文问题：training-free VLM event proposal+verification的agentic reward。
- 原文方法/输入/监督：offline trajectory+instruction，可optional outcome labels与visual refs；subagent事件时间线由primary核验再估progress。
- 原文摘要报告的验证：27B semantic-mismatch/wrong-object benchmark、仿真policy learning、真机工业多螺钉mixed-quality offline learning。
- 阅读者判断/待核细节：离线整轨迹可看未来；terminal labels/ref是可选但需比较消融。
- 与基础工作的关系：RF-Agent和结构progress的近邻；‘agent审查语义错误’并非未有人做。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2609.34484v1](https://arxiv.org/html/2609.34484v1)。实际范围：§3、4.4、5，未全simtable/Appendix。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/hu2026ars.full.reading.txt](_sources/hu2026ars.full.reading.txt)。

正文证据与阅读判断：此ARS为AgenticRewardSystem论文非阅读skill。eventproposal/independentverification/adaptivecropwindow，允许laterframes retrospective判早期grasp；terminaloutcome/reference可选。用Δprogresschunkpositive筛选weightedBC，非criticRL。真实screw3step2574demo+3092offlinepolicyrollout、1seed200eval；Table5 allrollout50.5/demoonly58/ARS72/ARS+3image-textreferences81.5%。作者§5自述offline适合，causalonlineopen/distillationfuture。核对细粒度事件、反退/partial、视觉验证/监督teacher已覆盖，未实际online。
