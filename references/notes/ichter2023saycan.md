# ichter2023saycan

**标题**：Do As I Can, Not As I Say: Grounding Language in Robotic Affordances

**书目登记**：Brian Ichter; Anthony Brohan; Yevgen Chebotar; Chelsea Finn; Karol Hausman; Alexander Herzog; Daniel Ho; Julian Ibarz; Alex Irpan; Eric Jang; Ryan Julian; Dmitry Kalashnikov; Sergey Levine; Yao Lu; Carolina Parada; Kanishka Rao; Pierre Sermanet; Alexander T Toshev; Vincent Vanhoucke; Fei Xia; Ted Xiao; Peng Xu; Mengyuan Yan; Noah Brown; Michael Ahn; Omar Cortes; Nicolas Sievers; Clayton Tan; Sichun Xu; Diego Reyes; Jarek Rettinghouse; Jornell Quiambao; Peter Pastor; Linda Luu; Kuang-Huei Lee; Yuheng Kuang; Sally Jesmonth; Nikhil J. Joshi; Kyle Jeffrey; Rosario Jauregui Ruano; Jasmine Hsu; Keerthana Gopalakrishnan; Byron David; Andy Zeng; Chuyuan Kelly Fu；2023；CoRL 2022; PMLR 205:287–318 (2023)。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2204.01691)。版本记录：[Submitted on 4 Apr 2022 (v1 ), last revised 16 Aug 2022 (this version, v2)]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：语言计划不保证该机器人此时能做。

**原文方法/输入监督**：pretrainedskills的valuefunctions给affordance，语言model给语义相关性，联合选择skill。

## 已读证据

arXiv v2摘要：真实mobilemanipulator长程开放语言指令。

## 边界与基础关联

**边界**：预训练skill库提供执行；不是LLM从头低层训练。

**阅读者推断/关联**：任务可行性/语义匹配两证据来源，是progress选择反证。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/ichter2023saycan.abs.web.txt`（若首轮批量来源为 `ichter2023saycan.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

