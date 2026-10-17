# zeng2024selfalign

**标题**：Learning Reward for Robot Skills Using Large Language Models via Self-Alignment

**书目登记**：Yuwei Zeng; Yao Mu; Lin Shao；2024；ICML 2024 / PMLR 235。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2405.07162)。版本记录：[Submitted on 12 May 2024 (v1 ), last revised 16 May 2024 (this version, v3)]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：LLM提出的奖励不精准，需要用环境行为落地。

**原文方法/输入监督**：先生成特征和参数化，用执行轨迹排序一致性自对齐参数。

## 已读证据

摘要：2模拟环境9任务，改善训练效果效率，较mutation方案少GPT tokens。

## 边界与基础关联

**边界**：LLM排序仍是监督先验；不是单凭自然语言证明正确奖励。

**阅读者推断/关联**：参数学习/行为排序自对齐先于简单代码重写。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/zeng2024selfalign.abs.web.txt`（若首轮批量来源为 `zeng2024selfalign.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

