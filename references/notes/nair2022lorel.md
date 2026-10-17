# nair2022lorel — Learning Language-Conditioned Robot Behavior from Offline Data and Crowd-Sourced Annotation

阅读日期：2026-10-06。书目年份/venue：2022；CoRL 2021 / PMLR 164（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2109.01115)；[书目正式版本](https://proceedings.mlr.press/v164/nair22a/nair22a.pdf)。版本：[Submitted on 2 Sep 2021 ( ), last revised 31 Oct 2021 (this version, v2)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/nair2022lorel.web.txt](_sources/nair2022lorel.web.txt)。

- 原文问题：用离线交互与众包语言指定多任务行为。
- 原文方法/输入/监督：包含高度次优的robot offline数据与language labels，classifier判断state change是否完成instruction，用于offline RL。
- 原文摘要报告的验证：真实Franka抽屉/移动物体，报告优于goal image与language IL超过25%。
- 阅读者判断/待核细节：依赖众包标注与robot域数据，reward分类非精细阶段势。
- 与基础工作的关系：语言状态变化和suboptimal数据已长期存在，不能说奖励文献仅成功示范。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

