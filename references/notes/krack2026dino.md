# krack2026dino — Rewarding DINO: Predicting Dense Rewards with Vision Foundation Models

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2603.16978)；[书目正式版本](https://arxiv.org/pdf/2603.16978)。版本：[Submitted on 17 Mar 2026]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/krack2026dino.web.txt](_sources/krack2026dino.web.txt)。

- 原文问题：视觉foundation模型拟合实际task reward而非示范轨迹进度。
- 原文方法/输入/监督：24 MetaWorld+任务sampled data、rank loss，language-conditioned compact模型。
- 原文摘要报告的验证：pairwise accuracy、rank correlation、calibration，以及off-the-shelf RL、真机泛化。
- 阅读者判断/待核细节：实际reward标签或特权状态预算须全文；纯视频自监督不可同列比较。
- 与基础工作的关系：静态reward质量与RL实验都已存在，state reward监督可能改变比较条件。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2603.16978v1](https://arxiv.org/html/2603.16978v1)。实际范围：III-A/C、IV-E/F；未完整rankingproof/results。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/krack2026dino.full.reading.txt](_sources/krack2026dino.full.reading.txt)。

正文证据与阅读判断：双视角DINOv3smallpatch+MiniLM/FiLM head，currentonlyranking；teacher需现有expertreward，random/expert switches广状态采样。8seenMWtasksPPO1M+真实sparsePBRS，未solvedassembly。simtoreal只rewardvisualdiagnostic。作者部分观测PBRSinvalid的笼统说法不自动成立：固定deterministicobservationmap可composition成statepotential；历史/随机obs/terminal界需另审，本文不据此指控实现。低成本视觉奖励但非无privilegedlabel训练。
