# zhang2026r2vlm — Recurrent Reasoning with Vision-Language Models for Estimating Long-Horizon Embodied Task Progress

阅读日期：2026-10-06。书目年份/venue：2026；CVPR 2026（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2603.17312)；[书目正式版本](https://arxiv.org/pdf/2603.17312)。版本：[Submitted on 18 Mar 2026]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/zhang2026r2vlm.web.txt](_sources/zhang2026r2vlm.web.txt)。

- 原文问题：低成本递归推理维护长期任务完成状态。
- 原文方法/输入/监督：local snippets+evolving CoT记录分解/关键步/完成状态；ALFRED/Ego4D自动生成训练。
- 原文摘要报告的验证：progress估计、policy learning、RL reward和proactive assistance。
- 阅读者判断/待核细节：记忆CoT错误传播与具体RL结果需全文；摘要非只有静态bench。
- 与基础工作的关系：‘语言阶段memory在线累计’已被直接研究。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2603.17312v1](https://arxiv.org/html/2603.17312v1)。实际范围：§3.1–3.3、4.2、4.4；未全训练/附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/zhang2026r2vlm.full.reading.txt](_sources/zhang2026r2vlm.full.reading.txt)。

正文证据与阅读判断：streaminglocal4frames+previousCoT memory动态merge/split/reordersteps、completionstatus；ALFRED11499traj124821dialogs/Ego4D13965127694，stage比例+内timeprogress，earlysharedstepsdistractor；SFT+RL。Table1 ALFREDMAE2.19 Ego4D19.25，人工审核benchmark。Table4 AI2THOR SPRINT50konlineIQL step2.45 task.50 vsbase2.20/.42；非真实robot。已有recurrentmemory/planadaptation和denseprogressRL。
