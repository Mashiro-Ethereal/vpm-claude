# pinto2018aac

**标题**：Asymmetric Actor Critic for Image-Based Robot Learning

**书目登记**：Lerrel Pinto; Marcin Andrychowicz; Peter Welinder; Wojciech Zaremba; Pieter Abbeel；2018；Robotics: Science and Systems XIV。

**实际读取来源**：[原始来源](https://www.roboticsproceedings.org/rss14/p08.pdf)。版本记录：原始来源见保存片段；正式版本状态按来源确认，不从书目标题推断。

阅读日期：2026-10-06。范围：**原始PDF摘要、引言、背景/方法入口**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：视觉RL贵，但模拟器有state信息可助训练。

**原文方法/输入监督**：actor看RGBD、critic看state，HER稀疏goal训练+domainrandomization。

## 已读证据

已读RSS PDF摘要/引言/§III：模拟+真实pick/push/block，无真机训练数据。

## 边界与基础关联

**边界**：仅训练使用特权state；一般POMDP下critic输入条件要注意，未全读理论/实验。

**阅读者推断/关联**：state奖励辅助visual策略不是新概念；部署不要求reward也纯视觉。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/pinto2018aac.abs.web.txt`（若首轮批量来源为 `pinto2018aac.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

