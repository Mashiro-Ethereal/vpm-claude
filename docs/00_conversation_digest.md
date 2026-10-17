# 对话总结与备忘（2026-10-15 至 2026-10-17）

> 用途：长时间不讨论 idea 后，用来快速恢复上下文。整理自会话“文献基础与论文方向探索”的全部对话（51 条你的消息）和项目文档。
> - **权威设计以 [VPM_idea.md](../VPM_idea.md) 为准**。本文只记录过程、决定的理由、约束和容易忘的细节。
> - 本文分成几类：已定稿的决定（§3）、已核对的事实（§5）、工作假设（§6）、待决事项（§8）。
> - 会话链接：`claude://claude.ai/epitaxy/local_95d1cfb6-fdbf-4835-8b93-0822b92ea198`
> - 完整对话记录：`/home/zxh/.claude/projects/-home-zxh-projects-dir-vpm-claude/36eb3cb1-2ce7-422d-84a7-bb234028d31c.jsonl`

## 0. 恢复上下文的阅读顺序

1. 本文。
2. [VPM_idea.md](../VPM_idea.md)：§0 故事与贡献、§1 总流程、§3 Stage1、§4 Stage2、§5 Stage3、§6 实验、§9 待决事项。
3. [07_vpm_optimization.md](exploration/07_vpm_optimization.md)：每条优化建议的“讨论结果”，记录了决定的来由。
4. [06_vpm_idea_review.md](exploration/06_vpm_idea_review.md)：对原稿的客观分析，包括近邻工作和内部问题。
5. 更早的材料：[05](exploration/05_five_directions.md) 五个方向、[04](exploration/04_close_reading_8papers.md) 8 篇精读、[02](exploration/02_literature_review.md) 综述、[03](exploration/03_candidate_directions.md) 三个方向（旧版）。
6. 检索与核验记录：[references/notes/SEARCH_2026-10-15.md](../references/notes/SEARCH_2026-10-15.md)。

## 1. 项目与当前状态

- **目标：** 投 TPAMI，承接两篇 NeurIPS 2025 论文：你一作的 PRM4RL，和你参与的 RF-Agent。只做研究方向与设计，不写稿件。
- **当前状态（2026-10-17）：**
  - idea 已逐项讨论定稿，写在 VPM_idea.md。
  - Stage1 的设计与实现已交给单独的会话（见 §7）。
  - 本会话今后只讨论整体 idea。

## 2. 时间线

| 日期 | 做了什么 | 产物 |
| --- | --- | --- |
| 10-15 | 用 ARS deep-research 的 lit-review 模式做文献基础，你选了 narrative review | [02](exploration/02_literature_review.md)、[SEARCH 记录](../references/notes/SEARCH_2026-10-15.md) |
| 10-15 | 提出三个方向 A/B/C | [03](exploration/03_candidate_directions.md) |
| 10-15 | 精读你指定的 8 篇（Robo-Dopamine、ProcVLM、FLORA（Beyond Pixels）、ORSO、LaRes、RoboReward、SARM、DenseReward）；撤回“critic 精确平移”的设想 | [04](exploration/04_close_reading_8papers.md) |
| 10-15 | 综合后提出五个方向 | [05](exploration/05_five_directions.md) |
| 10-16 | 你对方向二、三、五感兴趣，并给出自己 10-09 的原稿 VPM_idea；我做了客观分析 | [06](exploration/06_vpm_idea_review.md) |
| 10-16 | 提出优化建议，然后逐点讨论：第一点（动机）、第二点（Stage2 与 Stage3 的衔接）、第三点（自动机、谓词、guidance）、§2.2–§2.4、B 组（奖励接入） | [07](exploration/07_vpm_optimization.md)，VPM_idea 多次修改 |
| 10-17 | A 组（视觉 VPM 设计，记为备选）、C 组（Stage1/2 与 V0 的实验）、D 组（贡献、流程图、待决清单） | VPM_idea §0.4、§1、§5.7、§6、§9 |
| 10-17 | 定下 Stage1 的前提；发生“旧代码”事件（§4）；Stage1 交给单独会话 | 本文 |
| 10-17 | 把 Stage1 的三项前提写入 VPM_idea，并在 §9 新增“Stage2 用哪台机器” | VPM_idea §6.3、§6.6、§9 |
| 10-17 | 整理项目结构并初始化 git | README.md |

修改 VPM_idea 前都会备份，备份在 [archive/](archive/)：10-09 原稿，以及第一点、第二点、第三点、§2.2–§2.4、B 组、A 组、C 组、D 组各自定稿后的版本。D 组定稿后的备份，也是写入 Stage1 前提之前的版本。

## 3. 已定稿的决定（按主题）

### 3.1 动机与核心主张（10-16）

- **你的出发点：** 不论稀疏还是稠密，奖励只是一个标量，信息量很少。讨论后改成两层意思：
  - 标量奖励足以**定义**任务，但作为唯一的**学习信号**，信息量低。这样表述不与 PBRS“不改变最优策略”冲突，而后者正是 PRM4RL 的理论立足点。
  - 关键对比不在“网络更复杂”，而在任务变量是否已经在策略的输入里：状态输入时代价小；图像或 VLM 输入时，策略要自己从观测中学出任务结构。
- **核心主张：** “标量奖励是任务过程状态的有损投影”。增益取决于策略需要从观测中自己学出多少任务结构。
- **为什么用仿真：** DeepSeek-R1 列出的过程奖励模型的三个困难里，“步”难以定义、中间步难以判定这两个，可以由仿真特权状态加程序化 teacher 消除。你认为这正是 VPM 要解决的核心问题：全自动、准确地标注。
- **适用范围：** 长时程、多阶段、交互预算有限的任务。DeepSeek-R1 和 SimpleVLA-RL 说明，在其他条件下，结果奖励可能已经足够。
- **指标：**
  - 主指标：样本效率，以及有限预算下的最终成功率；
  - 次要指标：泛化；
  - 机制指标：用线性探针从策略特征中解码阶段和条件的准确率。
- **下游：** 两类最终都做，即从零训练的视觉策略和预训练 VLA。

### 3.2 Stage2 与 Stage3 的衔接（10-16）

- Stage2 训练**特权状态输入**的策略。你的理由：Stage1 的过程 teacher 是读特权状态的程序，一次生成不保证正确，Stage2 的任务是通过真正训练来检验和修正它。
- 搜索中每个候选的训练 rollout，按分层抽样保存仿真状态。Stage2 结束后，用最终选定的过程 teacher 统一重标、按需要的相机重新渲染，作为 Stage3 的训练数据。
  - 价值主要在“覆盖策略实际会访问的状态”，包括失败、停滞、回退和钻空子的行为，不只是提高数据利用率。
  - 你把分层配比类比为 LLM 后训练中的数据配比。
- **术语：** 过程 teacher 是读特权状态的程序；视觉 VPM 是 Stage3 的图像模型；单独出现的 VPM 指整条路线。
- 以下两项只记录、不进第一版：
  - 闭环：用下游策略的 rollout 重标，再训练视觉 VPM。记为后续方向。
  - 被钻空子的程度：记录，但不作核心指标。你认为这种情况少，发现时再分析。
- **仿真器：** ManiSkill、MetaWorld、LIBERO。“保存状态 → 恢复 → 渲染”的测试作为工程问题暂缓，目前只核对到文档层面。

### 3.3 Stage1 的过程表示（10-16）

- **带守卫谓词的阶段自动机**（与奖励机同构，但边上不直接给奖励）：
  - 守卫是谓词的合取；
  - 不变量是进入某阶段后需要保持的条件；
  - 不变量被破坏时，阶段沿回退箭头回退，guidance 随之改变并附一条说明，势值下降，PBRS 自然给出负的塑形奖励。
- **共享谓词库：**
  - 谓词有类型签名，对象带多标签属性。你提出“谓词的输入对象应当有限制”，这就是类型签名的来由。类型只回答“是否合法”，不回答“是否成立”。
  - 三层结构：测量函数、基本谓词（测量量加阈值）、派生谓词（逻辑组合）。
  - 分工：人定义类型体系和核心谓词，并写单元测试；LLM 标注对象类型、划分阶段、组合守卫、标出不变量、编写 progress。
  - 新谓词先作为任务局部谓词，附签名和测试；被多个任务用到后，才由人审核、升级进共享库。
  - 你担心新任务需要建很多新谓词。回应的依据是 LIBERO（130 个任务用少量谓词）和 BEHAVIOR，并在实验中报告谓词库的增长曲线。
- **guidance：** 当前阶段出边守卫中不成立的谓词，用模板渲染成文字；生成数据时可以由 LLM 改写。
  - 第一版的粒度是“条件加上它的自然补救办法”；带方向的提示（接近 RT-H）做消融。
- **检验：**
  - ArtifactValidator 新增类型检查；EnvGroundedValidator 检查代码能否在环境中运行。
  - 五项语义检验：守卫的必要性与充分性、可执行性、预测性、一致性（必要时加滞回）、阶段是否只由当前状态决定。

### 3.4 进度作为奖励时的六条接入规则（B 组，10-16）

1. `R = γΦ(s′) − Φ(s) + I_success · r_bonus`，γ 与 RL 算法一致。不带折扣的差分会让策略停在高进度状态（Robo-Dopamine 附录 A.2）。
2. 真正终止时势值为 0；超时截断时用 critic 自举（Grześ 2017；Pardo et al. 2018）。
3. 成功信号独立判定，不用视觉 VPM 的进度阈值。
4. 势值每步只算一次并复用。视觉 VPM 的进度用确定性回归；可选软势值 `Φ̂ = Σ_k P(k|o)(k + p_k)/K`。
5. 不做会改变塑形尺度的归一化：GRPO 在全部失败的组里会抵消塑形（Dark Room）。
6. 默认阶段等权；校准形状不进主实验（TR-DRL 最终选了线性）。

### 3.5 Stage2 的搜索与早期评价（§2.2–§2.4，10-16）

- **两层搜索：**
  - 内层用 BO 调阈值和 progress 参数，与 FLORA 的分工类似；
  - 外层只在 §3.5 的诊断发现问题时，由 LLM 修改结构；
  - RF-Agent 的扩展动作保留，分别作用于结构和参数。
- **早期评价：** 用固定的共享谓词里程碑，并先检验预测力（E-S3）。
- **阶段入口探针**作为后续改进：比较只在第 k 阶段有差异的候选，前面阶段已经确定；复制训练好的 actor，重置 critic，从第 k 阶段的入口状态开始训练。你复述的理解是对的。
- **视觉可学性**作为 teacher 选择的约束：同意，但只是锦上添花，不进主实验；做法是对每个谓词测一次可观测性。

### 3.6 视觉 VPM（A 组，10-17）

- **已定：** 视觉 VPM 不直接输出全局势值，由阶段概率和阶段内进度按软势值计算。
- **备选，等 Stage1、Stage2 完成后再定（§5.7）：**
  - 输入加短历史与多视角，或在预测出的谓词序列上运行自动机来跟踪阶段；
  - 骨干：你倾向 2–4B 的小型 VLM（为了泛化），轻量模型作对比；
  - 提示门控（共形校准）、主动核验（切换到腕部相机）、校准评价。
- **更正：** 原建议“作为奖励时只奖励有把握的推进”与 PBRS 冲突，已撤回。奖励中的不确定性只通过软势值体现。

### 3.7 Stage1、Stage2 与 V0 的实验（C 组，10-17）

- **任务三层（§6.1）：**
  - 第一层（承接 PRM4RL）：MetaWorld 的 pick-place、drawer-close、door-close、button-press；ManiSkill 的 PickCube、LiftPegUpright。
  - 第二层（多阶段）：ManiSkill 的 StackCube、PegInsertionSide、StackPyramid；MetaWorld 的 assembly、hammer、shelf-place、bin-picking。
  - 第三层（LIBERO）：Stage1、Stage2 从 LIBERO-90 选 3–5 个含两三个子任务的任务；LIBERO-10 留出测泛化；RL 允许用示范热启动（先 BC 再 RL）。你担心视觉 VPM 没见过 LIBERO 场景会泛化差，所以 LIBERO 也跑 Stage1、Stage2。
- **实验：**
  - G1：比较谓词库组合与 PRM4RL 式自由代码；
  - 谓词库增长曲线；
  - E-S3 早期评价的预测力，最先做；
  - E-S1 语义修正的价值；
  - E-S2 相同 GPU 时长下的搜索效率；
  - E-S4 预算分配。
- **基线：** PRM4RL、RF-Agent、环境稠密奖励、稀疏奖励。不加 Eureka，因为 BIRD 显示 RF-Agent 与 Eureka 差异基本不显著。
- **RL 算法：** ManiSkill 用 PPO；MetaWorld 和 LIBERO 用 SAC。奖励在采集时计算并存入。
- **统计：** 每个条件 3–5 个种子，报告置信区间。
- **rollout 保存与覆盖度分析：** 见 §6.4。
- **V0：** 用真值标签测上限，作为 Stage3 的止损点。
  - 第一轮只做状态 MLP 和从零训练的视觉策略；
  - 三种渠道：奖励、输入、辅助监督；
  - 对照：占位对照、通用辅助信号对照。

### 3.8 收尾（D 组，10-17）

- 贡献重写为五条（§0.4），第五条依赖 Stage3。
- 流程图按定稿更新（§1），V0 作为止损点。
- 待决事项汇总到 §9。

### 3.9 Stage1 的前提（10-17）

- 生成 Stage Graph 的 LLM 用 DeepSeek，Harness 用 Claude Code。
- 服务器 CPU：2 颗 Xeon Gold 6226R，32 核 64 线程。
- 先在 ManiSkill 上跑通，再扩展到其他环境。
- 这三项已于 10-17 写入 VPM_idea（§6.3、§6.6、§9）。§6.3 同时注明：PRM4RL、RF-Agent 基线用同一个 DeepSeek 模型重跑。

## 4. 工作偏好与约束

- **交流：** 用简体中文，学术术语用英文。
- **标注：** 区分【事实】【推导】【假设】【待你决定】；不用 FINER 或其他打分表；提出方案后停下来，等你选择。
- **来源：** 引用要核对原始来源，并说明读了哪些部分。你会追问“是否真的读过”。
- **改文档的流程：** 讨论，你明确说“写进去”，我先备份到 archive/，再改 VPM_idea.md 和 07，最后更新记忆。没有你的确认，不改设计文档。
- **旧代码约束（10-17）：**
  - `/home/zxh/projects_dir/vpm` 是你以前让 Codex 写的废案，你认为写得不够好，所以才在不受它影响的情况下和我重新研究这个 idea。
  - 不阅读、不复用、不参考它，也不据此更新文档。我曾据它写过一份 Stage1 草案（08），已按你的要求删除。
  - `vpm-v2` 中的材料（VPM_idea §8 链接了其中一部分），用之前先问你。
  - 本机的 `/home/zxh/projects_dir/ManiSkill` 目录和 conda 环境 `vpm-mani` 是旧项目搭的，沿用还是新建，先问你。
  - 核对对话记录后确认：此前的讨论（02–07 和 VPM_idea 的修改）没有读过这两个目录里的任何文件。
- **分工（10-17）：** 本会话只讨论整体 idea；Stage1 的实现在单独会话里，它不向本会话汇报。

## 5. 已核对的事实（便于复用）

### 5.1 资源

- **项目记录（10-06）：** 8 张 A100 80G；真实机械臂，配固定相机和关节状态，腕部相机可配置；没有力/力矩和触觉传感器。机械臂型号和可用时长尚未提供。
- **本机（10-17，`nvidia-smi`）：** 4 张 RTX 3090 24 GB。与上面的 8 张 A100 不一致，可能是两台机器；Stage2 用哪台待定。
- **参照：** PRM4RL 在 4 张 3090 上，MetaWorld 每个任务约 1 小时（5 个种子同时跑），ManiSkill 每个任务 1–10 小时；RF-Agent 每个任务 9 小时（IsaacGym）到 40 小时（Bi-DexHands）。

### 5.2 ManiSkill（10-17）

- PickCube-v1、LiftPegUpright-v1、StackCube-v1、PegInsertionSide-v1、StackPyramid-v1 在 3.0.1 版本中都存在。PRM4RL 用过的 LiftCube 在这个版本中不存在。
- **StackPyramid 没有环境稠密奖励**（官方文档的任务表），也没有官方 PPO 配置，回合上限 250 步。它在 Stage2 E-S3 中可能给不出排序信号；交给 Stage1 会话讨论。
- 官方文档显示这几个任务都有示范。
- PegInsertionSide 的文档有一处错误：成功条件写的是“白色一端”，代码判定的却是橙色一端（`peg_head`）。说明只靠文字描述不可靠。
- 场景物体按唯一名称登记在 `scene.actors` 和 `scene.articulations` 中，可以自动列出。
- 官方 PPO 示例：`ppo_fast.py` 默认 γ=0.8，PegInsertionSide 的配置用 0.97。按 PBRS 规则，γ 必须与 PPO 一致。
- 官方 PPO 配置的训练量：PickCube、StackCube、LiftPegUpright、PokeCube 为 5,000 万步、4096 个并行环境；PegInsertionSide 为 7,500 万步、2048 个并行环境。README 称 PickCube 的状态输入 PPO 在 GPU 上约需 2–5 分钟。
- `vpm-mani` 环境里缺 `tensordict`（`ppo_fast.py` 需要），`mplib` 在 NumPy 2 下导入失败。只在沿用该环境时有关。

### 5.3 LIBERO

- 基于 robosuite（MuJoCo）。任务完成由仿真状态上的谓词判定；示范数据中存有完整的仿真状态。但常用接口只给图像和本体状态，读物体位姿需要访问仿真器内部。
- LIBERO 论文把 LIBERO-100 分为 LIBERO-90 和 LIBERO-10（arXiv:2306.03310）。
- 它是 CPU 仿真，任务时程长，只有稀疏奖励。

### 5.4 DeepSeek（10-17 读取官方文档）

- `deepseek-flash` 对应 DeepSeek-V4.1-Flash，`deepseek-v4-pro` 对应 DeepSeek-V4-Pro-0813，上下文都是 1M。
- 旧名 `deepseek-v4-flash` 已改为指向 V4.1-Flash。名称背后的模型会变，每次运行都要记录实际版本。
- 高峰时段每百万 token：flash 的输入 0.3 美元、输出 1.2 美元；pro 分别为 1.32、3.96 美元。非高峰时段半价。LLM 费用相对 RL 算力可以忽略。
- Claude Code 的接入方法：设置 `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic` 等环境变量，详见官方的 Claude Code 接入说明。
- Claude Code 显示的成本按 Anthropic 价格估算，实际以 DeepSeek 账单为准。
- 可比性：PRM4RL 用 GPT-4o，RF-Agent 用 GPT-4o-mini 和 GPT-4o。基线需要用同一个 DeepSeek 模型重跑。

### 5.5 影响了决定的文献证据

- **搜索规则：**
  - BIRD（arXiv:2610.04364）在统一实现下比较了 6 种方法，差异基本不显著，REvolve 最强；
  - ARBO（arXiv:2609.32394）中，Bi-DexHands 平均成功率 Eureka 为 0.792，RF-Agent 为 0.707。
  - 所以论文不宜把贡献放在更复杂的搜索规则上。
- **评价成本：** RF-Agent 把减少 RL 训练次数列为未来工作；BIRD 明确没有研究计算效率。
- **接入方式：**
  - 跨论文的进度奖励比较，把奖励模型和接入方式混在了一起（精读 §3.2）；
  - Dark Room（arXiv:2607.21273）发现，决定效果的是接入渠道，而不是信号内容；
  - 精读的 8 篇都没有引用 PRM4RL。
- **理论：**
  - PBRS 不改变优势函数（GAE §4），等价于给价值函数一个初始值（Wiewiora 2003）。所以“精确平移 critic”会让切换势函数失去作用。
  - RHyVE（arXiv:2604.28056）：策略能力低时，候选的排名不可靠。
- **标注质量：** ProcVLM 的自动标注只有 49.44% 通过人工审计。DeepSeek-R1（arXiv:2501.12948）在推理任务上不用神经网络奖励模型。
- **最接近的工作（§0.4 的对照表）：** 奖励机（Icarte 2018）、ARM-FM、Code-as-Monitor；RF-Agent、RHyVE、ORSO；DenseReward、AHA、FailSafe、SARM；RT-H、RACER、ECoT、Dark Room。
- **06 的判断：** 三块组成部分各有很近的近邻，没有找到把三者组合起来的工作，但审稿人可能把组合看作系统集成。所以需要 V0 和信息量匹配的对照。

## 6. 工作假设（需要实测）

- E-S3 的校准集最重：4 个任务 × 40 个候选 × 3 个种子 × 约 2 小时，约 1000 GPU 小时（VPM_idea §6.6）。按 ManiSkill 官方配置推算，单次训练可能只要十几分钟到一小时，总量可能偏高；需要实测。
- rollout 存储：例如 1000 万个状态，每个约 1 KB，约 10 GB。
- 过程 teacher 的计算要在 GPU 上对全部并行环境批量进行，否则会拖慢 ManiSkill 的 GPU 并行训练。
- 描述性的覆盖度分析，可以为“搜索 rollout 覆盖策略行为”提前提供证据。

## 7. Stage1 实现会话

- **名称：** “Stage1 在 ManiSkill 上的实现”。链接 `claude://claude.ai/epitaxy/local_20268ca0-25e5-4ad5-8ea7-bfb480960ca3`。10-17 创建，已移到顶层，不再向本会话汇报。
- **给它的约束：**
  - 只以 VPM_idea 为依据，不参考旧代码；
  - 不修改 VPM_idea 和 07；涉及整体设计的问题记下来，拿回本会话讨论；
  - 代码放在哪里、是否沿用旧环境，先问你；
  - 逐点讨论，每一步停下来确认。
- **给它的议程：**
  1. LLM 的输入与输出；
  2. ManiSkill 第一版谓词库；
  3. 自动机的运行语义；
  4. progress 的写法与参数化；
  5. Harness 与可复现（含 flash 还是 pro）；
  6. 检验数据与通过标准；
  7. 任务集与 G1；
  8. 工程与算力。
- **10-17 的进展（据它的报告）：** 读完 VPM_idea，复述了 Stage1，对第 1 点提了六项建议。最大的变化是环境接口：给场景清单和 `evaluate()` 的源码，奖励代码一律不给。还没写代码，在等你确认。

## 8. 待决事项

**VPM_idea §9（10-17 写入 Stage1 前提后的编号）：**

1. LLM 的使用：已定，DeepSeek + Claude Code；具体型号在 Stage1 会话中定。
2. CPU：已定，32 核 64 线程。
3. 任务名核对：ManiSkill 部分已完成；MetaWorld 和 LIBERO 未核对。
4. Stage2 用哪台机器：本机 4 张 3090，还是 8 张 A100（10-17 新增）。
5. 下游 VLA 选哪个（如 OpenVLA-OFT、π0），以及微调的算力。
6. 视觉 VPM 的输入、骨干网络和置信度的用法（§5.7）。
7. 是否加入历史信息，以及是否相应收窄总问题中“长时程”的表述。
8. 内容 × 渠道矩阵中涉及视觉 VPM 的部分（V1 及以后的实验）。
9. 真机：避开依赖接触或力觉的谓词，还是作为反例；机械臂型号、每周可用时长、能否自动复位、腕部相机的安装方式。
10. 两层搜索与早期评价放在同一篇论文，还是单独成文。
11. 论文定位：新论文，还是 PRM4RL、RF-Agent 的扩展版。
12. PRM4RL 是否补发 arXiv 版本，以及怎样表述继承关系。
13. §0.4 引用的 TPAMI 实例（CA-Nav、VeBrain-1.5）尚未核实。

**10-17 新出现、交给 Stage1 会话的问题（未写入 VPM_idea）：**

- StackPyramid 在 Stage2 中的角色（它没有环境稠密奖励）。
- DeepSeek 用哪个型号，是否加第二个 LLM 做稳健性检验。

**决定后续走向的经验关口：**

- E-S3：早期评价有没有预测力；
- V0：真值上限，决定 Stage3 的范围；
- G1 与谓词库增长曲线：谓词库是否可靠、是否可扩展。

## 9. 记录为后续方向（不进第一版）

- 闭环重标，以及被钻空子的诊断（§7.6）；
- 阶段入口探针（§7.6）；
- 视觉可学性检查（§7.3）；
- §5.7 中的置信度等备选；
- 带方向的 guidance（消融）；
- 内容 × 渠道矩阵中涉及视觉 VPM 的部分。

## 10. 撤回或更正过的说法（不要再引入）

- “换势函数时精确平移 critic，让多个候选共享训练”：不成立。平移后，切换不再起作用（04 §3.3；GAE §4；Wiewiora 2003）。
- “作为奖励时只奖励有把握的推进”：与 PBRS 冲突（07 §3.5）。
- 势值必须每步只算一次并复用，不能在相邻两个塑形项中各算一次（07 §3.6，B 组第 4 条）。
- 仿真器的状态保存、恢复与重新渲染，只核对到文档层面，没有实测。
- 08_stage1_maniskill_plan.md：以旧代码为基础写成，已删除。其中来自 ManiSkill 和 DeepSeek 官方资料的事实，已收在本文 §5。

## 11. 工具与环境备忘

- **arXiv 访问：** WebFetch 访问不了 arxiv.org。可行的办法是用 `export.arxiv.org` 的 API（请求间隔至少 3 秒）和 `export.arxiv.org/pdf/<id>`，再用 `pdftotext -layout` 提取文字。OpenAlex 可用；Semantic Scholar 没有 key 时返回 429。
- **编辑脚本：** 改文档用的“唯一精确替换”脚本放在会话临时目录，会丢失，但不影响文档本身。
- **长期记忆：** 位于 `/home/zxh/.claude/projects/-home-zxh-projects-dir/memory/`，包括你的研究背景、输出偏好、项目进展、不参考旧代码的约束和 arXiv 访问办法。
