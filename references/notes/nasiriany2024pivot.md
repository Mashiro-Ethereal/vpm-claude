# nasiriany2024pivot

**标题**：PIVOT: Iterative Visual Prompting Elicits Actionable Knowledge for VLMs

**书目登记**：Soroush Nasiriany; Fei Xia; Wenhao Yu; Ted Xiao; Jacky Liang; Ishita Dasgupta; Annie Xie; Danny Driess; Ayzaan Wahid; Zhuo Xu; Quan Vuong; Tingnan Zhang; Tsang-Wei Edward Lee; Kuang-Huei Lee; Peng Xu; Sean Kirmani; Yuke Zhu; Andy Zeng; Karol Hausman; Nicolas Heess; Chelsea Finn; Sergey Levine; Brian Ichter；2024；ICML 2024; PMLR 235:37321–37341。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2402.07872)。版本记录：[Submitted on 12 Feb 2024]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：文本VLM难输出连续空间控制。

**原文方法/输入监督**：图上标候选动作/位置/轨迹，VLM选择再迭代精细化。

## 已读证据

摘要：真实导航/操作、模拟instructions，无robottrainingdata零样本控制。

## 边界与基础关联

**边界**：依赖候选生成与动作接口，表现并不完善。

**阅读者推断/关联**：VLM视觉空间推理/优化是reward-free反证。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/nasiriany2024pivot.abs.web.txt`（若首轮批量来源为 `nasiriany2024pivot.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

