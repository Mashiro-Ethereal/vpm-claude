# sun2024card

## 选择性精读：离线筛选与证据（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2410.14660v1)，实际读§4、§5.1–5.6；保存 full.web.txt 与 full_part2.web.txt。

**原文方法。** 自动反馈含学习过程统计、最佳/最差轨迹状态与子奖励、轨迹偏好。TPE比较成功和失败旧轨迹的平均折扣逐步奖励，实践排序准确率阈值0.8；初轮必须训练，此后不通过就反馈修改并跳过RL。其“无ground-truth reward”仍需要成功标记，不能表述为无监督。

**实验。** MetaWorld/ManiSkill2各6任务，统一GPT-4-1106-preview与PPO/SAC，5seed，通常2轮修改。Table2平均token：CARD14181.7、Eureka662882.5；后者初轮加5轮×16=96调用，前者3调用，token统计各仅一搜索运行。§5.4去除三类反馈均降低表现，额外迭代也可能降低表现。

**阅读者推断。** 离线轨迹排序减少重训已经被覆盖，但该排序是旧分布上的合理性检查，没有对大量候选预测最后效用的独立测试。完整折扣PBRS回报的边界项若固定，轨迹排序不能区分势函数；CARD的平均归一化/不同轨迹长度可能破坏这一不变性，必须具体计算，不能笼统声称所有CARD信号必然相同。

**标题**：CARD: A Large Language Model-Driven Reward Design Framework via Dynamic Feedback for Reinforcement Learning

**书目登记**：Shengjie Sun; Runze Liu; Jiafei Lyu; Jing-Wen Yang; Liangpeng Zhang; Xiu Li；2025；Knowledge-Based Systems (2025), article 114065。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2410.14660)。版本记录：[Submitted on 18 Oct 2024]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：代码生成多次重训/人工反馈使设计贵。

**原文方法/输入监督**：Coder/Evaluator动态process/trajectory反馈；TPE比较轨迹偏好，失败先修订而不每次RL。

## 初筛记录：摘要证据

arXiv摘要：MetaWorld/ManiSkill2 12任务中10与专家相当/更好，3超过oracle。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：读到的是2024v1；Knowledge-Based Systems2025版本尚未核差异。

**阅读者推断/关联**：直接覆盖训练前离线候选筛选；应进一步问代理评价何时预测真实学习。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/sun2024card.abs.web.txt`（若首轮批量来源为 `sun2024card.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
