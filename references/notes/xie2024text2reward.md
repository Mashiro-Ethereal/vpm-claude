# xie2024text2reward

## 选择性精读：反馈与实际部署（第二轮）
来源：[arXiv v3](https://arxiv.org/html/2309.11489v3)，实际读§2.2–4.1；保存 deep.web.txt。
**方法/条件。** 状态和点云接口文字化，自由奖励程序，可检索其他任务例子，执行错误纠正；用户根据视频和曲线提语言修订。超参先对专家奖励调好再用于生成奖励。L2R基线被改为RL而非原MPC，需区分比较版本。
**证据。** Fig2/3五seed，17操作13相当专家；Table1六运动任务各100rollout作者共识视频判定94–100%，不是额外独立人评。两真实Franka任务Fig5展示帧/视频，SAM+depth估计状态，少量校准/随机噪声；未提供此正文片段中的正式实机统计。Stack3程序×2轮反馈；Ant躺向歧义通过反馈修正。
**关联。** 交互修订和sim2real程序奖励不是RF之后才有；但没有系统在线选择/效用预测。

**标题**：Text2Reward: Reward Shaping with Language Models for Reinforcement Learning

**书目登记**：Tianbao Xie; Siheng Zhao; Chen Henry Wu; Yitao Liu; Qian Luo; Victor Zhong; Yanchao Yang; Tao Yu；2024；ICLR 2024。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2309.11489)。版本记录：[Submitted on 20 Sep 2023 (v1 ), last revised 25 May 2024 (this version, v3)]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：奖励编写需要领域经验；用语言目标替代手工奖励。

**原文方法/输入监督**：紧凑环境表示落地自由形式稠密奖励程序，并接受人类反馈修订。

## 初筛记录：摘要证据

摘要：ManiSkill2/MetaWorld 17个操作任务中13个与专家相当或更好；另6个运动行为成功率>94%，并展示真实部署。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：环境接口、包及人类反馈仍是条件；摘要未核对真实部署细节。

**阅读者推断/关联**：RF-Agent/PRM4RL的直接早期基线；程序奖励、人类修订和真实部署不是新的总类贡献。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/xie2024text2reward.abs.web.txt`（若首轮批量来源为 `xie2024text2reward.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
