# fu2024furl — FuRL: Visual-Language Models as Fuzzy Rewards for Reinforcement Learning

阅读日期：2026-10-06。书目年份/venue：2024；ICML 2024（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2406.00645)；[书目正式版本](https://raw.githubusercontent.com/mlresearch/v235/main/assets/fu24j/fu24j.pdf)。版本：[Submitted on 2 Jun 2024 ( ), last revised 5 Jun 2024 (this version, v2)]。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/fu2024furl.web.txt](_sources/fu2024furl.web.txt)。

- 原文问题：轻量微调VLM reward对齐，relay RL避local minima。
- 原文方法/输入/监督：预定义language稀疏task，微调VLM representation+SAC/DrQ baseline。
- 原文摘要报告的验证：MetaWorld多任务闭环RL对照。
- 阅读者判断/待核细节：依赖sparse task signal及relay strategy，具体label规则需正文。
- 与基础工作的关系：reward misalignment与online adaptation已有，问题应更具体。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

