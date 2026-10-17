# kim2025reds — Subtask-Aware Visual Reward Learning from Segmented Demonstrations

阅读日期：2026-10-06。书目年份/venue：2025；ICLR 2025（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2502.20630)；[书目正式版本](https://proceedings.iclr.cc/paper_files/paper/2025/file/277628cff838927d869cd1f671328ce0-Paper-Conference.pdf)。版本：[Submitted on 28 Feb 2025]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/kim2025reds.web.txt](_sources/kim2025reds.web.txt)。

- 原文问题：segmented demo学习subtask-aware visual reward。
- 原文方法/输入/监督：action-free视频按subtask分段，segment作为ground-truth reward；EPIC距离对齐reward，contrastive目标推断当前subtask。
- 原文摘要报告的验证：MetaWorld与FurnitureBench，unseen task/embodiment泛化。
- 阅读者判断/待核细节：需要segmentation监督；最接近PRM4RL的阶段感知视觉化，具体标注负担须正文。
- 与基础工作的关系：‘阶段语义+visual reward’已被直接覆盖，不能仅改监督模态。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2502.20630v1](https://arxiv.org/html/2502.20630v1)。实际范围：§4–5.3，未全部附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/kim2025reds.full.reading.txt](_sources/kim2025reds.full.reading.txt)。

正文证据与阅读判断：stage-segmentedexpert（MWcode/Furniturehuman）、causalhistory/subtasktext，EPIC+expertprogressmargin+stagecontrastive；onlinepolicyrolloutautomaticstage/failurepseudolabelfinetune。MetaWorld8tasks50demo+100kcollect，DreamerV34runs；真实OneLeg300expert200policyrollout、IQL150onlineepisodes20eval，completedsubtasks1.10→2.45不是完整success。已覆盖stagehistoryonlineadaptation，failure后其余固定当前stage是假设；有限distributionEPIC不等全MDP最优定理。
