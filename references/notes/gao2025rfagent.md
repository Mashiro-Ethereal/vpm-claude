# gao2025rfagent

**标题**：RF-Agent: Automated Reward Function Design via Language Agent Tree Search

**书目登记**：Ning Gao; Xiuhui Zhang; Xingyu Jiang; Mukang You; Mohan Zhang; Yue Deng；2025；NeurIPS 2025。

**实际读取来源**：[原始来源](../own_papers/RF_Agent.pdf)。版本记录：用户提供的NeurIPS2025正式PDF；已完整精读。

阅读日期：2026-10-06。范围：**本地完整全文精读**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：基于单路径/群体的奖励搜索未充分利用历史。

**原文方法/输入监督**：MCTS保留代码、思路、训练分数/反馈，五动作使用父节点、祖先和跨路径信息。

## 已读证据

本地全文及附录精读：等80/512预算；归一化1.70/2.68；更多token、平均9h/40h。

## 边界与基础关联

**边界**：没有视觉/真机实验，不减少反复RL训练，self-verify不是物理语义证明。

**阅读者推断/关联**：见基础独立笔记base_rf_agent.md。

基础原文阅读和来源抽取见 [base_rf_agent.md](base_rf_agent.md)。
