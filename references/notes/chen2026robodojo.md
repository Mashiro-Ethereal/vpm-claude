# chen2026robodojo

**标题**：RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies

**书目登记**：Tianxing Chen; Yue Chen; Zixuan Li; Junyuan Tang; Kailun Su; Haoran Lu; Weijie Wan; Baijun Chen; Songling Liu; Haowen Yan; Honghao Su; Zhiyang Dou; Kaixuan Wang; Dandan Zhang; Yunze Liu; Yan Qin; Qiwei Liang; Qiwei Wu; Zijian Lin; Wenwei Lin; Yuran Wang; Minghua He; Tianshu Wu; Ruihai Wu; Jingquan Zhou; Kai-Chong Lei; Haibao Yu; Yuanfeng Ji; Weiyang Jin; Guanyu Lin; Xiaofan Li; Qi Xiong; Renjing Xu; Zhongyu Li; Wenhao Chai; Enze Xie; Ziwei Wang; Yao Mu; Hao Dong; Wojciech Matusik; Mingyu Ding; Wenbo Ding; Ping Luo; Masayoshi Tomizuka；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2607.04434)。版本记录：[Submitted on 5 Jul 2026 (v1 ), last revised 8 Jul 2026 (this version, v3)]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：基准过窄/过短且sim与real各自分离。

**原文方法/输入监督**：42sim+18real；泛化/记忆/精度/长程/开放词5维，XPolicyLab统一接口。

## 已读证据

arXiv v3摘要：IsaacSim异构并行、RealEval标准硬件reset/remote、30policy排行榜。

## 边界与基础关联

**边界**：benchmark任务和实际机械臂适配成本要核；不是奖励学习训练集。

**阅读者推断/关联**：强policy评估平台，可用progress与success分指标。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/chen2026robodojo.abs.web.txt`（若首轮批量来源为 `chen2026robodojo.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

