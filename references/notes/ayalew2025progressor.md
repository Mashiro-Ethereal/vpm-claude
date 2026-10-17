# ayalew2025progressor — PROGRESSOR: A Perceptually Guided Reward Estimator with Self-Supervised Online Refinement

阅读日期：2026-10-06。书目年份/venue：2025；ICCV 2025（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2411.17764)；[书目正式版本](https://openaccess.thecvf.com/content/ICCV2025/papers/Ayalew_PROGRESSOR_A_Perceptually_Guided_Reward_Estimator_with_Self-Supervised_Online_Refinement_ICCV_2025_paper.pdf)。版本：[Submitted on 26 Nov 2024]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/ayalew2025progressor.web.txt](_sources/ayalew2025progressor.web.txt)。

- 原文问题：无人工标签的进度分布reward与在线OOD修正。
- 原文方法/输入/监督：输入initial/current/goal observation，自监督progress distribution；online RL中adversarial push-back抑制非专家OOD高估；EPIC预训练。
- 原文摘要报告的验证：摘要报告复杂行为RL、无域内微调的真机offline RL/noisy demos。
- 阅读者判断/待核细节：已专门应对reward distribution shift，不能概括现有模型都只看成功示范不适应rollout。
- 与基础工作的关系：PRM4RL若加online reward feedback，PROGRESSOR是直接近邻。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2411.17764v1](https://arxiv.org/html/2411.17764v1)。实际范围：§4–6，未全部附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/ayalew2025progressor.full.reading.txt](_sources/ayalew2025progressor.full.reading.txt)。

正文证据与阅读判断：start/current/goaltriplet normalizedtimeratioGaussianlabel，rewardµ−.4entropy；onlinepushback .9µ+expertloss默认rollouts inferior。MetaWorld6tasks1.5MDrQv25seed；reach已成功时作者承认pushback可能过罚。真实EPIC1.29Mframes预训练、4task各20success20failedemos、RWR-ACT20eval，是offlineweightedBC。uncertainty/onlineadaptation已覆盖；Gaussianvariance不自动等epistemicuncertainty或Qπ−Vπ。
