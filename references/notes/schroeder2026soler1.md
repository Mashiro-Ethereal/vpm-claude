# schroeder2026soler1 — SOLE-R1: Video-Language Reasoning as the Sole Reward for On-Robot Reinforcement Learning

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2603.28730)；[书目正式版本](https://arxiv.org/pdf/2603.28730)。版本：[Submitted on 30 Mar 2026 ( ), last revised 26 May 2026 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/schroeder2026soler1.web.txt](_sources/schroeder2026soler1.web.txt)。

- 原文问题：仅video-language reasoning reward支持在线RL。
- 原文方法/输入/监督：per-step spatiotemporal CoT；合成轨迹/推理+continuous progress、SFT和verifiable RL。
- 原文摘要报告的验证：4sim环境及真机，random initialization/24unseen tasks，无task-specific成功标签、demo或tuning。
- 阅读者判断/待核细节：零样本指deployment，模型训练集仍巨大；sole reward是否potential形式需全文。
- 与基础工作的关系：直接覆盖history reasoning+online RL+reward hacking鲁棒性。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2603.28730v2](https://arxiv.org/html/2603.28730v2)。实际范围：§2–4、5.3、5.7；未全Appendix/40task逐曲线。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/schroeder2026soler1.full.reading.txt](_sources/schroeder2026soler1.full.reading.txt)。

正文证据与阅读判断：video-nativeCoT当前Kframes+firstframe+previousprediction、remaininggoals，directabsoluteprogress reward非必须PBRS。sim随机actions偏离及stateinterpolation恢复、privilegedgeometry生成CoT/progress；realOXEvideo逆序时间labels，SFT+GRPORLVR。§5.3 40tasks四sim+realzero-shotfromscratch DrQv2，明确无trueexternalreward、无taskdemo、无taskfinetuning，24tasks≥50%vsGPT5 7/Gemini5。§5.7VLAsteering2→median12%。已覆盖零样本从无外部success学习、历史方向remainingsteps/failuresynthesis；泛化取决视觉/teacherdata，不能仅去true-success算首创。
