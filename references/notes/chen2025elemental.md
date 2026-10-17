# chen2025elemental

**标题**：ELEMENTAL: Interactive Learning from Demonstrations and Vision-Language Models for Reward Design in Robotics

**书目登记**：Letian Chen; Nina Marie Moorman; Matthew Craig Gombolay；2025；ICML 2025 / PMLR 267。

**实际读取来源**：[原始来源](https://proceedings.mlr.press/v267/chen25at.html)。版本记录：原始来源见保存片段；正式版本状态按来源确认，不从书目标题推断。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：文本不足表达机器人意图；LLM难以正确平衡特征权重。

**原文方法/输入监督**：自然语言+视觉用户示范，VLM构建特征/奖励，IRL估计权重，自反思迭代反馈。

## 已读证据

ICML正式摘要报成功提升42.3%、OOD泛化提升41.3%。

## 边界与基础关联

**边界**：有视觉示范监督；数字为摘要作者报告，训练器与OOD变更需全文核对。

**阅读者推断/关联**：视觉特征生成+权重学习+反馈循环已有强近邻。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/chen2025elemental.abs.web.txt`（若首轮批量来源为 `chen2025elemental.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

