# zhang2026unexpectedpolicy

**标题**：An Unexpected Robot Policy: Early Evaluations of GPT-6 Astra on RoboDojo and Beyond

**书目登记**：Wenbo Zhang; Kaixuan Wang; Yutao Ouyang; Xiaoyu Huang; Liyang Li; Kailun Su; Weiyang Jin; Wenhao Chai; Haotian Liang; Zhiyang Dou; Yue Chen; Tianxing Chen；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2609.24170)。版本记录：[Submitted on 21 Sep 2026]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：LLM能否不finetune直接做数值动作策略。

**原文方法/输入监督**：GPT-6Astra/GPT5.5/DeepSeekFlash统一postprocessing，42RoboDojo。

## 已读证据

原始摘要：Astra2100试验22.48%success/28.97Score，其他0.88/1.92%；一shot无aggregate收益。

## 边界与基础关联

**边界**：精度、动态、双手弱；progressScore不是success；最新预印本非已审稿结论。

**阅读者推断/关联**：强挑战有些任务无需奖励训练，但也支持低层技能仍必要。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/zhang2026unexpectedpolicy.abs.web.txt`（若首轮批量来源为 `zhang2026unexpectedpolicy.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

