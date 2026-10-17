# ARM-FM: Automated Reward Machines via Foundation Models for Compositional Reinforcement Learning

引用键：castanyer2026armfm。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2510.14176v3)。
- 版本、发表状态与实际范围：arXiv v3 2026-03-08，作者record标PublishedICLR2026；OpenReview直连验证码；实际读§2–4、附录A4/A5/A10.1及环境方法片段。书目所列年份：2026；venue：ICLR 2026（除明确写已核验者，书目状态不视为独立确认）。
- WHY：自动组合奖励规范。。
- HOW：FM生成RM、Python labeling与状态语言嵌入；generator/critic迭代可人工修正，策略π(s,z_u)。
- WHAT：MiniGrid/BabyAI/Craftium/MetaWorld改善RL，XLand同域任务组合zero-shot。
- 假设、监督与输入：使用env APIs给事件；3seeds；MetaWorld人工调整reward，UnlockPickup人工补lostkey回退边。
- 验证依据：A10.1有逆向progress边；自动1KRMs correctness为LLMjudge。未读HTML漏出的完整代码图，不能声称已逐行审code。
- 边界：A5无正循环+终奖支配非终奖不足推出discounted sparse最优或PBRS。γ=.9，直接1 vs .2再1的无环分支分别1/1.1，原稀疏则1/.9，假设均满足（阅读者反例）。
- 关联（阅读者推断）：可撤销progress/LLM修RM/语言状态已覆盖；学习弱监督视觉历史义务不同但新颖性尚须证据。
