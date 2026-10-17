# feng2026procvlm — ProcVLM: Learning Procedure-Grounded Progress Rewards for Robotic Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2605.08774)；[书目正式版本](https://arxiv.org/pdf/2605.08774)。版本：[Submitted on 9 May 2026 ( ), last revised 26 Sep 2026 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/feng2026procvlm.web.txt](_sources/feng2026procvlm.web.txt)。

- 原文问题：程序结构与阶段内部视觉变化定义progress。
- 原文方法/输入/监督：30 embodied数据集、60M帧合成subtask semantics；阶段budget按结构分配、按视觉变化分布；reasoning先remaining atomic actions再估分。
- 原文摘要报告的验证：ProcVQA/reward benchmark，摘要提reward-guided policy optimization但未给online结果。
- 阅读者判断/待核细节：大规模合成标签及teacher信息不是零监督；具体RL实验需全文。
- 与基础工作的关系：‘程序分解+视觉进度+剩余步骤推理’近乎直接覆盖。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2605.08774v2](https://arxiv.org/html/2605.08774v2)。实际范围：§3–5及Appendix F.1/F.2。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/feng2026procvlm.full.reading.txt](_sources/feng2026procvlm.full.reading.txt)。

正文证据与阅读判断：VLM全video阶段/边界/剩余动作标注400k轨迹60M帧，15k人工筛选refinement；程序stage预算+stage内视觉变化累计标签，Qwen3VL2B连续head+atomicremainingsteps/futureplanning。Table3 RoboFAC真失败1shotSucc VOC .9137/MAEfail .1241/MCC .7918，加failure .9301/.1187/.8053。RoboTwin2任务GRPO：2stageannotateddemos给Proc/Dopa、50无stage给Robometer；Δprogressclip+.1success。真实JAKA仅offline EvoRL优势条件RFT，同50demonstrations，12eval/方法two-bowl，softsuccess SFT37.5/70.8→62.5/83.3（部分放置.5）。程序推理/失败定位覆盖，不是policyconditioned可达性或realonlineRL。零样本Dopa blankanchor作者承认非原生输入。
