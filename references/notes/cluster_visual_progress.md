# 视觉、进度与过程奖励文献主题综合

研究日期：2026-10-06。本文件综合 `corpus_visual_progress.csv` 的 **54 条文献**，不预设研究方向，不把文献中的“value”“advantage”名称视作已成立的数学对象。事实来自公开原始摘要或正文；下文明确区分原文证据与阅读者推断。两篇基础工作见 [已有工作综合](../../docs/exploration/01_existing_work_synthesis.md)。

## 阅读范围与来源

54/54 条均实际读取了可得的完整原始摘要，并保存 54 个逐篇笔记及摘要来源记录。52 条使用 arXiv 原始摘要；VIRL 使用作者项目/PMLR 摘要；GTCC 使用 CVF 官方搜索返回的摘要（官方页直接请求 403）。VIRL 的 OpenReview 页面遇浏览器验证，作者页中的无关 Nerfies 模板文字没有作为论文证据。无条目仅凭题目判断，也没有因页面障碍断言论文不存在。

选择性正文精读 **30/54 条**，覆盖主要方法、奖励/监督构造、关键实验及影响判断的附录，具体范围逐篇注明；并不声称完整阅读这 30 篇所有附录与图像。30 份 arXiv HTML 原文和抽取保存在 `_sources/<key>.full.html` / `.full.reading.txt`。定位使用节、表、公式；没有冒称这些 HTML 对应的本地 PDF 页码通过 ARS preflight。初筛后新补读的范围在各笔记末尾“选择性正文精读更新”中记录。

精读名单：VIP、LIV、XIRL、Rank2Reward、PROGRESSOR、ReWiND、REDS、VICtoR、SARM、SARM2、Robo-Dopamine、RARM、ProcVLM、ProgressCompass、ARM、DenseReward、Dream2Reward、Robometer、RoboReward、TimeRewarder、VLAC、RynnValue、Agentic Reward System、SOLE-R1、R²VLM、GVL、DINO 奖励模型、TOPReward、ViVa、DecisionNCE。

其余 24 篇保持**摘要初筛**：TCC、VIPER、RoboCLIP、VLM-RM、VLC、LOReL、GraphIRL、VIRL、GTCC、RL-VLM-F、UPR、TCN、HOLD、Diffusion Reward、DVD、PRIMO、LRM、IRR、ProgressLM、TARL、TRACT、RoboFuME、FuRL、VLARL。它们的具体训练实现和摘要数字没有被本综合当作核对过的实验事实。没有新增书目或改动原始 CSV。正文版本按核验到的原文链接记录，包括 ProcVLM v2、RARM v4、SARM v4、RynnValue v2、Dream2Reward v1、ProgressCompass v1、DenseReward v1。

## 从原文得到的主题关系

| 主题 | 已有实质覆盖 | 关键监督/部署条件 |
|---|---|---|
| 视频时间与隐式价值 | VIP/LIV 从被动视频的时间结构学习目标距离；TimeRewarder/RynnValue 预测有符号时间差或剩余时间 | 专家轨迹时间与目标完成的对应关系；cutoff/阶段标注；人类时间结构向机器人转移 |
| 跨具身与任务对齐 | XIRL/TCC 跨视频 cycle alignment；DecisionNCE 用语言匹配偏好及转移方向 | 同任务语义对应、匹配指令；并非任意动力学下可达性证明 |
| 阶段与程序结构 | VICtoR、REDS、SARM/SARM2、Dopamine、ProcVLM | 阶段/动作原语、人类或 VLM 标签；物体状态、剩余步骤、局部视觉变化 |
| 历史与长程上下文 | ReWiND、Robometer、ARM、R²VLM、SOLE-R1、ProgressCompass | 因果窗口、首帧锚点、文本状态记忆、重复计数；不同方法压缩历史的方式不同 |
| 失败、回退、恢复 | Rank2Reward/PROGRESSOR 在线分布校正；ReWiND/TimeRewarder 反序监督；DenseReward 物理失败合成；Dream2Reward 成功转移场；Robometer 混合质量数据 | 真实失败、逆序近似、仿真扰动、成功正例提供的证据不同，不能视作相等的负例预算 |
| 预测未来与方向 | DecisionNCE-T 语言对齐转移方向；RARM 视频方向/参考匹配；Dream2Reward 预测成功潜在转移；ViVa 预测未来 proprioception 辅助 value | 局部方向、预期位移、未来身体状态与动作条件完成价值是不同目标 |
| 奖励到行为的验证 | GVL、ReWiND、RoboReward、SARM/SARM2、Robometer、Dopamine、RARM、DenseReward、ViVa、RynnValue、SOLE-R1 | 加权 BC、离线 critic、模拟在线 RL、真实在线 RL、是否保留真实成功信号必须分别说明 |

这是一组交叉主题，不能用“传统单帧进度”概括全部近邻。2026 年的方法已同时覆盖历史、非单调变化、终端判定、真实机器人和策略优化；新工作必须说明具体新增的预测对象、信息条件或优化性质。

## 最接近工作的实质差异

**基础 PRM4RL 的可继承性。** 它由 LLM 生成状态程序、阶段语言先验和固定势塑形，实验主要是可读状态仿真任务。视觉近邻的不同点主要在势/分数如何从观察与训练数据得到，以及成功信号如何获得。Dopamine 和 RynnValue 已使用视觉势与 `γΦ′−Φ`；RynnValue Appendix E.5 明确终端下一势为零和 action chunk 的折扣换算。将 PRM4RL 换成视觉编码器再加 PBRS，本身不构成新的研究问题。[Dopamine](tan2026dopamine.md)、[RynnValue](huang2026rynnvalue.md)

**程序结构不是空白。** ProcVLM 从约 400K 轨迹/60M 帧标注阶段、剩余原子动作与视觉变化，训练 future planning 和进度头；RoboFAC 实验包含真正失败定位和成功判断。SARM2 将 task-specific 阶段扩展为 21 动作原语及 MoE，目标是 normalized remaining steps，并用真实 on-policy loop 改善长程任务。VICtoR 与 REDS 更早已分解阶段/动作、提供视觉奖励并进行策略学习。[ProcVLM](feng2026procvlm.md)、[SARM2](chen2026sarm2.md)、[VICtoR](hung2025victor.md)、[REDS](kim2025reds.md)

**历史与验证不是空白。** ProgressCompass 在 24 任务/120 视频中分析 state recall、顺序追踪、重复消歧，维护 verified memory 和预期转移，冻结 Robometer 的进度 MAE 从 25.4 降至 9.3。其理论下界限定 current-frame estimator，历史模型仍困难来自实证；没有闭环 RL。R²VLM 已 recurrent CoT 动态修订步骤并在 AI2-THOR 中做在线 IQL。Agentic Reward System 可用后续帧回溯验证早期抓取，是真正的非因果离线监督系统，作者明确因果在线扩展尚未验证。[ProgressCompass](zhang2026progresscompass.md)、[R²VLM](zhang2026r2vlm.md)、[Agentic Reward System](hu2026ars.md)

**方向和恢复不是空白。** DecisionNCE-T 在 2024 年已用潜在转移方向对齐语言。Dream2Reward 以四帧历史预测成功潜在位移，结合有符号方向与幅度，正文 Fig.5 显示抓空后恢复奖励再升；不用失败标签训练。DenseReward 明确物理合成碰撞/抓空/掉落/恢复。RARM 以 confidence-gated 新最大进度奖励过滤失败/停滞，低置信时保持旧进度，其单调机制不意味着无法在恢复后前进。ARM 的三态监督也直接标记进步/停滞/回退。[DecisionNCE](li2024decisionnce.md)、[Dream2Reward](zhang2026dream2reward.md)、[DenseReward](fang2026densereward.md)、[RARM](yang2026rarm.md)、[ARM](mao2026arm.md)

**“value/advantage”的实际含义要看目标。** VIP 的理想分析对应专家最短到达路径的折扣时间；实际 embedding 不自动等于当前机器人策略价值。RynnValue 标签是截止时间距离；SARM2 是归一化剩余步数；GVL 定义 task progress，并把差分称 advantage。ARM 三态进度变化也不是 `Qπ(s,a)−Vπ(s)`。ViVa 则用成功/失败 outcome 构造剩余时间加失败惩罚的 cost-return，并预测未来 proprioception。把这些称为同一种价值会掩盖监督意义，但仅把新模型改称“真正价值”也不足以成立新颖性；DDL/RCE 等相关理论与算法由主智能体另外核对。

## 实验能支持什么

以下是核对过原文实验条件的五组强证据，数字只在各自实验内比较。

1. **静态奖励准确度与策略效果已有人检验。** RoboReward §3/Fig.3 在 Robomimic Lift/Can/Square 上比较同架构训练 checkpoint 与 base model：held-out MAE 与 DSRL 最终表现相关 `r=0.83`；真实两任务 20 次评估中 RR8B 与 Gemini 的排序也一致。这支持其受控设置中的关联，并不证明跨任务、跨策略、任意指标必然成立。[原文](https://arxiv.org/html/2601.00675v2)、[笔记](lee2026roboreward.md)
2. **成功示范排序一个指标可以与策略效果脱节。** ReWiND Table 2 加 full positional embeddings 的 unseen-demo `ρ=.85`，高于主模型 `.79`；Table 3 对应 policy success 相对主模型仅 `.69`。主模型也通过 rollout ranking、rewind 消融和真实 RL 检验奖励，不能描述为无人做闭环分析。[原文](https://arxiv.org/html/2505.10911v2)、[笔记](zhang2025rewind.md)
3. **成功正例训练已能显示局部失败/恢复。** Dream2Reward Table I：400 真实轨迹（234 成功/166 失败）AUC `.95`，Robometer `.93`，Dopamine `.41`；真实四任务离线 RL 为 `69/200=34.5%`，Robometer `28%`、Dopamine `22.5%`、BC `17%`。模拟在线只两项 LIBERO 任务，Dopamine 直接 progress 作为 standardized reward，Robometer 借原论文结果；不能把它说成各方法完整系统的等预算全面优胜。[原文](https://arxiv.org/html/2608.18787v1)、[笔记](zhang2026dream2reward.md)
4. **失败合成与历史已有真实在线效用。** DenseReward Tables 3/4：去失败数据 MAE `.0809→.1312`，0/1/2/3 历史帧 `.096/.088/.081/.086`；真实 DSRL 两任务 `40→80%` 和 `30→70%`，每策略只有 10 次评估。真实成功终止和仿真 PPO 的成功奖励保留，MPC 指标只是末端到物体距离。它支持特定任务和预算中的收益，不能支持无成功监督或普适可达性。[原文](https://arxiv.org/html/2607.13033v1)、[笔记](fang2026densereward.md)
5. **更自主的闭环设置亦有近邻。** SOLE-R1 §5.3 明确不使用外部真实 reward/success label、目标任务 demo 或 task-specific tuning，在四仿真套件及真实设置共 40 项任务测试从零在线 RL，24 项达到至少 50% 成功。Robometer 则用 learned success 自动终止/阶段推进并在真实 DSRL 提升表现；Dopamine 用进度阈值替代 success，PBRS 理论保持的是这一估计基底奖励，不能因此证明真实成功最优。去外部 success 不是可直接声称的新贡献。[SOLE-R1原文](https://arxiv.org/html/2603.28730v2)、[Robometer笔记](liang2026robometer.md)、[Dopamine笔记](tan2026dopamine.md)

现实预算对照还包括：ProcVLM 实际机器人实验是 50 demo 的离线优势条件 RFT，12 次评估且部分 nesting 算半成功；SARM 主要是 200 小时示范上的加权 BC；SARM2 初次需约 100 弱策略 rollout 人工适应；RARM 真实比较 30/60/90 training rollout、各 30 eval；RynnValue 四任务每 60 online rollout、各 20 eval、全程真人成功判定；Agentic Reward System 是 2,574 demo+3,092 offline rollout、单训练 seed、200 eval。这些结果不能横向按成功率排名。

## 可继续检验的问题：阅读者推断

**标签语义跨行为分布是否稳定。** 成功示范时间、程序完成百分比、局部有符号转移和策略条件成功概率可对同一状态给出不同排序。已有文献已解决一部分时序噪声、失败高估和多阶段泛化；仍可将问题具体化为：在同任务、替代成功路径、必要短期回退和探索策略之间，哪个标签/势预测的排序保持，哪一个有助于固定内层算法的有限预算提升？这里的贡献须是可观测的条件与机制，不能只提“加入分支/恢复”或“value 替 progress”。

**离线评估对闭环优化的预测条件。** 现有正关联（RoboReward/GVL）与局部反例（ReWiND 的 full-PE）可共存。更明确的问题是：在固定策略先验、终止判据、奖励缩放、训练预算及采样分布下，什么 transition/event 级误差影响学习而成功示范 VOC/MAE 没有反映？需要实际 policy rollouts 与 optimizer 压力测试；只做一套静态 benchmark 或计算新相关系数不够。ViVa 已有 milestone/error sensitivity，Dream2Reward 已有 reward flatness/failure-separation、Robometer 已有失败检测，因而指标设计需超出这些已有覆盖。

GVL Table 3 的具体证据是：banana-handover 的平均 VOC `.73`，GVL+DP `7/10`、DP `5/10`；bowl-in-rack VOC `.57`，`7/10` 对 `6/10`；open-drawer VOC `.09`，`4/10` 对 `6/10`；remove-gears VOC `.19`，`4.67/10` 对 `7/10`；fold-dress VOC `.66`，两者均 `7/10`。这是同一 GVL 方法跨七真实任务的 AWR/DP 实验，作者称 VOC 与改善关联；表中有分数型结果，不应一律解释为整数成功次数，也没有给出 RoboReward 式 `r=.83` 统计。它与 ReWiND 的消融一起，适合动机化“有条件预测优化效用”，而不能支持简单地否定 VOC。若候选是预测给定 reward family/learner/初始化/训练预算的实际效用，新贡献需要跨 family、task、learner 持出验证，并在同总预算下比较静态指标、短训练以及 ORSO/LaRes 等选择方法；本组没有读取后两者，交由对应代理/主智能体综合。[GVL原文](https://arxiv.org/html/2411.04549v1)、[GVL笔记](ma2025gvl.md)

**因果信息预算与可辨识性。** 长历史已被 ProgressCompass/R²VLM 处理，离线未来证据已被 Agentic Reward System 使用，ViVa/Dream2Reward 已预测未来。可问的是：当前图像/有限历史/首帧/任务记忆/腕相机/关节状态和动作，分别能解除哪些具体歧义，剩下哪些物理状态在视觉显现前仍不可判？这应以控制信息预算的成对执行验证，而不是宣称图像能够凭空辨识隐藏接触。用户没有 force/torque/tactile，因此方案应使用现有 RGB、proprio、腕相机与可控交互；需要新增传感器的方向不是默认可执行。

**结构奖励如何接受行为校正。** PRM4RL 提供阶段与势函数表达，RF-Agent 提供用行为反馈修订奖励的经验；Rank2Reward/PROGRESSOR/REDS/SARM2 已在线校正 reward-distribution。若延伸这条路线，实质问题应限定为如何以少量、独立的行为证据校正特定结构错误并保留已有约束，以及是否减少标注或内层训练成本。简单叠加搜索、self-verification 或在视觉模型外套程序不能推为新增问题。

这些是后续实验假设，不是文献已证明的普遍失败，也不是本代理替用户选定的研究方向。主智能体应与另两组文献及 DDL/RCE/LIRF 的证据合并后收敛。

## 局限与资源含义

本综述是定向两轮阅读，24 篇仅摘要、30 篇选择性正文，没有声称全数据库系统检索或所有最新版附件都逐页精读。最新 arXiv 结果属于作者报告，未复现。跨论文的 pretrained policy、外部成功判据、teacher 特权信息、机器人平台和评估样本差异很大；理论讨论区分固定势/终止条件和样本学习效果，不据简略正文推断实现错误。

8×A100 80G 足以支持复用现有 2B–8B 奖励模型、有限参数适应和多种 reward/inner-policy 消融；ProcVLM 20B+2.8B tokens、Dopamine 35M samples、Robometer 1M trajectories、RynnValue 7,000h 等全规模预训练是否适合本项目时间预算尚未确定。现有真实机械臂、固定相机/关节状态和可配腕相机适合先做成对短执行及有限 rollout 闭环验证；不能默认论文中的双臂长程、200h示范或多机器人并行预算已具备。机器人型号、可用时间和第一轮期限由用户后续决定。
