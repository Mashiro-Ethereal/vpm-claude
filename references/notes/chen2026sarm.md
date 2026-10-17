# chen2026sarm — SARM: Stage-Aware Reward Modeling for Long Horizon Robot Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；ICLR 2026（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2509.25358)；[书目正式版本](https://openreview.net/pdf?id=aemqAxScl9)。版本：[Submitted on 29 Sep 2025 ( ), last revised 27 Apr 2026 (this version, v4)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/chen2026sarm.web.txt](_sources/chen2026sarm.web.txt)。

- 原文问题：不同时长、示范质量下的stage-aware video reward。
- 原文方法/输入/监督：natural-language subtask annotation生成stage+细进度标签，RA-BC按reward筛选/重权。
- 原文摘要报告的验证：真机T-shirt flat83%、crumpled67%，BC8%/0%；human validation。
- 阅读者判断/待核细节：仍需要stage annotation；正文闭环主要BC而非自动在线RL须核对。
- 与基础工作的关系：PRM4RL转向视觉stage的直接近邻，不能只声称fine-grained stage reward。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2509.25358v4](https://arxiv.org/html/2509.25358v4)。实际范围：§3.1、4.2–4.3、AppendixA.8，未完整rewardtable。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/chen2026sarm.full.reading.txt](_sources/chen2026sarm.full.reading.txt)。

正文证据与阅读判断：task-specifichumanstageannot，平均durationstagebudget+内stage线性time；CLIPmulti-view/joint/history stage→progress，严重mistake轨迹排除RMtrain。主要真实pi0/RA-BC offline，200hTshirt。Table3 40kflat10/12、crumple8/12 vsReWiND6/12、3/12；§4.3关联rewardquality/policy。A.8仅simcube300experts100annot+DiffQL10k。已覆盖stage与数据重权；不能当realonlineRL。
