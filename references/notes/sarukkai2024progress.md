# sarukkai2024progress

## 选择性精读：进度作为表示而非直接奖励（第二轮）
来源：[arXiv v2](https://arxiv.org/html/2410.09187v2)，实际读§4–5、附录A.1–A.7和A.9片段；保存 full*.web.txt 与 progress_appendix.detail.web.txt。

**方法。** LLM从任务、状态接口、按benchmark人工写的几何feature库生成多维进度；启发式离散成bins，稀疏成功奖励加1/√访问次数。不做反馈进化；默认4进度候选，分别PPO训练100M环境样本并选最好。

**实验定位。** 20BiDex任务，Fig2/3平均成功0.59、13/20不低于Eureka。20倍成本指4策略样本vs80候选，各有训练成本，不是每步RL加速。Table1进度直接相加0.45、SimHashCounts0.34；完整版5次重复而两消融单次，是比较精度限制。困难TwoCatchUnderarm另每候选2B样本、4候选，最好成功0.55；总预算应计8B，不能把“每候选2B等于Eureka总量”的文字误读成总预算相同。附录A.2在8MiniGrid任务配NovelD，以达到奖励阈值的样本数测试；A.3库、A.6离散代码已读。

**关联。** “约束进度表示会比自由奖励搜索更省候选”已有强反证，但并不保证不同任务策略/同总预算都胜；结构抽象和探索奖励是两个消融因素。

**标题**：Automated Rewards via LLM-Generated Progress Functions

**书目登记**：Vishnu Sarukkai; Brennan Shacklett; Zander Majercik; Kush Bhatia; Christopher Ré; Kayvon Fatahalian；2024；arXiv / ICLR 2025 submission。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2410.09187)。版本记录：[Submitted on 11 Oct 2024 (v1 ), last revised 25 Oct 2024 (this version, v2)]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：逐候选完整训练使奖励生成的试错昂贵。

**原文方法/输入监督**：LLM程序粗估状态进度，用该低维表示离散状态并给count-based intrinsic reward。

## 初筛记录：摘要证据

摘要：Bi-DexHands比先前最佳方案少20倍奖励样本；直接进度奖励和普通hash计数不足。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：状态语义与任务进度可编程；样本减少不是通用理论节省。

**阅读者推断/关联**：PRM4RL直接近邻，但不是势差进度奖励；进度用于探索表示。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/sarukkai2024progress.abs.web.txt`（若首轮批量来源为 `sarukkai2024progress.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
