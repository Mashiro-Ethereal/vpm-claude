# ma2025gvl — Vision Language Models are In-Context Value Learners

阅读日期：2026-10-06。书目年份/venue：2025；ICLR 2025（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2411.04549)；[书目正式版本](https://proceedings.iclr.cc/paper_files/paper/2025/file/54854cf15a24fff9f5134a8641136fe4-Paper-Conference.pdf)。版本：[Submitted on 7 Nov 2024]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/ma2025gvl.web.txt](_sources/ma2025gvl.web.txt)。

- 原文问题：利用VLM世界知识在上下文中预测任务进度。
- 原文方法/输入/监督：把视频帧打乱后做temporal ordering，zero-/few-shot，支持跨任务/跨具身人类示例。
- 原文摘要报告的验证：超过300真实任务，dataset filtering、success detection、advantage-weighted regression。
- 阅读者判断/待核细节：这里称temporal value不自动是Bellman value；摘要应用不等于在线RL训练。
- 与基础工作的关系：提示顺序和语义先验可改善进度，不需专门训练；需与进度定义区分。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2411.04549v1](https://arxiv.org/html/2411.04549v1)。实际范围：§3、4.3；7taskpolicy段完整，未全表。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/ma2025gvl.full.reading.txt](_sources/ma2025gvl.full.reading.txt)。

正文证据与阅读判断：全trajectory shuffling+autoregressivepercent+firstanchor+ICL，30sampleframes，所谓value目标t/T不是Bellman校准。§4.3 realALOHA7tasks10eval，GVLΔvalueexponential加权DP，有VOC与policygain关联；open-drawer/remove-gears视角差rewardnoise可伤policy。全视频输入离线不能直接当causalonline；quality-policyassociation不是2026才有。

补读 Table 3：banana-handover VOC .73，GVL+DP 7/10、DP 5/10；bowl-in-rack .57、7/10 vs 6/10；open-drawer .09、4/10 vs 6/10；remove-gears .19、4.67/10 vs 7/10；fold-dress .66、7/10 vs 7/10。原文§4.3称预测质量与收益有关，但没有报告 Pearson 系数；表中分数型结果不能统一改写为整数成功次数。§5作者局限：VOC 更适合 a-periodic、expert 帧有唯一顺序的任务，擦拭/搅拌有歧义。
