# Same Trajectory, Contradictory Rewards (ROBORMBENCH): Paraphrase Fragility in Vision Language Reward Models

引用键：jeung2026robormbench。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2609.05401v1)。
- 版本、发表状态与实际范围：arXiv v1 preprint；实际读§3.2–3.3构造/SCR/FR/ME、§4主体表与§4.5 selection实验。书目所列年份：2026；venue：arXiv（除明确写已核验者，书目状态不视为独立确认）。
- WHY：等义任务描述使同轨迹奖励矛盾。。
- HOW：同视频意义保持paraphrases检验跨scoreband冲突；LLMensemblefilter并human210样本校验。
- WHAT：2390realtraj/21673instructionvariants，14embodiment；N20同offlinecandidatepool选择regret与SCR高度相关。
- 假设、监督与输入：progresshuman1–5，paraphrase词汇/语法/goalperspective；排除<5通过variants，score1downsampling。
- 验证依据：11rewardmodels，SCR/selectionregret Pearson.882/Spearman.856；中间score3不计criticalreversal。
- 边界：已证明offline决策相关不等于closedloopRL优化预测；语言意义过滤有17FP等已报告。
- 关联（阅读者推断）：奖励可靠性与选择行为桥梁已近邻；RF-Agent需测试真正优化后排序/预算收益而不只offlinebestofN。
