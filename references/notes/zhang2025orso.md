# zhang2025orso

## 选择性精读：方法、理论与预算（第二轮）
来源：[arXiv v3正文](https://arxiv.org/html/2410.13837v3)，实际读§3–5、§7.1、附录F；保存 full.web.txt、full_part2.web.txt、deep_part3.web.txt。

**原文方法。** 每个候选保持自己的策略状态，选中才推进训练，再用独立任务奖励评价；D³RB平衡各学习器的遗憾。理论Assumption 4.2要求某学习器所有时刻累计期望回报都占优且平均期望回报单调增加，故不是任意交叉学习曲线的保证。主实验还在某候选达到基准训练长度后保留最好并重采样候选集；大集合Ant实验明确不重采样。

**核对实验。** 六个IsaacGym任务，PPO；K=4/8/16，交互预算5/10/15倍基准n_iters；每次推进n_iters/100。Fig2最高预算较均匀训练候选提高56%任务分数。Fig3最多节省8倍GPU是按PPO迭代时间估算的达到人类水平时间，非实测总运行加速。Ant另测48/96候选、5seed（Fig6/Table3）。研究已直接覆盖有限训练预算下候选选择；依赖独立真实任务评价，未建立离线语义/梯度诊断对完整训练效用的持出校准。

**标题**：ORSO: Accelerating Reward Design via Online Reward Selection and Policy Optimization

**书目登记**：Chen Bo Calvin Zhang; Zhang-Wei Hong; Aldo Pacchiano; Pulkit Agrawal；2025；arXiv; ICLR 2025 author-reported。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2410.13837)。版本记录：[Submitted on 17 Oct 2024 (v1 ), last revised 25 Feb 2025 (this version, v3)]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：在多个shaping奖励中挑好者过度依赖完整重训。

**原文方法/输入监督**：把online reward selection和policy optimization联合，在线model selection并有regret分析。

## 初筛记录：摘要证据

arXiv v3摘要：最多8倍时间降、>50%效果优势，平均近专家。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：理论假设、数据重用/策略继承方式需全文；不是任何新候选生成都具保证。

**阅读者推断/关联**：强挑战单纯更省训练选奖励方向；核心近邻。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/zhang2025orso.abs.web.txt`（若首轮批量来源为 `zhang2025orso.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
