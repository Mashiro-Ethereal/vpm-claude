# ma2023liv — LIV: Language-Image Representations and Rewards for Robotic Control

阅读日期：2026-10-06。书目年份/venue：2023；ICML 2023 / PMLR 202（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2306.00958)；[书目正式版本](https://proceedings.mlr.press/v202/ma23b/ma23b.pdf)。版本：[Submitted on 1 Jun 2023]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/ma2023liv.web.txt](_sources/ma2023liv.web.txt)。

- 原文问题：统一语言图像表征和奖励学习。
- 原文方法/输入/监督：无动作、带文本视频，dual RL与互信息对比结合；支持语言/图像目标，预训练EPIC-KITCHENS，可目标域微调。
- 原文摘要报告的验证：摘要报告仿真/真机IL与policy synthesis优于既有表征。
- 阅读者判断/待核细节：进度/价值目标由视频时序派生，不代表任意非专家轨迹的真实回报。
- 与基础工作的关系：语言条件化视觉价值与奖励已覆盖直接视觉化PRM。原arXiv作者含书目遗漏的William Liang、Vaidehi Som。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2306.00958v1](https://arxiv.org/html/2306.00958v1)。实际范围：§4、§5.5与实验setting，未逐表精读所有LCBC结果。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/ma2023liv.full.reading.txt](_sources/ma2023liv.full.reading.txt)。

正文证据与阅读判断：VIPimagevalue+InfoNCElanguagealignment，重复末frame退化video时VIPL等InfoNCE（Prop1）；CLIPResNet50/EpicKitchen90kclips20Mframes20ktexts。§5.5languagepotential用MetaWorld/FrankaKitchenmodelbasedplanning；真实LCBC主要representation验证，勿当realrewardonlineRL。视觉语言价值统一与适应已覆盖；不保证任意robotdynamics可达价值。原书目authorlist漏WilliamLiang/VaidehiSom，未改书目。
