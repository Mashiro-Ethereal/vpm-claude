# yang2026rarm — RARM: Confidence-Gated Progress Reward Modeling for RL in Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2606.22027)；[书目正式版本](https://arxiv.org/pdf/2606.22027)。版本：[Submitted on 20 Jun 2026 ( ), last revised 25 Aug 2026 (this version, v4)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/yang2026rarm.web.txt](_sources/yang2026rarm.web.txt)。

- 原文问题：参考demo锚定进度且以confidence抑制视觉高估。
- 原文方法/输入/监督：general videos contrastive temporal训练，无robot特定data；deployment匹配rollout clips/reference clips，只奖confident forward progress。
- 原文摘要报告的验证：9个LIBERO/MetaWorld任务与4真机任务，cloth folding等收益。
- 阅读者判断/待核细节：single successful reference是task监督；confidence含义及错误匹配预算需全文。
- 与基础工作的关系：‘不确定性门控进度奖励’已被明确覆盖。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2606.22027v4](https://arxiv.org/html/2606.22027v4)。实际范围：§3、4.1–4.3、6；未全部附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/yang2026rarm.full.reading.txt](_sources/yang2026rarm.full.reading.txt)。

正文证据与阅读判断：通用定向video5frameclip，localpositive/time-reversednegative，DINOv3LoRAcrossattention；单successreferenceprogress+confidencegate且只奖新maxprogress，低conf/failure保持而不回退，非PBRS。sim9tasks1MDrQv25seed+success。realDSRLπ0 fourtask90train/30evalTable1 drawer29/30eraser25handover23fold25 vsbinary23/20/14/7及Robometer20/20/5/9。已覆盖方向/history/confidence/realonline；maxprogress丢回退不等不能恢复(all-to-all允许重试后前进)，representativeref/embodimentshiftlimits。
