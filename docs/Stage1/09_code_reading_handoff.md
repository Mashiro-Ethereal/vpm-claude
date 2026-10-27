# 代码阅读会话的交接说明（2026-10-27）

> **用途：** 开一个新会话，带用户读 Stage1 的代码并回答问题：每个文件做什么，训练时一步之内数据怎么流，关键的地方为什么这样写。这是阅读会话：不改代码，不提交，不跑训练。
>
> **怎么用：** 新会话的第一句话说“读 `docs/Stage1/09_code_reading_handoff.md`，照它带我读代码”。第 1 节是写给那个会话的规则；第 3–7 节也可以直接当代码地图读。

## 1. 用户与规则

### 1.1 用户

- PRM4RL 的第一作者、RF-Agent 的合作者，研究用 LLM 设计机器人 RL 的奖励。熟悉 RL、PBRS 和 ManiSkill，没读过这套代码。
- 已经知道两个结论：teacher 作为进展的度量基本没问题（[08](08_teacher_check.md)）；用它的 PBRS 奖励训练 PPO，三轮都没学会（[07](07_ppo_check.md)）。读代码时可能会把问题和这两份结果联系起来。

### 1.2 硬约束（原任务的原文，一直有效）

- “`/home/zxh/projects_dir/vpm-claude` 是我们唯一的工作目录，未经允许不要访问这台服务器上的其他位置，如果确实需要访问其他位置必须得到我的允许。例外：conda 环境 vpm-mani 可以只读使用（其中的 mani_skill 3.0.1 以可编辑方式装自 `/home/zxh/projects_dir/ManiSkill`，也只读，可以读它的源码），不装包、不改环境。”
- “不要修改设计文档（`VPM_idea.md` 和 `docs/` 下的文件），`docs/Stage1/` 除外。遇到需要改动整体设计的问题，记在 01 §5，告诉我，讨论之后再决定。”
- “不使用 `/home/zxh/projects_dir/vpm`（以前的失败尝试）。”
- “提交前先问我；不推送；不合并到 master。当前分支是 stage1-impl。`references/` 整个不进 git。”
- “DeepSeek 版 Claude Code（`/home/zxh/.local/bin/claude-deepseek`）只由 harness 的代码调用：不读包装脚本的源码；它的配置文件含密钥，不读取、不打印、不记录；不打印环境变量的值，需要时只列名字。”
- “调用 DeepSeek（PickCube 试跑）和下载任何资产之前，先问我。PickCube 用不到需要下载的资产。”

此外：
- 不用 0 号卡，那是别人的任务。
- wandb 不读凭据，不运行 `wandb login`。
- 全局的 CLAUDE.md 照常适用：重的编码交给 Codex，审查后不自动提交。

### 1.3 这个会话怎么做

- **一次讲一个点，讲细。** 用 PickCube 作贯穿的例子，第 5 节有现成的数字。讲完一个点就停下，等用户提问或说继续，不要一次倒出很多点。
- **写法：** 中文，技术名词用英文。分清【事实】（读代码或跑出来的）、【推导】和【假设】。不用评分表。
- **先核实再回答。** 回答前打开代码看，不凭本文或记忆。本文的行号是 2026-10-27 的，代码改过以后以文件为准。引用代码写成可点击的 `路径:行号`。
- **回答“为什么这样写”：**
  - 先查 [00](00_technical_plan.md) 的对应小节，再查那一步的任务说明：M1a–M5 的在 [briefs/](briefs/)，后面几步的在 `outputs/stage1/codex/<步骤>/brief.md`（PPO 检查是 `ppo_check`，第三轮的代码是 `rl_variants`，teacher 检验是 `teacher_check`）。
  - 两处都没规定的，是 Codex 的实现取舍，照实说。
  - 设计的理由在 00 第 11 节与 [01](01_design_discussion.md)。
- **可以跑的：**
  - 单元测试，命令见第 8 节。
  - 只读的小脚本，比如用 `tests/unit/synth.py` 给示例候选造快照，演示 teacher 一步步怎么走。脚本放在会话的 scratchpad，不放进仓库；先自己跑通，再给用户看。
  - 要用 GPU，先用 `nvidia-smi` 挑空闲的卡。
- **不做的：** 不跑训练；不调用 DeepSeek，即不跑 `scripts/run_generation.py --backend claude`。已有的运行记录可以读。
- **用户想改什么：** 先在对话里说清改什么、不改什么。代码改动等用户同意后，按 CLAUDE.md 交给 Codex；设计改动先记入 01 §5，讨论之后再定。

### 1.4 同一目录里的另一个会话

- 由 [04](04_handoff_prompt.md) 开的会话也在这个目录工作，做 PickCube teacher 的 RL 验证与调参，可能正在 GPU 上训练。
- 它有未提交的改动：
  - `vpmkit/rewards/pbrs.py`：加了 `shaping_gamma`、`shaping_scale`、`shaping_clip`、`terminal_phi` 四个参数；
  - `tests/unit/test_pbrs.py`；
  - `scripts/ppo_tune.py` 与 `tests/unit/test_ppo_tune.py`；
  - 07、01 中的段落。
- 不改这些文件，不碰它的进程。往 01 写东西之前，先看它的最新内容。
- 讲 `pbrs.py` 时，说明读的是哪个版本：已提交的（`git show HEAD:vpmkit/rewards/pbrs.py`，75 行），还是工作区的。本文按已提交的版本写。

## 2. 先读的背景（约 15 分钟）

- [00](00_technical_plan.md)：
  - 第 2.1 节：一次运行怎么走；
  - 第 3 节：候选的写法；
  - 第 4 节：运行语义，其中第 4.2 节有 PickCube 的例子，第 4.6 节是 PBRS；
  - 第 8 节：检验；附录 A：名词。
- [02](02_implementation_status.md)：第 8 节记每一步建了哪些文件、要点与用法；第 3、4 节记环境事实与踩过的坑。
- [05](05_implementation_plan.md) 第 3 节：目录结构。
- 结果：
  - [06](06_pickcube_trial.md)：DeepSeek 生成 PickCube teacher 的试跑，第 1 轮通过；
  - [07](07_ppo_check.md)：PPO 与 SAC 的检验；
  - [08](08_teacher_check.md)：teacher 在成功轨迹上的检验。

## 3. 整体与分工

**总览。** Stage1 的代码做三件事：让 LLM agent 为一个 ManiSkill 任务写一个 teacher（称为候选），检查这个候选，再把它变成 RL 的奖励。
- **候选**是一个目录：
  - `stage_graph.yaml` 定义阶段链，每个阶段有守卫（`exit`）和不变量（`invariants`）；
  - `predicates.py` 定义谓词，返回 margin，≥ 0 为真；
  - `progress.py` 给部分阶段写阶段内进度；
  - `bindings.py` 把候选里的对象名绑到仿真里的物体。
- **运行时：** Teacher 每步从适配层拿一份快照，算出全部谓词，按守卫与不变量更新阶段，输出 Φ = (k + p_k)/K。PBRSWrapper 再把 Φ 变成奖励。
- **生成时：** harness 把输入包交给 DeepSeek 版 Claude Code。agent 写候选，自己跑 `./check.sh`（第一层检查）。之后 harness 再跑第一层和第二层（审查 agent），不通过就带着报告让 agent 修改。

**谁写的：**
- Claude 写了 `vpmkit/resources/` 下的四份英文材料：`candidate_api.md`、`example/`、`TASK_template.md` 和 `review_prompt.md`。
- 参照候选 `candidates/reference/PickCube-v1/` 的内容是 Claude 在 M3 的任务说明里规定的，由 Codex 写成文件。它只用作测试夹具和试跑的对照答案，从不给 agent 看。
- 生成的 PickCube teacher 由 DeepSeek 写，在 `outputs/stage1/runs/PickCube-v1/20261026-184803/records/round_1/candidate/`。
- 其余代码由 Codex 按任务说明写，Claude 逐步审查。

## 4. 代码地图

括号里的数字是行号。

### 4.1 候选与接口说明：agent 产出什么

- **[candidates/reference/PickCube-v1/](../../candidates/reference/PickCube-v1/)**：参照候选，五个文件，约 150 行。
  - `stage_graph.yaml`：四个阶段 reach → grasp → carry → settle，各自的守卫与不变量；四条官方对应（`official`）；参数。
  - `predicates.py`：四个谓词 near、grasped、at_goal、arm_static。
  - `progress.py`：只给 reach 写了阶段内进度。
- **生成的候选**（路径见第 3 节）：阶段、守卫和不变量与参照相同，最后一段叫 hold；progress 写了 reach（d0 = 0.3）和 carry（d0 = 0.4）。两者的差别见 06 第 3 节与 08 的 g 项。
- **[candidate_api.md](../../vpmkit/resources/candidate_api.md)**（407 行）：给 agent 的接口说明，也是整套运行时的规格。§3 讲 stage_graph.yaml，§4 世界视图，§5 谓词，§6 progress，§7 绑定，§8 teacher 怎么运行，§9 `./check.sh` 的检查与错误代码。
- **[resources/example/](../../vpmkit/resources/example/)**：虚构任务 PlaceCubeOnPad-v1 的完整示例，包括候选的五个文件，以及 `env_source.py`、`helpers.py`、`scene_inventory.md`。agent 照它的风格写，单元测试也用它。

### 4.2 运行时：候选怎样变成 teacher

这是核心，约 900 行。
- **[teacher.py](../../vpmkit/teacher.py)**（274 行）：`Teacher`。
  - `__init__`（18）：读参数，包括阈值、`progress.<阶段>.<名>` 和 `runtime.debounce`（即 m）；把守卫、不变量和官方对应里的文字编译成文字槽；建 `Automaton`。
  - `step`（231）：一步的更新，顺序见第 5 节。
  - `compute_margins`（158）：对文件里用到的每个谓词实例调用一次谓词，得到 `[N, P]` 的 margin。
  - `_progress_scores` 与 `_stage_progress`（168–179）：阶段有 `progress_<阶段>` 函数就用它。没有就取该阶段守卫中各文字得分的平均：成立的文字记 1，不成立的记 clamp(1 + margin/scale, 0, 1)。
  - `_output`（219）：输出 stage、stage_progress、phi、pred、margin、guidance 六项；最后一个阶段的守卫成立时，progress 记 1。
  - `reset`（204）按 env_idx 重置阶段与计数；`evaluate_offline`（249）离线处理一整条轨迹。
  - `_call`（131）：每次调用候选代码，都检查返回值的形状、类型和设备，以及候选有没有原地改快照。
- **[automaton.py](../../vpmkit/automaton.py)**（54 行）：`Automaton.step`（36）。
  - 当前阶段的某条不变量不成立，它的计数加 1；计数到 m 就回退，几条同时到时取最早的目标。
  - 然后沿链连续前进：守卫成立就进下一段，同一步可以前进几段。
  - 阶段一变，计数清零。去抖只作用于回退，前进没有去抖。
- **[world.py](../../vpmkit/world.py)**（311 行）：
  - `Snapshot`（93）：一步的全部读数，是张量的数据类。内容有各对象的 `BodyState`、桌面高度、成对的抓取与接触力读数，以及 `evaluate()` 的字段（`official`）。
  - `make_views`（308）：给谓词的只读视图 `World`、`ObjectView`、`GripperView`。世界视图读不到 `official`，所以谓词看不到环境的判定。
- **[predicate.py](../../vpmkit/predicate.py)**（91 行）：
  - `@predicate`（53）：谓词的元数据，包括 `desc`、`need_true`/`need_false`（guidance 的模板）、`scale`（progress 用）和阈值参数。
  - `active_thresholds`（29）：用 contextvars 让每个 Teacher 用自己的阈值，几个 Teacher 可以共用一份加载的候选。
  - `signed`（89）：把布尔变成 ±1 的 margin。
- 小文件：
  - [literal.py](../../vpmkit/literal.py)：解析 `not p(a, b)`；
  - [render.py](../../vpmkit/render.py)：把 guidance 渲染成英文句子；
  - [geometry.py](../../vpmkit/geometry.py)：四元数、位姿、盒子的角点；
  - [api.py](../../vpmkit/api.py)：候选唯一能 import 的东西，即 `predicate`、`signed`、`G`；
  - [errors.py](../../vpmkit/errors.py)：错误类型。
- **[candidate/](../../vpmkit/candidate/)** 中负责加载的部分：
  - `schema.py`：`stage_graph.yaml` 的 pydantic 模型；
  - `modules.py` 的 `load_candidate_unchecked`（29）：把候选目录导入成一个新的包，收集谓词、`progress_<阶段>` 函数和 `bind`；
  - `__init__.py` 的 `load_candidate`（15）：先做静态检查，通过了再导入。

### 4.3 接到 ManiSkill 与 RL

- **[adapters/maniskill/](../../vpmkit/adapters/maniskill/)**：
  - `env.py` 的 `make_env`（13）：N > 1 用 GPU 仿真，N = 1 用 CPU；默认 `obs_mode="state"`、`reward_mode="sparse"`。
  - `binding.py`：候选的 `bind(env, api)` 用到的 api，有 `gripper`、`actor`、`site` 三种绑定。
  - `adapter.py` 的 `ManiSkillAdapter`（19）：构造时调用一次 `bind`；`snapshot(info)`（96）每步读一份快照，所有张量都复制出来。
  - `inventory.py`、`helpers_table.py`：生成输入包里的场景清单与 helpers，只在生成流程中用。
- **[rewards/pbrs.py](../../vpmkit/rewards/pbrs.py)**：`PBRSWrapper`，行号按已提交的版本。
  - `reset`（45）：全部重置，或按 `env_idx` 部分重置。Teacher 只重置、只更新被重置的环境，记下它们的 Φ(s)。
  - `step`（62）：奖励 = γΦ(s′) − Φ(s) + success · r_bonus，成功终止时 Φ(s′) 取 0。`info["pbrs"]` 记下 Φ、上一步的 Φ、阶段与塑形项。
- **[ppo_bootstrap.py](../../vpmkit/ppo_bootstrap.py)**（11 行）：`final_bootstrap_mask`，只对截断自举，成功终止不自举。
- **[scripts/ppo_check.py](../../scripts/ppo_check.py)**（490 行）：照官方 `ppo.py` 改写。
  - `main`（426）：环境栈从里到外是 `gym.make` → `PBRSWrapper`（只在 `--reward teacher` 时）→ `FlattenActionSpaceWrapper` → `ManiSkillVectorEnv`。
  - `train`（211）：基本照抄官方。改动在自举的判断，另外记下各阶段所占的比例（`teacher/stage_frac/<阶段>`）。
  - `evaluate`（147）：训练后的确定性评估。
- **[scripts/sac_check.py](../../scripts/sac_check.py)**（486 行）：照官方 `sac.py` 改写；`replay_transition`（104）决定存进回放的 next_obs 与是否自举。
- **[scripts/pbrs_smoke.py](../../scripts/pbrs_smoke.py)**：M5 的冒烟测试与开销测量。
- **[scripts/teacher_check.py](../../scripts/teacher_check.py)**（582 行）：08 的检验。
  - `TeacherObserver`（41）：挂在 PBRS 包装的位置，只记录，不改奖励。
  - `rollout`（97）：跑回合并逐步记录。
  - `candidate_statistics`（232）：08 中 a–f 各项的统计。

### 4.4 检查候选（两层）

- **[candidate/static.py](../../vpmkit/candidate/static.py)**（394 行）：第一层的前三组。
  - 三组是解析、schema 与引用（`_schema`，151）、代码限制（`_restrictions`，347）；入口是 `check_static`（380）。
  - 只读 YAML 和 Python 的语法树，不导入、不执行候选代码。
  - 配套的文件：`codes.py` 是错误代码表；`pyinfo.py` 从语法树读函数签名与默认值；`report.py` 生成报告，其中的 Markdown 就是 agent 运行 `./check.sh` 时看到的。
- **[validate/](../../vpmkit/validate/)**：
  - `layer1.py` 的 `run_layer1`（25）：静态检查通过后，开一个子进程跑运行检查。
  - `run_worker.py` 的 `run_candidate`（120）：8 个环境，种子 0–2，各跑 31 步随机动作。检查绑定、官方字段是否存在、第一个状态、NaN 和返回值的形状。
  - `check_sh.py` 与 `resources/check.sh.template`：写出 agent 在工作区里跑的 `./check.sh`。
- **[review_prompt.md](../../vpmkit/resources/review_prompt.md)**：第二层审查 agent 的提示词。

### 4.5 生成流程（harness）

- **[package/](../../vpmkit/package/)**：生成 agent 的输入包。
  - `strip.py`：从环境源码里删掉奖励函数。
  - `helpers.py`：渲染 helpers.py。
  - `build.py` 的 `build_package`（61）：写出 TASK.md、源码、helpers、场景清单、接口说明、示例与 manifest。TASK.md 的模板是 [TASK_template.md](../../vpmkit/resources/TASK_template.md)。
- **[harness/](../../vpmkit/harness/)**：
  - `run.py` 的 `run_generation`（67）：一轮是生成 → 第一层 → 第二层审查；不通过就带着报告进入下一轮修改，最多 4 轮。每轮的记录写进 `records/round_<n>/`。
  - `backends.py`：`ClaudeCodeBackend`（125）以子进程调用 DeepSeek 版 Claude Code；`ScriptedBackend`（206）供测试用。保存的记录里，像密钥的字段值被抹掉。
  - `review.py`：审查的提示与 JSON 解析。
  - `rundir.py`：建 `workspace/` 与 `records/`。
  - `env.py`：构造子进程的环境变量。
- 命令行入口：`scripts/build_packages.py`、`scripts/run_generation.py`、`scripts/check_candidate.py`。
- 配置在 [configs/default.yaml](../../configs/default.yaml)：轮数、超时、GPU，以及 pbrs 的 γ 与 r_bonus。

### 4.6 测试

- `tests/unit/`：只用 CPU，与模块一一对应。
  - 想弄清运行语义，看 [test_teacher.py](../../tests/unit/test_teacher.py)：`test_carry_slips_near_and_far`（60）把 00 第 4.2 节的情形（搬运中方块滑落，夹爪离得近或远）写成了测试；`test_release_*`（67、86）是松手阶段的例子。这几个测试用的是示例候选。
  - [test_automaton.py](../../tests/unit/test_automaton.py)：回退、连续前进、去抖；`test_pick_slip_near_and_far`（17）是同一个情形在自动机这一层的测试。
  - [test_pbrs.py](../../tests/unit/test_pbrs.py)：逐项相消、部分重置。它在工作区有另一个会话未提交的改动。
  - `synth.py`：造合成快照。
- `tests/fixtures/mutations.py`：把示例候选改坏的 119 种改法，每个错误代码至少一种。
- `tests/integration/`：要 GPU，设了 `VPM_INTEGRATION=1` 才跑。每个环境开一个子进程（`maniskill_worker.py`），因为 SAPIEN 在一个进程里建第二个 GPU 场景会崩溃。

### 4.7 输出目录（不进 git）

- `outputs/stage1/packages/PickCube-v1/`：PickCube 的输入包。
- `outputs/stage1/runs/PickCube-v1/20261026-184803/`：试跑。`records/round_1/` 中有 prompt、生成会话的事件流（`generation.jsonl`）、本轮结束时的候选，以及两层的报告（`layer1.md`、`review.md`）。
- `outputs/stage1/ppo_check/`：07 中 PPO 与 SAC 的各次运行，每次一个目录，有 `config.json`、`train.jsonl`、`eval.json`、`final_model.pt`。`ppo_tune/` 是另一个会话的。
- `outputs/stage1/teacher_check/20261027-002010/report.md`：其中“Recorded traces”一节有 PickCube 回合逐步的阶段、Φ 与 guidance，适合当例子。
- `outputs/stage1/codex/<步骤>/`：Codex 的任务说明、事件流与汇报。

## 5. 训练时的一步：数据怎么流

以 `ppo_check.py --reward teacher` 为例，从 PPO 给出动作到拿到奖励：

1. `ManiSkillVectorEnv.step` 调用里面的 `PBRSWrapper.step`（pbrs.py 62）。它先让 ManiSkill 走一步，拿到 `obs`、`terminated`（PickCube 中等于 success）、`truncated` 和 `info`。
2. `ManiSkillAdapter.snapshot(info)`（adapter.py 96）读一份快照：夹爪与各物体的位姿、速度、尺寸，夹爪开度，手臂关节速度，抓取与接触力读数，`evaluate()` 的字段。
3. `Teacher.step`（teacher.py 231）：
   1. `compute_margins`：算出 near(g, cube)、grasped(g, cube)、at_goal(cube, goal)、arm_static(g) 四个实例的 margin；
   2. `_literal_truth`：margin ≥ 0 为真，取反的文字再翻转；
   3. `Automaton.step`：先查当前阶段的不变量，决定是否回退；再沿守卫连续前进；
   4. `compute_progress`：算每个阶段的 p_k；
   5. `_output`：取当前阶段的 p_k，算 Φ = (k + p_k)/K 与 guidance。
4. 回到 `PBRSWrapper.step`：成功终止时 Φ(s′) 取 0；奖励 = γΦ(s′) − Φ(s) + success · r_bonus；再把 Φ(s′) 存为下一步的 Φ(s)。
5. `ManiSkillVectorEnv` 发现有回合结束，当场重置这些环境，调用 `PBRSWrapper.reset(options={"env_idx": ...})`。Teacher 只重置这些环境，在新回合的初始状态上算 Φ(s)。包装套在里面，所以截断那一步的 Φ(s′) 是在重置之前算的（00 第 4.6 节）。
6. PPO 算优势时，只对截断的回合用 critic 自举，成功终止不自举（ppo_bootstrap.py）。

**PickCube 的例子**（生成的 teacher，K = 4，γ = 0.8）：
- **reach（k = 0）：** p = 1 − d/0.3，d 是 TCP 到方块中心的距离，p 截在 [0, 1]。d = 15 cm 时 Φ = (0 + 0.5)/4 = 0.125；30 cm 以外 Φ = 0。
- **进入 grasp：** d 小于方块的半对角线加 2 cm（约 5.5 cm）时 near 成立，同一步前进到 grasp。
- **grasp（k = 1）：** 守卫 grasped 是布尔谓词，margin 为 ±1，scale = 1，这一段没有 progress 函数。没抓住时 p = clamp(1 − 1, 0, 1) = 0，所以 Φ 一直是 0.25（08 第 3 节第 2 条）。
- **carry（k = 2）：** p = 1 − 方块到目标的距离/0.4；离目标 20 cm 时 Φ = (2 + 0.5)/4 = 0.625。抓取读数断开一步（m = 1），不变量 grasped 不成立，退回 reach；near 仍成立，同一步又进到 grasp，Φ 掉到 0.25。08 第 2 节 b 项的 180 次就是这种情况。
- **hold（k = 3）：** 守卫 arm_static 成立时最后一段完成，p = 1，Φ = 1。这时环境的 success（at_goal 且 arm_static）也成立，回合终止，Φ(s′) 取 0，这一步的奖励是 −Φ(s) + r_bonus。
- **奖励的量级【推导】：**
  - 在 reach 段离方块 15 cm 处，原地不动一步得 0.8 × 0.125 − 0.125 = −0.025；靠近 1 cm 得 0.8 × 0.1333 − 0.125 ≈ −0.018。
  - 在 grasp 段停一步得 −(1 − 0.8) × 0.25 = −0.05。

## 6. 阅读路线

### 6.1 最快：teacher 在训练时做什么（约 600 行）

1. 参照候选的 `stage_graph.yaml`：一个 teacher 长什么样。
2. `teacher.py` 的 `step` 与 `_output`，加上 `automaton.py`：每一步怎么算谓词，怎么回退和前进，Φ 怎么来。
3. `rewards/pbrs.py`：Φ 怎么变成奖励。
4. `ppo_check.py` 的 `main` 与 `evaluate`：环境怎么一层层套起来，训练后怎么评估。`train` 照抄官方 `ppo.py`，可以跳过。

### 6.2 完整的顺序

1. **候选**（第 4.1 节）：先看参照候选的五个文件，再看 `candidate_api.md` 的 §3–§8，最后看示例。
2. **运行时**（第 4.2 节）：`teacher.py` → `automaton.py` → `world.py` → `predicate.py` 与几个小文件 → `candidate/schema.py`、`modules.py`。对照 00 第 3、4 节。
3. **接到 ManiSkill 与 RL**（第 4.3 节）：`adapter.py` → `pbrs.py` → `ppo_check.py`、`sac_check.py`。
4. **检查候选**（第 4.4 节）：`static.py` → `layer1.py` → `run_worker.py` → `review_prompt.md`。对照 00 第 8 节。
5. **生成流程**（第 4.5 节）：`TASK_template.md` → `package/build.py` → `harness/run.py` → `backends.py`，再看试跑的记录 `records/round_1/`。对照 00 第 5–7 节。

测试可以和对应的模块一起看。

## 7. 常被问到的地方

- **grasp 段的 Φ 为什么不变：** 默认 progress 的公式在 teacher.py 168–179，grasped 的 ±1 margin 来自 `signed`。设计规则是布尔守卫的阶段不写 progress（01 §4.2）。
- **m（去抖）在哪里：** automaton.py 36–54；参数是 `runtime.debounce`，默认 1（teacher.py 43–47）。
- **包装为什么套在 ManiSkillVectorEnv 里面：** 见 00 第 4.6 节。套在外面的话，截断那一步的 Φ(s′) 会算在重置后的状态上。
- **成功终止为什么不自举：**
  - 理由见 00 第 4.6 节最后两条。ManiSkill 官方 PPO 对成功终止也自举，这里改了。
  - 代码在 pbrs.py 67 与 `ppo_bootstrap.py`；SAC 的在 `replay_transition`。
- **阈值与参数怎么改：** 默认值在 `stage_graph.yaml` 的 `params`；`Teacher(..., params={...})` 可以覆盖，越出声明的范围会报错（teacher.py 31–42）。
- **候选能写什么、不能写什么：** 见 candidate_api.md §5、§9；代码限制在 static.py 的 `_restrictions`。
- **官方对应有什么用：**
  - 它把候选的文字和环境 `evaluate()` 的字段对上。
  - 运行检查只核对字段存在（run_worker.py 156）。
  - 逐步是否一致，由 teacher_check.py 的 `official_correspondence`（203）统计，结果见 08 的 e 项。
- **部分重置：** 见 pbrs.py 的 `reset` 与 `Teacher.step` 的 `env_mask`；测试是 `test_masked_step_*`（test_teacher.py 197、205）。
- **离线重标一整条轨迹：** `Teacher.evaluate_offline`（teacher.py 249），Stage2、Stage3 会用。
- **重置后的抓取读数是旧的：** 02 第 4 节第 12 条，08 第 2 节。

## 8. 命令

都用 vpm-mani 的 Python，系统自带的 python3 是 3.8。没有 pytest，用标准库 unittest。

单元测试（CPU）：

```bash
cd /home/zxh/projects_dir/vpm-claude && mkdir -p outputs/tmp && ulimit -c 0 && TMPDIR=$PWD/outputs/tmp XDG_CACHE_HOME=$PWD/outputs/cache MS_ASSET_DIR=$PWD/outputs/maniskill CUDA_VISIBLE_DEVICES="" /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/unit -t . -v
```

- 只跑一个模块时，把 `discover -s tests/unit -t .` 换成模块名，例如 `tests.unit.test_teacher`。
- 全部单元测试里包括另一个会话未提交的 `test_ppo_tune.py` 和改过的 `test_pbrs.py`。它们失败，不一定是已提交代码的问题。
- 集成测试要 GPU，命令见 02 第 8 节“M2 的要点”。

## 9. 现状（2026-10-27）

- 分支 `stage1-impl`，没有推送。代码的提交按时间顺序：adcd518（M1a）、97bc833（M1b）、c423943（M2）、96ad2d5（M3）、c1a3580（M4a）、077ac58（M4b）、ec70e54（M5）、a2be90f（PPO 接入检查）、58117bd（第三轮检验的代码）。其后是 7db8f87（只改文档），以及 2026-10-27 的一次提交：`scripts/teacher_check.py` 与它的测试、08、09、10，以及 02 的相关改动。
- 另一个会话未提交的：见第 1.4 节。
