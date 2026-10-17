# liu2026primo — From Passive Observer to Active Critic: Reinforcement Learning Elicits Process Reasoning for Robotic Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；arXiv; ECCV 2026 author-reported（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2603.15600)；[书目正式版本](https://arxiv.org/pdf/2603.15600)。版本：[Submitted on 16 Mar 2026 ( ), last revised 7 Jul 2026 (this version, v2)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/liu2026primo.web.txt](_sources/liu2026primo.web.txt)。

- 原文问题：用outcome RL让video MLLM主动评估进度。
- 原文方法/输入/监督：7B、初始/当前image锚定历史，CoT outcome-based RL；PRIMO dataset。
- 原文摘要报告的验证：reward reasoning MAE约减50%；RoboFail67%、o1高6pp。
- 阅读者判断/待核细节：训练reward model的RL不自动等于robot closed-loop RL；摘要未明确policy实验。
- 与基础工作的关系：structured temporal reasoning和failure detection已有覆盖。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

