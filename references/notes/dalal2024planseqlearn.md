# dalal2024planseqlearn

**标题**：Plan-Seq-Learn: Language Model Guided RL for Solving Long Horizon Robotics Tasks

**书目登记**：Murtaza Dalal; Tarun Chiruvolu; Devendra Singh Chaplot; Ruslan Salakhutdinov；2024；ICLR 2024。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2405.01534)。版本记录：[Submitted on 2 May 2024]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：高层LLM计划依赖预定义技能，无法回答技能如何从头学会。

**原文方法/输入监督**：PSL模块化结合LLM规划、运动规划与低层RL，运动规划跨接抽象语言与控制。

## 已读证据

摘要：超过25任务、最多10阶段、4基准，原始视觉长程任务>85%成功。

## 边界与基础关联

**边界**：模型规划/运动规划接口也是先验；不能把85%与其他不同基准直接比较。

**阅读者推断/关联**：挑战只有进度奖励才能连接高层规划与低层学习的主张。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/dalal2024planseqlearn.abs.web.txt`（若首轮批量来源为 `dalal2024planseqlearn.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

