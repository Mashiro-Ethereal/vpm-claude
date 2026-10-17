# chen2021dvd — Learning Generalizable Robotic Reward Functions from "In-The-Wild" Human Videos

阅读日期：2026-10-06。书目年份/venue：2021；RSS 2021（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2103.16817)；[书目正式版本](https://www.roboticsproceedings.org/rss17/p012.pdf)。版本：[Submitted on 31 Mar 2021]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/chen2021dvd.web.txt](_sources/chen2021dvd.web.txt)。

- 原文问题：从wild human视频与少量robot数据学通用task reward。
- 原文方法/输入/监督：Domain-agnostic Video Discriminator判断两视频是否same task；用于visual MPC。
- 原文摘要报告的验证：WidowX200在unseen环境由单human demo完成任务，任务/环境zero-shot。
- 阅读者判断/待核细节：依赖小robot dataset+大human corpus；下游是MPC而非本文SAC/PPO。
- 与基础工作的关系：trajectory semantics reward不同于per-step program势，不能忽略控制器区别。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

