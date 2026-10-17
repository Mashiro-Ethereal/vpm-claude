# escontrela2023viper — Video Prediction Models as Rewards for Reinforcement Learning

阅读日期：2026-10-06。书目年份/venue：2023；NeurIPS 2023（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2305.14343)；[书目正式版本](https://proceedings.neurips.cc/paper_files/paper/2023/file/d9042abf40782fbce28901c1c9c0e8d8-Paper-Conference.pdf)。版本：[Submitted on 23 May 2023 ( ), last revised 30 May 2023 (this version, v2)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/escontrela2023viper.web.txt](_sources/escontrela2023viper.web.txt)。

- 原文问题：从专家视频概率学习无动作reward。
- 原文方法/输入/监督：训练autoregressive video transformer，视频预测likelihood作为reward；依赖专家视频分布。
- 原文摘要报告的验证：DMC、Atari、RLBench闭环控制及OOD桌面跨具身。
- 阅读者判断/待核细节：likelihood奖励熟悉性与真实任务改进可能不同；摘要未给分解保证。
- 与基础工作的关系：相比PRM4RL转向动态行为密度，相关于在线分布偏移与奖励选择。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

