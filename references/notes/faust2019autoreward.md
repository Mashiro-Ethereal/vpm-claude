# faust2019autoreward

**标题**：Evolving Rewards to Automate Reinforcement Learning

**书目登记**：Aleksandra Faust; Anthony Francis; Dar Mehta；2019；AutoML@ICML 2019 workshop。

**实际读取来源**：[原始来源](https://arxiv.org/abs/1905.07628)。版本记录：[Submitted on 18 May 2019]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：原始简单目标直接奖励导致控制效果差。

**原文方法/输入监督**：AutoRL把reward tuning当hyperparam优化，种群完整训练选任务objective高者。

## 已读证据

2019 AutoML@ICML摘要：4MuJoCo任务×2RL算法，复杂任务改善更大。

## 边界与基础关联

**边界**：参数化奖励族、重复RL；非LLM语义/结构生成。

**阅读者推断/关联**：奖励外层双层优化本身早已有，不作为新理论。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/faust2019autoreward.abs.web.txt`（若首轮批量来源为 `faust2019autoreward.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

