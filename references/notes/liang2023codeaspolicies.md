# liang2023codeaspolicies

**标题**：Code as Policies: Language Model Programs for Embodied Control

**书目登记**：Jacky Liang; Wenlong Huang; Fei Xia; Peng Xu; Karol Hausman; Brian Ichter; Pete Florence; Andy Zeng；2023；ICRA 2023。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2209.07753)。版本记录：[Submitted on 16 Sep 2022 (v1 ), last revised 25 May 2023 (this version, v4)]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：语言命令无法直接映射精确运动API。

**原文方法/输入监督**：few-shotcodeexamples+递归codegen，处理detector输出与controlprimitiveAPI。

## 已读证据

摘要：多个真实平台、reactive/waypoint控制；HumanEval39.8%不是机器人成功率。

## 边界与基础关联

**边界**：人工示例/API/primitive重要，不是无接口先验控制。

**阅读者推断/关联**：可执行程序接口并不特指奖励，必须与程序policy比较。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/liang2023codeaspolicies.abs.web.txt`（若首轮批量来源为 `liang2023codeaspolicies.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

