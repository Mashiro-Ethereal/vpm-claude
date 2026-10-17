# wu2026lrm — Large Reward Models: Generalizable Online Robot Reward Generation with Vision-Language Models

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2603.16065)；[书目正式版本](https://arxiv.org/pdf/2603.16065)。版本：[Submitted on 17 Mar 2026 ( ), last revised 30 Sep 2026 (this version, v3)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/wu2026lrm.web.txt](_sources/wu2026lrm.web.txt)。

- 原文问题：VLM适配为多interface frame-level reward。
- 原文方法/输入/监督：real robot/human/sim mixed数据，progress/completion/temporal pair比较；IL起始policy用PPO refinement。
- 原文摘要报告的验证：held-out long任务仿真PPO；2平台4真机task progress-weighted BC。
- 阅读者判断/待核细节：真机证据是weighted BC，不能写成全真机PPO；v3为2026-09-30。
- 与基础工作的关系：直接包含接口与非特权reward闭环，评价目标需更精确。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

