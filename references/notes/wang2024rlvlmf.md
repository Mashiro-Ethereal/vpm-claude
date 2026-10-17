# wang2024rlvlmf — RL-VLM-F: Reinforcement Learning from Vision Language Foundation Model Feedback

阅读日期：2026-10-06。书目年份/venue：2024；ICML 2024 / PMLR 235（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2402.03681)；[书目正式版本](https://raw.githubusercontent.com/mlresearch/v235/main/assets/wang24bn/wang24bn.pdf)。版本：[Submitted on 6 Feb 2024 ( ), last revised 14 Jun 2024 (this version, v4)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/wang2024rlvlmf.web.txt](_sources/wang2024rlvlmf.web.txt)。

- 原文问题：VLM自动提供偏好，学习机器人reward。
- 原文方法/输入/监督：语言goal+agent图像对，VLM选择偏好，偏好模型生成reward而非直接raw score。
- 原文摘要报告的验证：classic control及刚体/关节/形变操作闭环学习优于同假设对照。
- 阅读者判断/待核细节：仍依赖VLM视觉偏好准确性和在线查询；摘要无历史模型保证。
- 与基础工作的关系：RF-Agent以反馈搜索与本方法用视觉偏好学reward有不同反馈来源。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

