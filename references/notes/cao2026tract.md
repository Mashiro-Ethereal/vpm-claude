# cao2026tract — TrAct: Bridging Robot Control and Visual Prediction with Visual Tracks

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2608.24101)；[书目正式版本](https://arxiv.org/pdf/2608.24101)。版本：[Submitted on 25 Aug 2026 ( ), last revised 1 Sep 2026 (this version, v3)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/cao2026tract.web.txt](_sources/cao2026tract.web.txt)。

- 原文问题：visual tracks在action与world model间统一decision接口。
- 原文方法/输入/监督：VLAT产action/track，TWM预测video，VLAC评分预测future选action。
- 原文摘要报告的验证：LIBERO-INTEGRAL27→55%、真机Franka49→76% vsπ0.5。
- 阅读者判断/待核细节：重点MPC式inference而非training奖励，未来模型误差影响选择。
- 与基础工作的关系：未来预测+reward评估早已相接，不能用其有无做新颖性分界。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

