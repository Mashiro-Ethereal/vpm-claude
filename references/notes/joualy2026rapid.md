# joualy2026rapid

## 选择性精读：奖励稳定与平台收益（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2609.21767v1)，实际读§III–VII；保存 deep.web.txt/rapid_exp.detail.web.txt。

**方法。** 50GPU并行环境与SAC update/data比控制；单请求VLM偏好；固定512图anchor上相邻奖励Pearson≥0.99且均差≤0.025、连续2次才冻结；16×16灰度farthest采样。Gemma3-12B生成偏好，RGB仅奖励、策略用特权状态；停止判断是模型稳定而非奖励正确或最终策略质量保证。

**证据。** 5任务3seed、各1Msteps，TableII同IsaacLab/RTX5090：C1 9.18h/19840调用/86.3%→C5 1.15h/896/98.7%。单请求离线标注准确在Gemma反降70.9→65.1%，但50环境下策略更好；标签准确不足以直接预测学习效用。冻结后15run中11短暂下降最后恢复（§VI-C）。没有真机或OOD，§VII-C明确指出real-only不能拿50并行加速。

**关联。** “GPU并行+降低查询/稳定停止”有近期强工作；label/reward fidelity与训练收益不同提供效用方向具体证据。

**标题**：Scaling Vision-Language Reward Learning for Robot Manipulation in Parallel Simulation

**书目登记**：Lobna Joualy; Eric Demeester; Nikolaos Tsiogkas；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2609.21767)。版本记录：[Submitted on 18 Sep 2026]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：VLM偏好学习受API顺序请求与串行采样成本限制。

**原文方法/输入监督**：GPU并行rollout、适配策略更新、一次偏好请求、奖励稳定与代表图像采样。

## 初筛记录：摘要证据

摘要：IsaacLab5个Franka任务，9.18h→1.15h，API19840→896，平均成功86.3→98.7%。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：组合系统效果；要核对同预算消融，5模拟任务不能代表通用/真机效果。

**阅读者推断/关联**：视觉奖励成本基线；用户8A100有利于并行但不能忽略标注成本。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/joualy2026rapid.abs.web.txt`（若首轮批量来源为 `joualy2026rapid.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
