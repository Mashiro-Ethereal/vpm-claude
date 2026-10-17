# chen2020cheating

**标题**：Learning by Cheating

**书目登记**：Dian Chen; Brady Zhou; Vladlen Koltun; Philipp Krähenbühl；2020；CoRL 2019 / PMLR 100。

**实际读取来源**：[原始来源](https://arxiv.org/abs/1912.12294)。版本记录：[Submitted on 27 Dec 2019]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：视觉驾驶同时学感知与控制难。

**原文方法/输入监督**：先用真实layout/交通参与者特权信息训练teacher，再教vision sensorimotor agent。

## 已读证据

CoRL2019摘要：CARLA100%，NoCrash改善、违规频率数量级下降。

## 边界与基础关联

**边界**：仿真驾驶、先验teacher；数字不与操作任务比。

**阅读者推断/关联**：“状态知识转视觉策略”训练脚手架已有反证。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/chen2020cheating.abs.web.txt`（若首轮批量来源为 `chen2020cheating.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

