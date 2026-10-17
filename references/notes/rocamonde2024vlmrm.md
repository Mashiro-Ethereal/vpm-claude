# rocamonde2024vlmrm — Vision-Language Models are Zero-Shot Reward Models for Reinforcement Learning

阅读日期：2026-10-06。书目年份/venue：2024；ICLR 2024（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2310.12921)；[书目正式版本](https://openreview.net/pdf?id=N0I2RtD8je)。版本：[Submitted on 19 Oct 2023 ( ), last revised 14 Mar 2024 (this version, v2)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/rocamonde2024vlmrm.web.txt](_sources/rocamonde2024vlmrm.web.txt)。

- 原文问题：语言指定任务的zero-shot视觉reward。
- 原文方法/输入/监督：CLIP图文相似度，可baseline prompt与embedding projection去掉无关维度；单句目标。
- 原文摘要报告的验证：MuJoCo humanoid跪下/劈叉/莲花坐，规模效应与失效分析。
- 阅读者判断/待核细节：作者明确空间推理和OOD视觉限制；这不是long-horizon manipulation全面验证。
- 与基础工作的关系：reward语义对齐与闭环效果早已有研究，不能从静态CLIP分数推新颖性。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

