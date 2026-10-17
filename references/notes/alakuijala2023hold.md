# alakuijala2023hold — Learning Reward Functions for Robotic Manipulation by Observing Humans

阅读日期：2026-10-06。书目年份/venue：2023；ICRA 2023（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2211.09019)；[书目正式版本](https://arxiv.org/pdf/2211.09019)。版本：[Submitted on 16 Nov 2022 ( ), last revised 7 Mar 2023 (this version, v2)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/alakuijala2023hold.web.txt](_sources/alakuijala2023hold.web.txt)。

- 原文问题：从无标签人类视频学task-agnostic goal distance。
- 原文方法/输入/监督：直接temporal regression或time-contrastive embedding距离，输入current/goal图像；无需预先robot数据或专门任务demo。
- 原文摘要报告的验证：多个仿真任务相较仅sparse reward更快。
- 阅读者判断/待核细节：仍有task completion sparse reward；摘要未给纯dense唯一reward的效果。
- 与基础工作的关系：视觉distance shaping已有成熟近邻，不能只移植PRM4RL几何势。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

