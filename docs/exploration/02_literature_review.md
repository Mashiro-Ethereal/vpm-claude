# 文献综述：LLM 奖励设计、进度势函数与奖励评价

整理日期：2026-10-15。综述形式为 **narrative review**，由用户选定；流程按 ARS `deep-research` 的 `lit-review` 模式执行。本文是 [03_candidate_directions.md](03_candidate_directions.md) 的文献基础，不是论文稿件。检索与核验过程见 [SEARCH_2026-10-15.md](../../references/notes/SEARCH_2026-10-15.md)。

**阅读范围标注**（全文统一）：

- **[基础论文]**：本次会话从本地 PDF 抽取全文，读了正文和主要附录（具体章节见检索记录 §3）。
- **[原文 §x]**：本次读过该来源的原文正文，只引用标出的章节。
- **[精读]**：你指定的 8 篇（Robo-Dopamine、ProcVLM、FLORA、ORSO、LaRes、RoboReward、SARM、DenseReward），本次下载原文通读。阅读范围、逐篇笔记和方法缺陷见 [04_close_reading_8papers.md](04_close_reading_8papers.md)（精读后新增的标注）。
- **[摘要]**：本次只读完整摘要。只依据摘要的条目不评价方法缺陷，也不引用正文数字。
- **[笔记]**：依据项目已有的逐篇笔记（2026-10-06，读到哪些章节以笔记顶部记录为准）。本次只用 arXiv API 核对了标题和编号，没有重读正文。

**预印本**指截至 2026-10-15 没有查到正式出版信息的 arXiv 文章，其中的数字一律视为作者报告。

---

## 要点

1. **在匹配预算的第三方比较中，搜索算法越复杂，结果并不越好。** 两项 2026 年 9–10 月的独立评测都把 RF-Agent 列为基线：BIRD 统一实现了 14 种迭代奖励设计方法，比较了其中 6 种；ARBO 在 128 个候选的预算下比较了 5 种。两者都没有复现 RF-Agent 原文中的稳定领先，见 §2.1。BIRD 还把成本问题明确留作未研究的局限。
2. **评价一个奖励候选，多数方法仍要完整训练一次策略。** 已有的降本思路包括离线筛选、在线选择、共享回放、分叉验证、表示约束和学习曲线外推。但目前没有工作在留出任务、留出学习器、多种奖励家族上，系统检验“低成本信号能预测完整训练效用”，并给出同算力下的节省幅度，见 §2.2。
3. **“不改变最优策略”和“在有限预算内学得快”是两个独立的维度。** 势函数塑形（PBRS）只作用于后者。EPIC、TAC 这类在 PBRS 下不变的指标只能衡量前者。LLM-RLHF 方向的最新理论（Razin 2025；Shang 2026）表明，奖励的有效性取决于它与初始策略和学习算法的相互作用；这套分析尚未迁移到连续控制中由 LLM 写的奖励代码上，见 §2.3。
4. **进度/价值信号分化成两条路线。** 程序化路线（PRM4RL、Video2STL、FLORA、StructRL）解释性强，但依赖状态接口或事件谓词；学习路线（RoboReward、Robometer、Dopamine 2.0、SeeQ、eVTA₀）依赖大规模数据，并受视角和时间顺序理解能力限制。真实传感器下的程序化进度是否可辨识，仍缺少系统研究，见 §2.4。
5. **“分数高”不等于“行为符合意图”。** BIRD 的小规模人类评测显示，在成功取决于接触力、步态这类视频里难以看清的量的任务上，人根据视频做的完成度判定与基准分数的一致性很低（作者推测 VLM 评审会遇到同样的困难）；参考奖励本身也可以被钻空子，见 §2.5。
6. **规模可以部分替代奖励设计。** AlphaNIST 和 SGS（CoRL 2026）表明，在大规模并行仿真加多样化重置的条件下，只用稀疏二值奖励就能学会高难度装配。奖励设计的价值因此需要放在算力受限、无法重置或真实机器人的场景中论证，见 §2.6。

---

## 1. 两篇基础工作：证明了什么，边界在哪里

### 1.1 PRM4RL [基础论文]

**方法。** LLM 一次性生成三样东西：子任务列表、子任务判定函数 Ψ(s)、进度函数 Φ(s)。奖励写成 `R = γΦ(s′) − Φ(s) + I(s′)·r_bonus`（式 3），策略输入中加入当前子任务的 SimCSE 语言嵌入（§4.3）。全流程只调用一次 LLM（§4，“single interaction”），没有反馈修正环节。

**理论。** 定理 4.1 是 Ng 等（1999）的 PBRS 最优策略不变性；推论 4.2 由它直接推出收敛性不受影响。定理 4.3 是 Wiewiora（2003）给出的表格 Q-learning 中“势函数塑形等价于 Q 值初始化”。正文将其解读为“基于先验的价值初始化”，但关于加速的结论实际由实验支撑，而不是由定理保证（§4.2、附录 A.1）。定理陈述没有讨论有限时域、超时截断和终止状态势的处理。

**实验。** MetaWorld 10 个任务、ManiSkill 5 个任务，SB3 的 SAC/PPO，5 个随机种子，GPT-4o（温度 0.7）。基线为 ELLM（用同一个 Ψ 重新实现）、Text2Reward（在 T2R 原文覆盖的任务上直接复用其奖励）和环境自带的专家奖励（§5.1、附录 A.2–A.3）。消融（图 5–6）显示：直接把进度当奖励时，回合奖励上升而成功率下降，这是已经观察到的“优化目标偏离”现象。

**边界（本次阅读确认）。**

- 只在可读状态的仿真中验证。
- Ψ/Φ 的错误不会被任何反馈信号发现。附录 A.6 的 pick-place 示例中，前三个阶段的 `main_progress` 取 `subtask_idx + subprogress`，而最后阶段直接设为 1.0，所以进度在任务完成时从约 3 降到 1。按定理，这不改变最优策略，但会在最后一步产生负的塑形项；它是否影响学习，原文没有检验。
- 跨任务迁移只在 MetaWorld 内部测试（图 7–8）。

### 1.2 RF-Agent [基础论文]

**方法。** 把奖励设计写成外层序列决策问题，用 MCTS 管理奖励代码树。节点保存设计思路、代码、评价分数和训练反馈；扩展动作包括两种变异、与精英节点交叉、路径推理、生成不同思路；选择时用 UCT，其中加入随搜索进程衰减的 LLM 自评分；代码通过编译后，再根据代码重新生成设计思路，即 thought alignment（§4.2）。

**预算与协议。** IsaacGym 7 个任务，每任务 80 个候选，用 GPT-4o-mini 和 GPT-4o 两种模型；Bi-DexHands 10 个任务，每任务 512 个候选，只用 4o-mini（§5.3）。最终评价换用与搜索阶段不同的 5 个种子，报告各检查点评价值中的最大值（§5.3、附录 C）。整个搜索过程没有重复运行。

**结果与成本。** 表 1 中 IsaacGym 的平均人类归一化分数：4o-mini 下 RF-Agent 1.70、Eureka 0.63、Revolve 0.67；4o 下分别为 2.68、2.00、2.03。在 4 张 RTX 3090 上，每个任务平均耗时 9 小时（IsaacGym）和 40 小时（Bi-DexHands）（附录 C）。prefill token 是基线的 2–3 倍（附录 E，表 4–5）。作者在局限中写明：方法“没有减少多次 RL 训练的需求”，未来工作是“减少 RL 训练次数，同时保持有效的迭代改进”（§6）。

### 1.3 两篇共同提供的基础与共同边界

- **共同基础：** “结构化的奖励表达”（PRM4RL）加上“用策略训练结果修订奖励”（RF-Agent），以及仿真 RL、LLM 生成奖励代码、消融设计方面的工程经验。
- **共同边界：** 都依赖特权状态和仿真器给出的任务度量 F；都没有研究评价成本如何降低、奖励改变了什么（是任务定义还是学习速度）、真实传感器下能否辨识进度。
- 这些判断与项目已有的 [01_existing_work_synthesis.md](01_existing_work_synthesis.md) 一致。本次的补充是 §2.1 的第三方匹配预算证据，以及 §1.1 对理论陈述范围的核对。

---

## 2. 主题综合

### 2.1 迭代奖励设计：从“更强的搜索”到“匹配预算下的比较”

**演进脉络。** 起点是 Eureka（Ma et al., 2024）[笔记] 和 Text2Reward（Xie et al., 2024）[笔记]。此后的工作沿两个方向改进：

- **历史信息的使用和搜索组织：** REvolve [笔记] 用种群进化；RF-Agent 用树搜索；R*（Li et al., ICML 2025）[笔记] 把结构演化与参数对齐分开；MLREF（Liu et al., 2026，预印本）[笔记] 维护持久模块池并做模块信用分配；ARBO（Li, Tan & Wang, 2026，预印本）[原文 §1–3, §5] 让 LLM 智能体在运行时自己制定搜索策略。
- **反馈来源：** CARD [笔记] 用轨迹偏好；RDA（Lee et al., RLC 2026）[笔记] 用 VLM 对视频打分；ORSO、LaRes [精读] 用在线选择和共享回放。

**第三方匹配预算证据。**

- **BIRD（Bhamidipaty et al., 2026，预印本）[原文：正文全部，附录 D、F 全部，附录 G、I.2、I.4 部分]。** 在统一实现下比较了 6 种已发表方法（REvolve、RDA、R*、RF-Agent、Eureka、CARD）。协议是每次搜索 8 个候选 × 5 轮 = 40 次策略训练，每次 1M 环境步，由 claude-opus-5 生成奖励（附录 I.2、I.4）。§4.1 的结论是：REvolve 在各套件上最强（只在 HumanoidBench 上落后于 RDA），“其余方法之间没有哪一个以不重叠的置信区间稳定胜出”。图 7 汇总排名中 RF-Agent 列第 4/8，即已发表的有监督方法中仅次于 REvolve（按图中标签顺序读取）。§4.2 对 30 个设计选择做消融，只有 4 个明确有益：选自身奖励最高的检查点、汇总式反馈、以任务成功为 fitness、四轮历史。由此总结的简单配方 ERA-U/ERA-S 里包含 RF-Agent 的 design thought（表 1）。附录 F 显示，迭代并没有使奖励在 EPIC 距离上靠近参考奖励，EPIC 距离与基准分数也基本无关（MT10 上 Spearman −0.08，MuJoCo 上 +0.08）。附录 D 的局限第三条写明：“we do not study computational efficiency or ways to reduce the cost of IRD”。
- **ARBO [原文 §5.2–5.3、附录 B]。** 用 MiniMax-M2.7、每任务 128 个候选，在 Bi-DexHands 10 个任务上比较。平均成功率：ARBO 0.918，Eureka 0.792，ShinkaEvolve 0.741，RF-Agent 0.707，REvolve 0.655，R* 0.640（表 1）。ARBO 每个候选的 prefill token 约 17.7 万，RF-Agent 约 1.08 万（表 7）。
- **MLREF [笔记]。** 在约 81 次候选训练的设置下，报告其平均成绩高于 Eureka 和 RF-Agent。

**综合判断。** RF-Agent 原文的领先，与 BIRD/ARBO 中的“中游”表现，可以用设置差异解释，因此属于**条件性差异**，不是不可调和的矛盾：

- 预算不同：原文 80/512 个候选，BIRD 40 个，ARBO 128 个；
- 模型不同：原文 GPT-4o-mini/4o，BIRD claude-opus-5，ARBO MiniMax-M2.7；
- 基准不同：原文 IsaacGym/Bi-DexHands，BIRD 是 MetaWorld/MuJoCo/Assistax/HumanoidBench；
- 评价都取各检查点的最大值，搜索方差都没有量化。

还有一种不能排除的解释：生成模型越强，首轮奖励就越好，搜索结构的边际作用随之下降。BIRD 观察到额外迭代的收益递减，并发现后续迭代主要在调系数（§4.1），与这一解释相容。

由此得到两点。第一，RF-Agent 的优势依赖预算和所用 LLM，“更复杂的搜索规则”本身已经不足以支撑一篇期刊论文的贡献。第二，三项研究都把每个候选视为一次完整训练，ARBO 也只在“候选数量”这个口径上计算成本。评价成本和行为对齐这两个问题仍然开放：BIRD 明确留下了前者，并用人类评测揭示了后者。

### 2.2 评价一个奖励候选的成本，以及各类降本方法

按“用什么信号代替完整训练”分为五类：

1. **离线、静态信号。**
   - CARD [笔记]：用旧的成功/失败轨迹比较平均折扣奖励的排序，准确率阈值 0.8，需要成功标签。
   - FLORA（Xu et al., 2026，预印本）[精读]：在 5 条示范上计算阶段预测与 GPT-4.1 标注的一致率、势值与时间的 Spearman 相关、非负塑形项比例，用这些代理指标搜索势函数结构。
   - R* [笔记]：可执行 critic 投票生成片段偏好，用于参数对齐。
   - TAC（Muslimani et al., RLC 2025）[摘要]：衡量奖励与人类轨迹排序的一致性，并证明在 PBRS 下不变。
   - EPIC/DARD/STARC [笔记/摘要]：计算到参考奖励的伪距离。
2. **在线或部分训练信号。**
   - ORSO [精读]：在线模型选择，理论依赖“某学习器始终占优”的假设（Assumption 4.2）。
   - LaRes [精读]：共享回放，用新奖励重标；非精英智能体继承最优智能体的策略和 Q 函数，用奖励缩放和参数约束防止崩溃。
   - Harutyunyan 等（2015）[原文 §1–5.1]：用 Horde 架构让多个势函数在固定行为策略下从同一条经验流离策略学习，再投票合成策略；只在经典控制任务的线性逼近上验证。
   - RHyVE（Wu et al., 2026，预印本）[原文 §1–3]：从共享检查点分叉做短时程训练，额外成本 O(MKL)。作者报告在低能力阶段奖励排名不可靠，只有超过与任务相关的阈值后才有信息量。
   - LLM-ALSO（Wu, Zheng & Xiong, 2026，预印本）[原文 §3.2–3.5、附录 A]：在多智能体合作任务（Level-Based Foraging）中，把 LLM 的提议限制在结构化 PBRS 配置空间内，势函数是若干可解释特征的凸组合；候选在检查点处经过分支验证才并入主训练。基线只有稀疏奖励、预定义 PBRS 和单次 LLM 选择，没有不受限的奖励代码搜索。作者明确说明，由于势函数定义在加入了回合级历史缓存的增广状态上，他们“不假设标准的策略不变性保证”（§3.2）。
   - MLREF [笔记]：报告验证集最优在测试集上仍是最优。
3. **约束候选表示。**
   - LLMProgress（Sarukkai et al., 2024）[笔记]：把进度离散化后做计数探索，候选数从 80 降到 4。
   - CoUR（Mo, 2026，预印本）[原文 §3–4]：对代码不确定性做相似度复用，对解耦后的奖励项做贝叶斯优化。作者报告加入不确定性量化后训练迭代减少 20%（RQ2）；表 1 中 IsaacGym 归一化分数为 CoUR 5.62、Text2Reward 2.78、Eureka 2.66，基线不含 RF-Agent，评价取 10 个检查点中的最大值。它属于“减少冗余评价”，不是跨任务的效用预测。
4. **通用学习曲线外推和多保真度方法。** LC-PFN（Adriaensen et al., 2023）[摘要]、ifBO（Rakotoarison et al., ICML 2024）[摘要]，以及 AutoRL 综述（Parker-Holder et al., JAIR 2022）[摘要]。
5. **不训练直接预测结果。** PoEM（Hamidieh et al., 2026，预印本）[摘要]：用已在其他奖励上后训练好的策略，预测新奖励下 RL 的结果。验证限于文本和图像生成模型。

**离线指标能否预测下游效用，证据有正有反。**

- 正面：RoboReward（Lee et al., 2026，预印本）[精读] 报告，奖励准确率与 RL 后表现的相关系数 r = 0.83。比较对象是同一奖励模型在不同收敛阶段的检查点加基础模型，在 Robomimic 的 3 个任务上用 DSRL 训练到收敛。同节图 2 还显示，学到的进度奖励接近真值奖励的效果，学到的二值成功奖励则明显更差。PPE（Frick et al., 2024）[摘要] 和 Wen 等（ICLR 2025）[摘要] 在 LLM-RLHF 中也报告了弱到中等的正相关。
- 反面或限定条件：ReWiND [笔记] 中，排序指标更高的变体反而策略成功率更低；BIRD 附录 F 中 EPIC 距离与分数无关；Wen 等指出准确率相近的奖励模型，优化后的策略表现可以差别很大；R* 附录 B.2 [笔记] 承认指标“看起来正确”不等于学得更好。

**调和。** 正相关多出现在“同一家族、同一任务、同一学习器”的比较中；反例多出现在改变表示或改变奖励家族的情形中。这与 §2.3 的理论一致：效用是奖励、学习器、预算三者相互作用的结果。

**缺口（截至本次检索）。** 没有看到工作同时做到以下几点：跨奖励家族、任务和学习器的留出预测；报告排序误差、选错后的遗憾和误淘汰率；在同等 GPU 预算下与 ORSO、RHyVE、successive halving 这类强基线比较。这与项目笔记 [cluster_search_policy.md](../../references/notes/cluster_search_policy.md) 在 2026-10-06 的判断一致。本次新增的 RHyVE、CoUR、PoEM、BIRD 都没有填补这一缺口：RHyVE 规模小，只处理少量候选；CoUR 减少冗余评价约 20%，但不做跨任务预测；PoEM 不在控制领域；BIRD 明确没有研究成本。

### 2.3 Shaping 理论：保持最优策略与有限预算效用

**保持最优策略这一侧。**

- 经典结果：Ng 等（1999）[笔记] 的 PBRS 不变性；Wiewiora（2003）[笔记] 的 Q 初始化等价；Devlin & Kudenko（2012）[笔记] 的动态势；Grzes（2017）[笔记] 对分幕任务和终止状态的分析。
- 近期细化：Canonaco 等（2024）[摘要] 分析有限时域截断给 PBRS 带来的偏差，并说明 Φ 取最优价值函数 V* 时最有利；LG-AC（Serris et al., 2026）[摘要] 指出 PBRS 会在终止状态产生欺骗性奖励；Xiao 等（CDC 2019）[摘要] 把 PBRS 扩展到随机策略和 actor-critic；Bahrpeyma（2026）[原文 §2.3–2.4、§5.4] 的统一框架指出，在回放缓冲、自举 critic 和奖励归一化同时存在的深度 RL 流水线中，保证能否成立仍未解决；它比较了回放中处理时变势函数的四种做法，指出还没有隔离其取舍的对照研究（§5.4）。GAE 论文（Schulman et al., ICLR 2016）[原文 §4] 给出：对任意策略，塑形后 Q 和 V 都减去 Φ(s)，优势函数不变。
- 与 LLM 结合的版本：Hounwanou 等（2026）[摘要] 形式化证明“LLM 给出的有界进度分作为势函数，即使不准确也保持最优策略集”，但只在一个小 MDP 上做了数值验证；Bhambri 等（2024）[摘要] 和 Zhang 等（2024）[摘要] 把 LLM 的计划或背景知识写成势函数，实验在网格类环境中。这些与 PRM4RL 的定理 4.1 属于同一类结果。

**有限预算效用这一侧。**

- Gupta 等（2022）[摘要]：从样本复杂度角度刻画 shaping 何时带来收益。
- Laidlaw 等（NeurIPS 2023）[摘要]：在 155 个确定性 MDP（BRIDGE 数据集）上，effective horizon 能预测 reward shaping 对 PPO/DQN 的影响，而以往的样本复杂度界做不到；ICLR 2024 的后续工作 [摘要] 把分析推广到随机环境。
- Razin 等（NeurIPS 2025）[摘要]：无论奖励模型多准确，只要它诱导的奖励方差低，优化地形就是平坦的；对一个策略好用的奖励模型，对另一个策略可能无效。
- Shang 等（2026，预印本）[摘要]：奖励误差可以是无害的，甚至有益（能防止策略停滞在中等奖励的输出上）；奖励的有效性“很大程度上取决于它与初始策略和学习算法的相互作用”。
- Fluri 等（2025）[笔记] 证明训练误差低不等于遗憾低；Karwowski 等（2023）[摘要] 给出 Goodhart 效应的几何解释和早停方法。

**综合（阅读者推断，待检验）。** 上述文献合起来说明，奖励候选至少有两个应分开度量的维度：

- **规格维度：** 它改变了哪个最优策略。这正是 EPIC、STARC、TAC 衡量的东西，它们在 PBRS 下都不变；完整轨迹回报排序在同一起始状态、终止势为零时也不变。
- **可学性维度：** 给定学习器和预算，它让学习快多少。PBRS 只改变这一维。

一个标准推导可以说明 PBRS 的收益从哪里来。对蒙特卡洛策略梯度，若终止状态的势取 0，则塑形后的回报为 `G′_t = G_t − Φ(s_t)`，相当于加了一个状态相关的 baseline：梯度无偏，只改变方差。据此推断，PBRS 在深度 RL 中的实际收益可能主要来自两处：critic 还没学会 Φ 之前的过渡阶段，以及超时截断留下的项 `γ^{T−t}Φ(s_T)`；后者正是 Canonaco 等讨论的有限时域偏差。

这一推断可以同时解释几件事：PRM4RL 的进度势为何有效；直接把进度当奖励为何会偏离目标（PRM4RL 图 6）；为何 VLM-PBRS 中接近随机水平的标签只带来很小的改进。但它还没有在连续控制中由 LLM 写的奖励上得到系统检验。

### 2.4 进度/价值信号：程序化路线与学习路线

**程序化路线。**

- PRM4RL：状态程序加势差。
- LLMProgress：进度用于计数探索 [笔记]。
- VLM-PBRS（Müller & Kudenko, 2026，预印本）[原文 §4–6]：用小 VLM 的图像对偏好学习势函数，在 MetaWorld 4 个任务和 Franka Kitchen 3 个任务上，用 SAC、5 个种子。标签准确率 0.48–0.75（表 1）。标签接近随机时，只比稀疏奖励略好，达不到人工稠密奖励（图 5 说明文字）。非 PBRS 的 RL-VLM-F 会因标签错误收敛到次优策略；人工稠密奖励在 button-press 上也导致次优。
- FLORA [精读]：运动流符号势加里程碑记忆，在增广 MDP 上做 PBRS，在真实 Franka 的 3 个任务上验证；作者承认单调性假设、对遮挡敏感、需人工指定感兴趣区域、离线优化成本四项局限（04 §2.3）。
- Video2STL（Atasever et al., 2026，预印本）[摘要]：VLM 生成 STL 规范，阈值从成功轨迹中标定，用滚动窗口的鲁棒度给出稠密奖励，用因果监视器给出进度奖励。
- MRBT（Potteiger et al., 2026）[摘要]：LLM 生成奖励行为树，用 SMT 验证，并能对子任务失败作出响应。
- ARM-FM、GCR [笔记]：LLM 生成奖励机或组合可达性价值函数。
- StructRL（Yin et al., 2026，预印本）[摘要]：把可验证的子任务完成转化为 VLA 在线 RL 的中间奖励，在 RoboCasa365 和 LIBERO-Long 上用 GR00T-N1.5 与 π0.5 验证。
- Code-as-Monitor（Zhou et al., CVPR 2025）[摘要]：VLM 生成的视觉程序用作故障监视器。

**学习路线。**

- RoboReward、Robometer、GVL/OpenGVL、ReWiND [笔记/原文]。
- Robo-Dopamine 2.0（Xu et al., 2026，预印本）[摘要]：历史条件、OOD 感知的带符号进度。
- Robo-Dopamine（Tan et al., CVPR 2026）[精读]：多视角过程奖励模型，以 PBRS 接入 RL，稀疏成功信号由自身模型判定。ProcVLM、SARM、DenseReward [精读] 的要点见 04 §2。
- eVTA₀/RLER（Wu et al., 2026，预印本）[摘要]：不用示范，从稀疏结果出发用 TD 自举学习成功概率，并随策略演化在线更新奖励。
- SeeQ（Singh et al., 2026，预印本）[摘要]：先用语言预测当前子任务，再估计子任务 Q 值。
- World Value Models [摘要]、DiTaR [摘要]、Rank-Then-Act [摘要]。

**感知方面的诊断证据。**

- AnyviewMeter（Tu et al., 2026，预印本）[摘要]：任务状态不变时，奖励模型的预测也会随视角和遮挡变化；引入相机几何和多视角融合可以降低误差，包括固定相机加腕部相机的真实任务。
- RoboChrono（Wu et al., 2026，预印本）[摘要]：VLM 的帧匹配能力明显强于帧排序能力；“下一动作预测”几乎不依赖视觉输入。
- ProgressCompass、R²VLM [笔记]：进度估计需要正确的上下文和历史。

**综合。**

- **共识：** 阶段或子任务结构对两条路线都有帮助（StructRL、SeeQ、SARM2、ProcVLM）；需要历史或上下文；视角会影响判断。
- **分歧：** 进度的目标定义不统一，有剩余时间、成功概率、阶段完成度等（精读后补充：精读的 5 篇进度/过程奖励模型分别用人工阶段加线性时间、等份额关键帧、视觉变化、人为设计的曲线、回合末 1–5 分来定义进度，接入 RL 的方式也各不相同，所以跨论文的 RL 比较把模型和接入方式混在了一起，见 04 §1、§3.1–3.2），项目笔记 [cluster_visual_progress.md](../../references/notes/cluster_visual_progress.md) 已提醒不同 value 名称的含义不同。两条路线各有代价：学习路线依赖大数据（Robometer 约 1M 轨迹、RynnValue 约 7,000 小时，均见笔记）；程序化路线依赖状态或谓词接口。
- **缺口：** 在真实传感器下，部分谓词不可直接观测，如抓取是否成功、插入深度。程序化进度在这种条件下的可辨识性，以及如何借助历史或主动观测（如腕部相机）解除歧义，只有零散处理：FLORA 自己承认对遮挡敏感（原文 §VII-C）；NoisyRM [笔记] 讨论了信念更新，但依赖大量标签。

### 2.5 对齐、验证与“高分不等于意图”

- **BIRD §4.4 [原文]：** 2 位作者对策略回放评分。完成度与基准分数的一致性：MT10 为 ρ = 0.78，Assistax 为 0.36，HumanoidBench 为 0.26（表 2）。HumanoidBench 中 67 个策略里有 9 个超过参考奖励的 75%，这 9 个全被评为不自然；两个脚本策略（倒退跳、原地摇晃）也能得到相当的参考奖励。作者推测：随着迭代奖励设计变强，分数与自然度之间的差距会扩大，除非把自然度纳入目标或反馈（§5）。
- **No Free Checker（Wan et al., 2026，综述）[摘要]：** 调研约 150 个机器人策略验证器，结论是可用性越高（更便宜、更早、更稠密），可信度越低，“没有免费的检查器”。
- **其他：** RDA [笔记] 用另一个 VLM 给视频评分来衡量对齐，并在 §5.3 用真实的失败轨迹（用躯干推代替双手搬运）驱动奖励修订；ROBORMBENCH [笔记] 显示同一轨迹在改写指令后奖励会出现矛盾；PRM-as-a-Judge 1.0/1.5 [笔记] 提供过程评价工具。

**综合。** 迭代奖励设计会放大评价器的缺陷：优化压力指向哪里，钻空子的行为就出现在哪里。把“规格”（做成什么、怎么做）和“学习辅助”（怎样学得快）分开表示，可以让人只审计前者。这一路径在现有文献中还没有被系统检验，属于工作假设，候选方向 A 以此为出发点。

### 2.6 反向证据：规模能否替代奖励设计

- **AlphaNIST（Zhang et al., 2026；作者注释含 “ICRA”，录用状态未确认）[摘要]：** 只用稀疏二值奖励，从零训练一个策略覆盖 NIST 装配板上全部 20 个任务，训练成功率 98.2%（仿真）。不用示范、进度塑形、脚本原语或逐任务调参。
- **SGS（Zhang et al., CoRL 2026）[摘要]：** 在最多 2²⁰ 个并行环境中，按成功率把训练集中到策略能力的边界附近，解决了以往方法解决不了的地形运动和接触丰富的装配任务，再蒸馏成 RGB 策略零样本迁移到真机。摘要明确把 shaped rewards 和 demonstrations 称为需要大量工程的逐任务先验。
- **真实机器人 RL 流水线：** HIL-SERL [摘要] 依靠示范、人工纠正和高效 RL 算法；RL-100 [摘要] 在扩散策略上用同一个 PPO 式目标统一模仿学习与 RL（离线加在线阶段）；eVTA₀/RLER、Reward-DAgger [摘要]、FIERCE [摘要] 使用学到的进度或失败评估器。

**综合。** 在“仿真可以大规模并行且能做多样化重置”的条件下，稠密奖励设计的必要性明显下降。PRM4RL 和 RF-Agent 的动机都是“稀疏奖励难学”，在这一条件下需要重新界定：

- 一种做法是把贡献落在算力受限的场景，用“奖励设计换算力”的比率来衡量价值；
- 另一种是落在无法重置的真实机器人场景；
- 第三种是落在“怎么做”的规格表达上，例如自然度、安全约束。

目前没有工作定量给出 shaping 与规模之间的替代关系，这是一个开放问题。

---

## 3. 矛盾与调和

| 主张 A | 主张 B | 调和 |
|---|---|---|
| RF-Agent 原文：同预算候选数下明显优于 Eureka/Revolve（表 1、图 5） | BIRD：6 种方法差异不显著，REvolve 最强；ARBO：128 个候选时 Eureka 平均高于 RF-Agent | 条件性差异：预算、LLM、基准和评价协议都不同；三方都没有量化搜索方差。RF-Agent 的优势只在特定设置下成立 |
| RoboReward：奖励准确率与 RL 表现 r = 0.83 | ReWiND：排序指标高的变体策略更差；BIRD：EPIC 与分数无关 | 条件性差异：正相关出现在同族、同任务、同学习器的检查点之间；反例出现在改变表示或奖励家族时。EPIC 衡量的是规格接近度，在 PBRS 下不变，不衡量可学性 |
| PRM4RL、RF-Agent：稠密奖励或进度对稀疏长程任务关键 | AlphaNIST/SGS：大规模并行加重置时，稀疏奖励就够 | 条件性差异（场景不同），但两者之间的定量边界未知，标为未解决 |
| CARD：训练前用离线轨迹排序筛选候选 | RHyVE：低能力阶段奖励排名不可靠 | 不在同一层面：CARD 检查的是规格是否合理（成功轨迹排在失败轨迹前），RHyVE 测的是可学性随能力阶段的变化 |
| RoboReward/PPE：准确率能预测下游表现 | Razin 2025：准确率高而方差低时，优化很慢 | 部分调和：同一学习器、相近的奖励模型之间，准确率有预测力；换了学习器或奖励模型方差不同时，方差主导 |

**跨论文张力清单（#262，供你确认）**

```yaml
cross_paper_tensions:
  - pair_id: CP-001
    paper_a: "gao2025rfagent"
    paper_b: "bhamidipaty2026bird"
    candidate_basis: "opposite finding direction"
    overlap_topic: "树搜索类迭代奖励设计是否在匹配预算下稳定优于其他方法"
    a_finding: "RF-Agent 在 IsaacGym/Bi-DexHands 同候选数下优于 Eureka/Revolve"
    a_evidence_pointer: "RF-Agent 表 1、图 3–5（基础论文）"
    b_finding: "40 次训练、claude-opus-5 条件下，6 种方法间差异基本不显著，REvolve 最强"
    b_evidence_pointer: "BIRD §4.1、图 4/图 7"
    pair_assessment: "conditional_difference"
    resolution_status: "resolved_in_synthesis"
    resolution_pointer: "§2.1 综合判断"
    scholar_confirmation: "pending"
  - pair_id: CP-002
    paper_a: "gao2025rfagent"
    paper_b: "li2026arbo"
    candidate_basis: "opposite finding direction"
    overlap_topic: "Bi-DexHands 上 RF-Agent 与 Eureka 的相对表现"
    a_finding: "512 个候选、4o-mini 下 RF-Agent 领先"
    a_evidence_pointer: "RF-Agent 图 3/图 5"
    b_finding: "128 个候选、MiniMax-M2.7 下平均成功率 Eureka 0.792 > RF-Agent 0.707"
    b_evidence_pointer: "ARBO 表 1"
    pair_assessment: "conditional_difference"
    resolution_status: "resolved_in_synthesis"
    resolution_pointer: "§2.1 综合判断"
    scholar_confirmation: "pending"
  - pair_id: CP-003
    paper_a: "lee2026roboreward"
    paper_b: "zhang2025rewind"
    candidate_basis: "shared construct/outcome/measure"
    overlap_topic: "离线奖励指标能否预测策略效用"
    a_finding: "准确率与 DSRL 表现 r = 0.83"
    a_evidence_pointer: "RoboReward §3 图 3"
    b_finding: "排序指标更高的变体策略成功率更低"
    b_evidence_pointer: "项目笔记 zhang2025rewind.md（表 2/表 3）"
    pair_assessment: "conditional_difference"
    resolution_status: "resolved_in_synthesis"
    resolution_pointer: "§2.2 调和"
    scholar_confirmation: "pending"
  - pair_id: CP-004
    paper_a: "gleave2021epic"
    paper_b: "bhamidipaty2026bird"
    candidate_basis: "shared construct/outcome/measure"
    overlap_topic: "EPIC 距离与策略表现的关系"
    a_finding: "EPIC 在覆盖条件下界定策略遗憾"
    a_evidence_pointer: "项目笔记 gleave2021epic.md（§4/§6.3）"
    b_finding: "迭代奖励设计得到的奖励，其 EPIC 距离与基准分数无关"
    b_evidence_pointer: "BIRD 附录 F"
    pair_assessment: "conditional_difference"
    resolution_status: "resolved_in_synthesis"
    resolution_pointer: "§2.3 综合（规格维度与可学性维度）"
    scholar_confirmation: "pending"
  - pair_id: CP-005
    paper_a: "zhang2025prm4rl"
    paper_b: "zhang2026alphanist"
    candidate_basis: "opposite finding direction"
    overlap_topic: "稀疏奖励长程操作是否需要稠密进度奖励"
    a_finding: "进度势显著改善稀疏任务的学习"
    a_evidence_pointer: "PRM4RL §5.2、图 3–5"
    b_finding: "大规模仿真下二值奖励即可达到 98.2% 训练成功率"
    b_evidence_pointer: "AlphaNIST 摘要"
    pair_assessment: "conditional_difference"
    resolution_status: "flagged_unresolved"
    scholar_confirmation: "pending"
  - pair_id: CP-006
    paper_a: "sun2024card"
    paper_b: "wu2026rhyve"
    candidate_basis: "shared RQ subtopic"
    overlap_topic: "训练前或训练早期比较奖励候选是否可靠"
    a_finding: "离线轨迹排序可以跳过部分 RL 训练"
    a_evidence_pointer: "项目笔记 sun2024card.md（§4, §5.1–5.6）"
    b_finding: "低能力阶段奖励排名不可靠"
    b_evidence_pointer: "RHyVE 摘要与 §3.3"
    pair_assessment: "conditional_difference"
    resolution_status: "resolved_in_synthesis"
    resolution_pointer: "§3 表第 4 行"
    scholar_confirmation: "pending"
```

**覆盖说明：** 本综述涉及约 70 个来源，共评估 6 个候选论文对。选取依据是共享子问题、共享度量、结论方向相反；文献耦合只作为纳入信号。这是**有范围的提示性扫描，不是完整的两两矛盾检测**，不同主题之间未被发现的矛盾可能存在，不能视为不存在。需要你逐条确认 `resolution_pointer`，也可以补充其他论文对。

---

## 4. 知识缺口

1. **成本与效用的可预测性（方法学缺口）。** 缺少在留出任务、留出学习器、多奖励家族上验证的低成本效用预测，以及与强基线的同算力比较。BIRD 和 RF-Agent 都把成本列为未解决问题。影响：如果低成本信号可以预测效用，迭代奖励设计的成本可以降低一个数量级；如果不能，需要先给出预测能力的上限，例如种子噪声决定的天花板。
2. **迭代奖励设计的收益来源（理论与实证缺口）。** 没有工作把 LLM 奖励代码分解为“改变规格的部分”和“只影响学习速度的部分”，也没有检验哪一部分与不自然或钻空子的行为相关。BIRD 只计算了到参考奖励的 EPIC 距离。影响：决定“只搜索势函数”能否兼顾性能和对齐。
3. **连续控制中 shaping 效用的理论（理论缺口）。** effective horizon、奖励方差、误差分类这些理论分别建立在表格 MDP 或 LLM-RLHF 上，没有落到 actor-critic 加 GAE、有限时域截断、LLM 势函数这一组合中。影响：缺少可计算的预测量。
4. **真实传感器下程序化进度的可辨识性（实证缺口）。** 在固定相机、腕部相机、关节状态而没有力觉的条件下，哪些谓词可以辨识，靠历史或主动观测能解除哪些歧义，尚无系统研究。影响：PRM4RL 类方法能否走向真实机器人。
5. **shaping 与规模之间的替代关系（实证缺口）。** AlphaNIST/SGS 与 PRM4RL/RF-Agent 的结论在不同场景下各自成立，但缺少同一任务族上随算力或并行规模变化的对照。影响：决定奖励设计类论文应该在什么场景下立论。
6. **报告规范（方法学缺口）。** RF-Agent、BIRD、ARBO 都报告各检查点的最大值，且不重复整个搜索过程。期刊级论文需要报告搜索方差和最终检查点或留出评价。

---

## 5. 文献矩阵（核心来源 × 主题）

主题主张：

- **T1**：更复杂的搜索带来更好的奖励。
- **T2**：候选效用可以用比完整训练更便宜的信号估计。
- **T3**：保持最优策略不等于有限预算下的效用。
- **T4**：结构化进度能改善稀疏或长程任务的 RL。
- **T5**：高分不等于符合意图，验证器需要在可用性与可信度之间权衡。
- **T6**：难的操作任务必须做稠密奖励设计。

标记：✓ 支持，✗ 反驳，— 未涉及。

| 来源 | 范围 | T1 | T2 | T3 | T4 | T5 | T6 |
|---|---|---|---|---|---|---|---|
| PRM4RL（NeurIPS 2025） | 基础论文 | — | — | ✓ | ✓ | — | ✓ |
| RF-Agent（NeurIPS 2025） | 基础论文 | ✓ | — | — | — | — | ✓ |
| BIRD（2026 预印本） | 原文正文+部分附录 | ✗ | ✗（EPIC） | — | — | ✓ | — |
| ARBO（2026 预印本） | 原文节选 | ✓（智能体式搜索） | — | — | — | ✓（局限） | — |
| RHyVE（2026 预印本） | 原文 §1–3 | — | ✓（有条件） | ✓ | — | — | — |
| VLM-PBRS（2026 预印本） | 原文 §4–6 | — | — | ✓ | ✓ | ✓ | — |
| RoboReward（2026 预印本） | 精读 | — | ✓ | — | ✓ | — | — |
| ReWiND（2025） | 笔记 | — | ✗ | — | ✓ | — | — |
| CARD（KBS 2025） | 笔记 | — | ✓ | — | — | — | — |
| ORSO（ICLR 2025） | 精读 | — | ✓ | — | — | — | — |
| LaRes（NeurIPS 2025） | 精读 | — | ✓ | — | — | — | — |
| MLREF（2026 预印本） | 笔记 | ✓ | ✓ | — | — | — | — |
| FLORA（2026 预印本） | 精读 | — | ✓ | ✓ | ✓ | — | — |
| LLMProgress（2024） | 笔记 | ✗（约束表示更省） | ✓ | — | ✓ | — | ✓ |
| CoUR（2026 预印本） | 原文 §3–4 | — | ✓ | — | — | — | — |
| LLM-ALSO（2026 预印本） | 原文 §3 | — | ✓（分支验证） | ✓ | — | — | — |
| PoEM（2026 预印本） | 摘要 | — | ✓（非控制领域） | — | — | — | — |
| Laidlaw 2023/2024（NeurIPS/ICLR） | 摘要 | — | ✓ | ✓ | — | — | — |
| Razin 2025（NeurIPS） | 摘要 | — | ✗（只看准确率不够） | ✓ | — | — | — |
| Shang 2026（预印本） | 摘要 | — | ✗（只看准确率不够） | ✓ | — | — | — |
| TAC（RLC 2025） | 摘要 | — | ✓（规格维度） | ✓ | — | ✓ | — |
| Canonaco 2024 | 摘要 | — | — | ✓ | — | — | — |
| Hounwanou 2026（预印本） | 摘要 | — | — | ✓ | ✓ | — | — |
| Video2STL（2026 预印本） | 摘要 | — | — | — | ✓ | — | ✓ |
| StructRL（2026 预印本） | 摘要 | — | — | — | ✓ | — | ✓ |
| SeeQ / eVTA₀（2026 预印本） | 摘要 | — | — | — | ✓ | — | — |
| AnyviewMeter / RoboChrono（2026 预印本） | 摘要 | — | — | — | — | ✓ | — |
| No Free Checker（2026 综述） | 摘要 | — | — | — | — | ✓ | — |
| AlphaNIST（2026） | 摘要 | — | — | — | ✗ | — | ✗ |
| SGS（CoRL 2026） | 摘要 | — | — | — | ✗ | — | ✗ |

---

## 6. 注释书目（按主题，只收与候选方向直接相关的来源）

### 6.1 迭代奖励设计与匹配预算比较

**Bhamidipaty, L. M., Robson, L., Petrini, L., Lyu, S., & Ndousse, K. (2026). *A bird's-eye view of iterative reward design*. arXiv:2610.04364.** 预印本，代码开源。
- 相关性：第三方统一比较中包含 RF-Agent，是最直接的外部证据；代码库可作为匹配预算实验的工具。
- 主要发现：见 §2.1 和 §2.5。另外，在 16 个候选的固定预算下，每轮候选数怎样分配，对 10 个任务中的 7 个没有影响（附录 G）。
- 方法：在统一配置空间中复现 14 种方法；4 套基准共 21 个任务；用 Bradley–Terry 排名；人类评测 n = 2。
- **方法缺陷**（empirical；read: 正文全部，附录 D、F 全部，附录 G、H.2、I.2–I.4、I.6 部分段落；附录 B、C、E、H.1、I.1、I.5、J、K 未读）
  - checked: found：internal validity、external validity、conclusion conservatism | checked: none found：research hypothesis clarity、variable operational definitions、statistical reporting completeness（报告了 95% BCa 置信区间和种子数）| not checked：—
  - 每次搜索只有 40 次训练，低于 RF-Agent 原文的 80/512 个候选；当方法的优势依赖大预算时，这一设置会把它的优势掩盖掉。[reader-inferred]
  - 公开基准的任务信息可能已经泄漏进 VLM。[author-acknowledged, section: 附录 D]
  - 没有改变生成模型和评审模型；评测只覆盖机器人控制。结论在其他模型或领域是否成立未经检验。[author-acknowledged, section: 附录 D]
  - 对齐结论依据的人类评测只有 2 位作者；作者把它定位为一个“多数人会同意的负结果”。[author-acknowledged, section: §4.4、附录 D]

**Li, M., Tan, R., & Wang, R. (2026). *Beyond scripted search: Sample-efficient reward discovery via agentic black-box optimization*. arXiv:2609.32394.** 预印本。
- 相关性：在 Bi-DexHands 上把 RF-Agent 作为基线，并以候选数量衡量样本效率。
- 主要发现：见 §2.1；作者报告 7 个消融变体平均损失 29.6% 的增益。
- **方法缺陷**（empirical；read: §1–3、§5.2–5.3、§6、附录 B 表 7）
  - checked: found：variable operational definitions、internal validity、external validity | checked: none found：— | not checked：research hypothesis clarity、statistical reporting completeness、conclusion conservatism
  - 成本只按候选数量计算；ARBO 每个候选的 prefill token 是 RF-Agent 的 16 倍以上，这一口径没有覆盖 LLM 开销。[reader-inferred，依据表 7]
  - 所有方法共用 MiniMax-M2.7，而 RF-Agent 原文用的是 GPT-4o 系列；基线之间的相对表现可能随模型改变。[reader-inferred]
  - 只按文本历史推理，看不到“高分但动作不自然”这类非文本失败。[author-acknowledged, section: §6]

**Gao, N., Zhang, X., Jiang, X., You, M., Zhang, M., & Deng, Y. (2025). RF-Agent: Automated reward function design via language agent tree search. *NeurIPS 2025*. arXiv:2602.23876.** [基础论文] 见 §1.2。

**Liu, C., Wang, X., Chen, R., Li, Z., & Huang, L. (2026). *MLREF*. arXiv:2608.18827.** [笔记] 持久模块池加模块信用；把 RF-Agent 作为基线，设置 80 次 MCTS 更新。方法缺陷：not assessed（本次只读了笔记）。

### 6.2 评价成本与候选选择

**Wu, F., Zheng, X., Wang, Z., Dai, Y., & Li, H. (2026). *RHyVE*. arXiv:2604.28056.** 预印本。
- 相关性：从共享检查点分叉验证，以及“能力阶段决定排名是否可靠”这一观察，直接对应候选方向 B 的强基线。
- 主要发现：见 §2.2。作者明确把该方法定位为“验证驱动的部署协议，而不是通用调度器”。
- **方法缺陷**（empirical；read: §1–3，按规则只评价所读章节）
  - checked: found：external validity | checked: none found：— | not checked：research hypothesis clarity、variable operational definitions、internal validity、statistical reporting completeness、conclusion conservatism（实验章节未读）
  - 分叉验证的额外成本按 O(MKL) 增长，方法明确面向小候选集和稀疏检查点；当候选数达到迭代奖励设计常见的几十到上百个时，不能直接套用。[author-acknowledged, section: §3.2]

**Mo, S. (2026). *Chain of uncertain rewards with large language models for reinforcement learning*. arXiv:2604.13504.** 预印本。代码不确定性加贝叶斯优化，以降低评价成本；在 IsaacGym 9 个环境和 Bi-DexHands 20 个任务上验证（要点见 §2.2）。
- **方法缺陷**（empirical；read: §3–4 与表 1）
  - checked: found：internal validity | checked: none found：variable operational definitions | not checked：research hypothesis clarity、external validity、statistical reporting completeness、conclusion conservatism
  - 评价取 10 个检查点中的最大值，且基线不含近期的搜索类方法（RF-Agent、REvolve 等）；报告的领先幅度可能受评价协议和基线选择影响。[reader-inferred]

**Wu, X., Zheng, Z., & Xiong, H. (2026). *LLM-ALSO*. arXiv:2605.29293.** 预印本。多智能体合作任务中受限于结构化 PBRS 空间的迭代塑形（要点见 §2.2）。
- **方法缺陷**（empirical；read: §3.2–3.5、附录 A）
  - checked: found：internal validity、external validity | checked: none found：variable operational definitions | not checked：research hypothesis clarity、statistical reporting completeness、conclusion conservatism
  - 基线全部是稀疏奖励或 PBRS 族，无法说明受限搜索相对于不受限奖励代码搜索的得失。[reader-inferred]
  - 势函数定义在含历史缓存的增广状态上，作者不主张策略不变性成立。[author-acknowledged, section: §3.2]
  - 只在 Level-Based Foraging 上验证。[reader-inferred]

**Hamidieh, K., Daras, G., & Torralba, A. (2026). *PoEM*. arXiv:2609.30226.** [摘要] 预印本。用已后训练的策略在对数空间的线性或低秩组合，预测新奖励下的 RL 结果；验证限于文本和图像模型。方法缺陷：not assessed（abstract_only）。

**Lee, T., et al. (2026). *RoboReward*. arXiv:2601.00675.** [精读] 预印本。奖励准确率与 DSRL 表现 r = 0.83。方法缺陷见 04 §2.6。

**Zhang, C. B. C., Hong, Z.-W., Pacchiano, A., & Agrawal, P. (2025). ORSO. *ICLR 2025*.** [精读]；**Li, P., et al. (2025). LaRes. *NeurIPS 2025*.** [精读]；**Sun, S., et al. (2025). CARD. *Knowledge-Based Systems*, 326, 114065.** [笔记]；**Xu, T., et al. (2026). FLORA. arXiv:2605.22123.** [精读]。这四篇的要点见 §2.2；方法缺陷：ORSO、LaRes、FLORA 见 04 §2.3–2.5，CARD not assessed（本次只读了笔记）。

**Adriaensen, S., et al. (2023). LC-PFN. arXiv:2310.20447.** [摘要]；**Rakotoarison, H., et al. (2024). ifBO. *ICML 2024*.** [摘要]；**Parker-Holder, J., et al. (2022). AutoRL survey. *JAIR*, 74, 517–568.** [摘要]。用作通用多保真度基线和背景。

### 6.3 Shaping 理论与效用

**Razin, N., Wang, Z., Strauss, H., Wei, S., Lee, J. D., & Arora, S. (2025). What makes a reward model a good teacher? An optimization perspective. *NeurIPS 2025*. arXiv:2503.15477.** [摘要] 奖励方差决定优化地形是否平坦，只看准确率不够。方法缺陷：not assessed（abstract_only）。

**Shang, S., Strauss, H., Wei, S., Arora, S., & Razin, N. (2026). *When errors can be beneficial*. arXiv:2604.25872.** [摘要] 预印本。对奖励误差按其对策略梯度的影响分类，并提出考虑误差危害的评价指标。

**Laidlaw, C., Russell, S., & Dragan, A. (2023). Bridging RL theory and practice with the effective horizon. *NeurIPS 2023*.** [摘要]；**Laidlaw, C., et al. (2024). *ICLR 2024*.** [摘要]。effective horizon 能预测 shaping 的效果，结论建立在确定性或随机的表格 MDP 上。

**Gupta, A., Pacchiano, A., Zhai, Y., Kakade, S. M., & Levine, S. (2022). *Unpacking reward shaping*. arXiv:2210.09579.** [摘要]；**Canonaco, G., et al. (2024). arXiv:2404.07826.** [摘要]；**Serris, O., Doncieux, S., & Sigaud, O. (2026). LG-AC. arXiv:2608.30406.** [摘要]；**Xiao, B., et al. (2019). Potential-based advice for stochastic policy learning. *CDC 2019*.** [摘要]；**Bahrpeyma, F. (2026). A unified framework for dynamic reward shaping in reinforcement learning. arXiv:2608.08158.** [原文 §2.3–2.4、§5.4]；**Hounwanou, C. D., et al. (2026). arXiv:2608.18008.** [摘要]；**Schulman, J., Moritz, P., Levine, S., Jordan, M., & Abbeel, P. (2016). High-dimensional continuous control using generalized advantage estimation. *ICLR 2016*. arXiv:1506.02438.** [原文 §4]；**Harutyunyan, A., Brys, T., Vrancx, P., & Nowé, A. (2015). Off-policy reward shaping with ensembles. *ALA 2015*（短版见 AAMAS 2015）. arXiv:1502.03248.** [原文 §1–5.1]。这些都用于 §2.3 的理论背景；方法缺陷：not assessed（摘要条目为 abstract_only；Bahrpeyma、GAE、Harutyunyan 只读了所注章节，用于核查精读 §3.3 的推导）。

**Muslimani, C., et al. (2025). Towards improving reward design in RL: A reward alignment metric for RL practitioners (TAC). *RLC 2025*. arXiv:2503.05996.** [摘要] 在 PBRS 下不变的对齐指标；11 人用户研究中，使用该指标后选中高性能奖励的比例提高 41%（作者报告）。

**Skalse, J., et al. (2023). STARC. arXiv:2309.15257.** [摘要]；**Karwowski, J., et al. (2023). Goodhart's law in RL. arXiv:2310.09144.** [摘要]；**Wen, X., et al. (2025). Rethinking reward model evaluation. *ICLR 2025*.** [摘要]；**Frick, E., et al. (2024). PPE. arXiv:2410.14872.** [摘要]。

经典文献沿用原语料 [笔记]：Ng, Harada & Russell（1999）；Wiewiora（2003）；Devlin & Kudenko（2012）；Grzes（2017）；Müller & Kudenko（2025）；Gleave 等（ICLR 2021，EPIC）；Wulfe 等（ICLR 2022，DARD）；Fluri 等（2025）。

### 6.4 进度/价值信号

**Müller, H., & Kudenko, D. (2026). *Automating potential-based reward shaping with vision language model guidance*. arXiv:2606.27180.** 预印本。
- 相关性：小 VLM 偏好加 PBRS，是“基础模型给出的势函数”最直接的近邻。
- 主要发现：见 §2.4。
- **方法缺陷**（empirical；read: §4–6、表 1、图 5 文字）
  - checked: found：variable operational definitions、external validity | checked: none found：research hypothesis clarity、statistical reporting completeness（5 次独立运行的均值和标准误）、conclusion conservatism | not checked：internal validity
  - 标签准确率只在专家轨迹采样的 100 张图上测量，与 RL 训练中实际查询的状态分布不同；用它解释“准确率与样本效率的关系”时会产生偏差。[reader-inferred]
  - 只有 7 个任务，评价指标是折扣回报而不是 MetaWorld 惯用的成功率，与其他工作的成功率结果不能直接比较。[author-acknowledged, section: §6（作者说明了指标选择）]

**Atasever, M., et al. (2026). Video2STL. arXiv:2609.37519.** [摘要]；**Potteiger, N., et al. (2026). MRBT. arXiv:2605.05795.** [摘要]；**Yin, Z., et al. (2026). StructRL. arXiv:2609.36352.** [摘要]；**Zhou, E., et al. (2025). Code-as-Monitor. *CVPR 2025*.** [摘要]。都属于程序化或形式化进度的近邻。

**Xu, Y., et al. (2026). Robo-Dopamine 2.0. arXiv:2608.15680.** [摘要]；**Wu, D., et al. (2026). eVTA₀. arXiv:2609.33653.** [摘要]；**Singh, S., et al. (2026). SeeQ. arXiv:2609.22085.** [摘要]；**Wang, Z., et al. (2026). World Value Models. arXiv:2606.24742.** [摘要]；**Li, D., et al. (2026). DiTaR. arXiv:2610.14159.** [摘要]；**Maksyuta, Y., et al. (2026). Rank-Then-Act. arXiv:2607.01897.** [摘要]。学习路线的近邻。

**Tu, Y., et al. (2026). AnyviewMeter. arXiv:2609.20106.** [摘要]；**Wu, Y., et al. (2026). RoboChrono. arXiv:2609.36605.** [摘要]。感知方面的诊断证据。

原语料中的关键条目 [笔记]：GVL、ReWiND、Robometer、ProgressCompass、R²VLM、SARM2、RynnValue、ARM-FM、GCR、NoisyRM、VisionRM、Baert 2024。

精读条目 [精读]：**Tan et al.（2025/2026）. Robo-Dopamine. arXiv:2512.23703；CVPR 2026。** **Feng et al.（2026）. ProcVLM. arXiv:2605.08774。** **Chen et al.（2025/2026）. SARM. arXiv:2509.25358；ICLR 2026。** **Fang et al.（2026）. DenseReward. arXiv:2607.13033。** 版本、阅读范围和要点见 04 §0、§2。

### 6.5 对齐、验证与反向证据

**Wan, Y., et al. (2026). *No free checker: A survey of verifiers for robot policies*. arXiv:2609.09250.** [摘要] 综述。可用性与可信度之间存在此消彼长。

**Zhang, O., et al. (2026). AlphaNIST. arXiv:2610.13354.** [摘要]；**Zhang, O., et al. (2026). A balanced data diet (SGS). *CoRL 2026*. arXiv:2610.12465.** [摘要]。规模能否替代 shaping 的反向证据。

**Luo, J., et al. (2024). HIL-SERL. arXiv:2410.21845.** [摘要]；**Lei, K., et al. (2025). RL-100. arXiv:2510.14830.** [摘要]；**Li, R., Korkmaz, Y., & Bıyık, E. (2026). Reward-DAgger. arXiv:2610.04054.** [摘要]；**Tan, R., et al. (2026). FIERCE. arXiv:2609.18651.** [摘要]。真实机器人 RL 流水线。

**Hatgis-Kessell, S., Knox, W. B., & Brunskill, E. (2026). EARS. arXiv:2609.15544.** [摘要]。在不与环境交互的情况下用偏好学习奖励，适用于真实交互昂贵的场景。

### 6.6 TPAMI 发表实例（用于判断期刊范围）

- Zhang, T., et al. Adjacency constraint for efficient hierarchical RL. *IEEE TPAMI*（DOI 10.1109/TPAMI.2022.3192418），arXiv:2111.00213 [摘要]。arXiv 管理员注释说明它与同一作者的 arXiv 2006.11485 有大量文本重叠；后者是 NeurIPS 2020 论文 “Generating Adjacency-Constrained Subgoals in Hierarchical RL”（作者注释 “Accepted by NeurIPS 2020”）。这是 RL 方法论文由 NeurIPS 版本扩展成 TPAMI 论文的实例。
- Patterson, A., Liao, V., & White, M. Robust losses for learning value functions. *IEEE TPAMI* (2022)，arXiv:2205.08464 [摘要]。
- Shao, R., et al. Large VLM-based VLA models for robotic manipulation: A survey。作者注释为“Under Minor Revision at IEEE TPAMI”，arXiv:2508.13073 [摘要]。
- 原语料中 TPAMI 范围的核对见 [TPAMI_SCOPE.md](../../references/notes/TPAMI_SCOPE.md)。

---

## 7. 来源核验摘要

- **原语料：** sources.csv 中 130 个 arXiv 编号经 API 核对，128 个标题一致，2 个不一致的原因已查明（见检索记录 §1）。
- **新来源：** 56 个 arXiv 编号全部由 API 返回了一致的标题和作者。另有 1 条只出现在网络检索摘要中的说法（“Booth, Knox & Taylor 2025 关于 shaping 与起始分布”）无法定位到原文，**没有写进综述**。
- **证据等级（技术领域按相对标准，金标准为 Level III 受控实验）：**
  - 大多数实证论文属于 Level III（受控仿真或真机实验）；
  - 理论论文按证明是否严谨评价，不套用 Level 等级；
  - 综述为 Level V。
- **用途分级：**
  - 可作为主要证据：基础论文；BIRD（正文全部与部分附录，预印本）；精读的 8 篇（见 04）；VLM-PBRS §4–6；LLM-ALSO §3；CoUR §3–4；GAE §4；Harutyunyan 2015 §1–5.1；Bahrpeyma 2026 §2.3–2.4、§5.4。
  - 作为支持证据：同行评审的理论论文（摘要层面）。
  - 需要附带说明：只读了摘要的预印本，以及本次只读了笔记的条目。
- **利益冲突：** 两篇基础论文是本项目的已有工作，评价它们时存在学术利益冲突（intellectual COI），所以 §1 的边界判断都给出了原文定位，方便你复核。BIRD 的作者来自 Anthropic Fellows Program 和 Anthropic，而本综述由 Anthropic 的模型完成；BIRD 中 claude 系列模型被用作奖励生成器，这对 BIRD 关于方法比较的结论没有直接利害关系，但在此一并披露。

---

## 8. 本综述的局限

- 这是叙述性综述，不是系统综述。只检索了 arXiv 和通用网络，没有覆盖 IEEE Xplore 等期刊数据库；中文文献没有检索；有 1 条查询因网络中断没有完成。
- 新纳入的 56 篇中，50 篇只读了摘要；2026 年的预印本占多数，作者报告的数字都没有复现。
- 原语料 164 篇的内容判断依赖 2026-10-06 的笔记。本次只核对了编号和标题，以及与候选方向直接相关条目的笔记要点。
- §2.3 中“PBRS 在策略梯度中相当于 baseline”是标准推导；由此得出的“效用主要来自 critic 过渡阶段和截断项”是阅读者推断，需要实验检验。
- ARS 的隐藏引用标记和 Material Passport 流程没有使用，因为本项目没有对应的下游校验环节；改为在正文中直接写出原文定位。

## 9. AI 使用声明

本综述的检索、阅读、核验和综合由 AI 助手（Claude，ARS deep-research `lit-review` 模式）完成，所有判断都需要研究者复核。来源的存在性用 arXiv API 程序化核验；原文阅读范围按条目标注。
