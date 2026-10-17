# liu2023libero

**标题**：LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning

**书目登记**：Bo Liu; Yifeng Zhu; Chongkai Gao; Yihao Feng; Qiang Liu; Yuke Zhu; Peter Stone；2023；NeurIPS 2023 Datasets and Benchmarks。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2306.03310)。版本记录：[Submitted on 5 Jun 2023 (v1 ), last revised 14 Oct 2023 (this version, v2)]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：lifelong决策必须迁移程序性技能与知识。

**原文方法/输入监督**：130任务四suite，程序任务生成、高质量teleop，系统学transfer/order/pretraining。

## 已读证据

摘要：顺序fine-tune前向迁移可胜LL方法；无单encoder普遍最佳，naivepretrain可伤效果。

## 边界与基础关联

**边界**：示范监督基准，奖励自探索实验需重新定义数据预算。

**阅读者推断/关联**：可测目标/空间/长程泛化，也提供imitation强基线。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/liu2023libero.abs.web.txt`（若首轮批量来源为 `liu2023libero.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

