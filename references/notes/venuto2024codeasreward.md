# venuto2024codeasreward

**标题**：Code as Reward: Empowering Reinforcement Learning with VLMs

**书目登记**：David Venuto; Mohammad Sami Nur Islam; Martin Klissarov; Doina Precup; Sherry Yang; Ankit Anand；2024；ICML 2024 / PMLR 235:49368–49387。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2402.04764)。版本记录：[Submitted on 7 Feb 2024]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：每步VLM计算奖励慢。

**原文方法/输入监督**：VLM-CaR通过代码生成得到可执行稠密奖励，降低反复视觉模型推理。

## 已读证据

摘要：离散/连续多环境更准确/有效于原始稀疏奖励。

## 边界与基础关联

**边界**：摘要未明确完整视觉到状态变量接口；精度要核标注/任务。

**阅读者推断/关联**：视觉模型知识蒸馏为程序已有，不应泛称首次。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/venuto2024codeasreward.abs.web.txt`（若首轮批量来源为 `venuto2024codeasreward.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

