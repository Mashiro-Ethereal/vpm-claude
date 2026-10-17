# huang2023innermonologue

**标题**：Inner Monologue: Embodied Reasoning through Planning with Language Models

**书目登记**：Wenlong Huang; Fei Xia; Ted Xiao; Harris Chan; Jacky Liang; Pete Florence; Andy Zeng; Jonathan Tompson; Igor Mordatch; Yevgen Chebotar; Pierre Sermanet; Tomas Jackson; Noah Brown; Linda Luu; Sergey Levine; Karol Hausman; Brian Ichter；2023；CoRL 2022; PMLR 205:1769–1782 (2023)。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2207.05608)。版本记录：[Submitted on 12 Jul 2022]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：LLMembodiedplan须根据自己动作结果修正。

**原文方法/输入监督**：successdetector/scenedescription/humaninteraction转换语言闭环feedback，inner-monologue重新计划。

## 已读证据

摘要：sim/real桌面和真实厨房长程mobile任务，反馈提高完成度。

## 边界与基础关联

**边界**：依赖技能与success/scene工具；未直接解决新低层reward。

**阅读者推断/关联**：失败反馈闭环本身早有，新工作须是新的信号与检验。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/huang2023innermonologue.abs.web.txt`（若首轮批量来源为 `huang2023innermonologue.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

