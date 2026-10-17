# zhu2026dycotre

**标题**：DyCoT-RE: Chain-of-Thought-enhanced LLM reward engineering with dual-dynamic optimization for reinforcement learning

**书目登记**：Xinning Zhu; Jinxin Du; Longfei Huang; Lunde Chen；2026；Neurocomputing 695, 133945 (2026-09-28)。

**实际读取来源**：[原始来源](https://www.sciencedirect.com/science/article/pii/S0925231226013421)。版本记录：原始来源见保存片段；正式版本状态按来源确认，不从书目标题推断。

阅读日期：2026-10-06。范围：**官方出版商索引摘要与节摘录；全文访问受限**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：静态采样temperature/模型限制奖励搜索适应性。

**原文方法/输入监督**：CoT代码进化+policy entropy调temperature+多LLM动态选用。

## 已读证据

ScienceDirect原始摘要：CartPole/BipedalWalker/Ant/SpaceMining，优于human/nonCoT/single优化。

## 边界与基础关联

**边界**：完整原文受组织访问限制；新环境未知于pretraining只是作者主张。

**阅读者推断/关联**：动态搜索探索与backbone选择已有，当前不同于进度潜函数。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/zhu2026dycotre.abs.web.txt`（若首轮批量来源为 `zhu2026dycotre.web.txt`，见该文件）；ScienceDirect获取补充见 `_sources/search_policy_sciencedirect_original.web.txt`。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

