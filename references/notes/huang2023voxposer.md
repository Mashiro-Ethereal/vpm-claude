# huang2023voxposer

**标题**：VoxPoser: Composable 3D Value Maps for Robotic Manipulation with Language Models

**书目登记**：Wenlong Huang; Chen Wang; Ruohan Zhang; Yunzhu Li; Jiajun Wu; Li Fei-Fei；2023；CoRL 2023; PMLR 229:540–562。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2307.05973)。版本记录：[Submitted on 12 Jul 2023 (v1 ), last revised 2 Nov 2023 (this version, v2)]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：只用predefinedprimitive限制开放指令操作。

**原文方法/输入监督**：LLM+VLM程序组合3Dvaluemap，再model-basedplanning闭环6DoFtrajectory，可在线学contactdynamics。

## 已读证据

摘要：大量模拟/真实日常操作，动态扰动响应。

## 边界与基础关联

**边界**：valuemap是规划cost，非学到RLreward；视觉/规划接口重要。

**阅读者推断/关联**：视觉可执行reward/constraint的新颖性要与value-map planning区分。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/huang2023voxposer.abs.web.txt`（若首轮批量来源为 `huang2023voxposer.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

