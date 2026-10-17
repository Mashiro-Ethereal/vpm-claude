# lu2025vlarl — VLA-RL: Towards Masterful and General Robotic Manipulation with Scalable Reinforcement Learning

阅读日期：2026-10-06。书目年份/venue：2025；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2505.18719)；[书目正式版本](https://arxiv.org/pdf/2505.18719)。版本：[Submitted on 24 May 2025]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/lu2025vlarl.web.txt](_sources/lu2025vlarl.web.txt)。

- 原文问题：online RL提升预训练autoregressive VLA。
- 原文方法/输入/监督：轨迹multi-turn formulation；自动task segments的pseudo reward训练process model，curriculum/GPU vectorization等。
- 原文摘要报告的验证：OpenVLA7B在LIBERO40tasks比强finetune baseline高4.5%。
- 阅读者判断/待核细节：segment pseudo label和初始化policy是预算；不是从零只靠新reward学。
- 与基础工作的关系：自动分段process supervision+VLA-RL已覆盖直接pipeline扩展。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

