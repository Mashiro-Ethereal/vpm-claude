# Stage1 实现计划

> **用途：** 说明怎样把 [00 技术方案](00_technical_plan.md) 实现出来：分几步，每步交给 Codex 做什么，我怎么验收，什么时候停下来问你。做什么以 00 为准，本文只管怎么执行。
>
> **状态（2026-10-21）：** 已确认。第 10 节的三处实现细节你全部同意，已写进 00（第 2.1、2.4、3.2–3.4、7.1、7.2、7.5、8.2 节与附录 A）。同日你又定：先在 PickCube 一个任务上走通全流程（包括生成），再扩展到其余 15 个；示例改用虚构的典型抓放任务（00 第 6.4、10.3 节）。第 1–9 节已随之改写。“准备”一步已做完（第 4.1 节），你已看过并同意。2026-10-26 起由 PickCube 试跑会话执行：M1a 已提交（adcd518，第 4.2 节），M1b 已提交（97bc833，第 4.3 节）；M2 已提交（c423943，第 5 节）；M3 已提交（96ad2d5，第 6 节），参照候选你已看过同意（01 §4.14）；TASK.md 的模板已提交（5a7691d）；M4a 已提交（c1a3580，第 7.1 节）；审查提示词已提交（5351ba4）；M4b 已提交（第 7.2 节）；PickCube 试跑等你批准。

## 1. 总体安排

| 步骤 | 内容 | 谁做 | 用 GPU | 做完后你要做的 |
| --- | --- | --- | --- | --- |
| 准备 | 写 candidate_api.md（接口说明）和示例（虚构的抓放任务），英文 | 我 | 否 | 看一眼示例 |
| M1a | 运行时：世界视图、谓词、自动机、Teacher | Codex | 否 | — |
| M1b | 候选的静态检查：schema、加载、AST 限制 | Codex | 否 | 看汇报 |
| M2 | ManiSkill 适配层，先只做 PickCube | Codex | 是 | — |
| M3 | PickCube 参照候选；第一层四项；`check.sh` | Codex（参照候选的规格我写） | 是 | 看一眼参照候选 |
| M4a | 输入包生成（先只做 PickCube 的） | Codex（TASK.md 的设计规则我写） | 是 | — |
| M4b | harness 与第二层审查；PickCube 试跑 | Codex（审查的提示词我写） | 是，调用 DeepSeek | 批准试跑；在你的终端跑一次；看对比报告 |
| M5 | PBRS 奖励包装；开销测试 | Codex | 是 | — |
| 扩展 | 适配层补读数、下载资产；其余 15 个任务分六组生成 | Codex、harness | 是，调用 DeepSeek | 看过试跑结果再定；每组结束看汇报 |

- M1–M5 先只在 PickCube 上走通（包括生成），你看过结果，再扩展到其余 15 个任务（第 9 节）。
- 各步依次进行，后一步要用前一步的代码。M5 只依赖 M1、M2，可以提前做，但为了集中审查，仍按顺序做。
- 00 中的 M1、M4 各拆成两次交给 Codex，每次的范围小一些，审查也容易。

## 2. 每一步怎么做

- **分工：** 我写规格和任务说明、审查、跑测试、向你汇报；Codex 写代码和测试。
- **我自己写的四份英文材料：** candidate_api.md 与示例（M1 之前）、TASK.md 的模板与设计规则（M4a 之前）、第二层审查的提示词（M4b 之前）。它们既是给 agent 看的文字，也是 Codex 实现时的规格，所以由我先写定，再交出去。
- **每一步的流程：**
  1. 写任务说明。任务说明要自含：目标、要建的文件、接口、要通过的测试、运行命令、汇报格式，并摘录 00 的相关章节。
  2. 交给 Codex。用 GPU 的步骤关沙箱：交出去前工作区要干净，用 nvidia-smi 挑空闲的卡；只改项目内的文件，不装包，不改 conda 环境与 ManiSkill。
  3. 审查：自己重跑全部测试；逻辑代码（自动机、Teacher、各项检查、harness 的轮次）逐行看 diff；对照 00 逐条核对。
  4. 不通过，就把具体问题交回同一个 Codex 会话；返工两次仍不行，停下来告诉你。
  5. 通过后向你汇报，你同意再提交，每步一个提交。
- **测试的约定（00 第 10.1、10.2 节）：** 用 vpm-mani 的 Python 和标准库 unittest。单元测试放在 `tests/unit/`，用 CPU 就能跑；集成测试放在 `tests/integration/`，用环境变量开关，每个用 GPU 的环境开一个子进程。命令前加 `ulimit -c 0`，`XDG_CACHE_HOME` 指到 `outputs/cache`。

## 3. 代码结构

```text
vpmkit/
  world.py             世界快照与视图：谓词与 progress 只能从这里读状态
  geometry.py          几何工具 G：四元数（wxyz，与 ManiSkill 相同）、位姿运算、坐标变换、包围盒
  predicate.py         @predicate 装饰器与谓词的元数据
  literal.py           文字的解析：p(a, b) 与 not p(a, b)
  automaton.py         线性链自动机的批量更新（00 第 4.2 节）
  teacher.py           Teacher：谓词实例 → 自动机 → progress、Φ、guidance
  render.py            guidance 渲染成英文
  candidate/           候选的 schema（pydantic）、加载、各项检查、AST 限制、报告
  adapters/maniskill/  环境创建、绑定接口、张量快照、场景清单、辅助函数对照表
  validate/            第一层（四项）、运行检查的子进程、第二层（提示词与解析）
  package/             输入包生成：删奖励函数、TASK.md、场景清单、manifest
  harness/             运行目录、环境变量、Claude Code 后端与脚本后端、轮次、记录
  rewards/pbrs.py      PBRS 奖励包装
  resources/           candidate_api.md、示例（example/）、TASK.md 的模板与设计规则、第二层的提示词
candidates/reference/PickCube-v1/   PickCube 参照候选（测试样例与试跑的答案，不进输入包）
configs/default.yaml   轮数、max-turns、每轮的时间上限、K、显卡、路径
scripts/               build_packages.py、check_candidate.py（check.sh 调用它）、run_generation.py、summarize_runs.py
tests/unit/  tests/integration/  tests/fixtures/（各类错误的候选；合法的用示例）
```

## 4. M1 核心（两次交给 Codex，都不用 GPU）

### 4.1 准备：candidate_api.md 与示例（我写）

- **candidate_api.md：** 按 00 第 3、4 节和第 8.2 节，写文件格式、YAML 写法、谓词与 progress 的写法、运行语义和静态规则。绑定一节先写占位，M2 之后按实际接口补全。M1 的测试要覆盖它写下的每条规则。
- **示例：** 按 00 第 6.4 节，虚构的典型抓放任务（抓起方块、放到目标垫上、松手）：按 ManiSkill 风格写的虚构 `env_source.py`（含 `evaluate()`）、一小段场景清单、完整的候选（`stage_graph.yaml`、`bindings.py`、`predicates.py`、`progress.py`、`notes.md`）。它严格遵守每一条设计规则；绑定先按设想的接口写，M2 之后核对。写完请你看一眼：agent 会照它的风格写。
- **完成情况（2026-10-21）：** 两者都已写好，在 `vpmkit/resources/`：`candidate_api.md` 共 10 节；`example/` 中有 `env_source.py`、`helpers.py`、`scene_inventory.md` 和 `candidate/`。写的时候定下的接口细节已写进 00（附录 B），理由见 01 §4.12。自查结果见 00 第 6.4 节。你已看过并全部同意，其中 `near` 的写法和 grasp 的不变量按讨论改过（01 §4.12 第 1、9 项）。
- **留给后面几步的：**
  - M1a、M1b 照 candidate_api.md 实现，字段名、签名与错误代码都以它为准；
  - M2 之后核对它的绑定一节（第 5 节）；
  - M2 生成场景清单、M4a 生成 `helpers.py`，都照示例中的格式。

### 4.2 M1a 运行时

- **内容：** world、geometry、predicate、literal、automaton、teacher、render；参数覆盖（供 BO 用）；快照的保存与读取（供离线重算用）。
- **关键接口**（以 candidate_api.md 第 3–8 节为准，任务说明摘录它）：
  - 谓词：`@predicate(desc, need_true, need_false, scale)`，签名 `f(w, *对象, **阈值) -> margin [N]`；`vpmkit.api` 导出 `predicate`、`G`、`signed`。
  - 对象视图：`pos`、`quat`、`pose`、`lin_vel`、`ang_vel`、`half_size` `[N, 3]`、附加属性；带关节的物体另有 `joint_pos`、`joint_vel`、`joint_limits`。夹爪视图：TCP 的位姿与速度、`width`、`max_width`、`arm_qvel`。世界视图：`table_z`、`grasping(g, o)`、`contact_force(a, b)`、`batch_size`、`device`。不提供按名字取对象的接口。
  - Teacher：`reset(env_idx, stage=None)`；`step(world)` 返回 00 第 4.4 节的六个字段；`evaluate_offline(快照序列, 初始阶段)`；`render(输出, i)`。
- **测试**（用合成的快照，在 CPU 上跑）：
  - 00 第 4.2 节的例子逐个写成测试：PickCube 搬运中方块滑落（夹爪还近，停在 grasp；已经远了，停在 reach）；StackCube 松手。
  - 示例的 grasp：爪子离开方块附近（`near` 不成立），回到 reach，guidance 是“靠近方块”；还在附近、没抓住时停在 grasp。
  - 自动机的规则：同一步连续前进；几条不变量同时不成立，回到最早的阶段；新进入的阶段从下一步才查不变量；m = 2 时的计数与清零；按 env_idx 重置；从存下的阶段开始。
  - 最后一个阶段的条件全部成立时，guidance 为空、progress 为 1。
  - 取反的真值与 margin；默认 progress 的公式；布尔谓词的 margin 为 ±1。
  - 批量：N 个环境处在不同阶段时，结果与逐个环境算的相同；离线一次算完全部帧，结果与逐步算的相同。
  - 渲染：代入显示名、句首大写、取反时用 need_false 模板。
  - 示例（`resources/example/`）的谓词与 progress 在合成快照上运行：形状为 `[N]`，没有 NaN 或 Inf。
- **验收：** 测试全部通过；`automaton.py`、`teacher.py` 逐行看。
- **分工调整（2026-10-26，只改分工，不改设计）：** `stage_graph.yaml` 的 pydantic 模型和“不做检查的候选加载”（`load_candidate_unchecked`）提前放进 M1a，因为 Teacher 和它的测试要用；M1b 只做静态检查、报告和先检查后加载的 `load_candidate`。
- **完成情况（2026-10-26）：** Codex 一次做完，审查通过。新建 `vpmkit/` 下 13 个文件（world、geometry、predicate、literal、automaton、teacher、render、errors、api 与 `candidate/` 的 schema 和加载）与 `tests/unit/` 下 9 个文件。我重跑测试：68 个全部通过，没有跳过；几何工具与 ManiSkill 自己的函数在 1200 组随机四元数、位姿和接近万向锁的角度上一致。`automaton.py`、`teacher.py` 逐行核对，符合 00 第 4.2 节。另用示例走了一遍完整回合（靠近、抓取、搬运、松手、被碰落后回退），阶段、Φ 与 guidance 都符合预期。CPU 上 N = 4096 时每步约 3.5 ms。任务说明见 [briefs/m1a.md](briefs/m1a.md)。

### 4.3 M1b 候选的静态检查

- **内容：** 候选目录的检查与先检查后加载（pydantic 模型与不做检查的加载已在 M1a 写好）；00 第 8.2 节第一层的第 1–3 项（解析；schema 与引用，含四项新检查；AST 限制）；报告用 JSON，附 Markdown 摘要，每条问题有错误代码、位置和说明。
- **测试：** 示例（`resources/example/candidate/`）作合法候选，不误报；`tests/fixtures/` 中，candidate_api.md 第 9.1–9.3 节的每个错误代码至少一个。candidate_api.md 中只有格式模板和片段，完整的 YAML 就是示例的 `stage_graph.yaml`。
- **验收：** 每类错误都报对，代码和位置也对；合法候选不误报。
- **完成情况（2026-10-26）：** Codex 一次做完，审查通过。新建 `vpmkit/candidate/` 下的 `codes.py`（34 个错误代码的登记表）、`pyinfo.py`（从语法树读出谓词、progress 与 `bind` 的签名和装饰器参数）、`report.py`（JSON 与 Markdown 报告）、`static.py`（第 1–3 组共 29 条规则，按组门控），以及 `tests/fixtures/mutations.py`（把示例改坏的 119 种改法，每个错误代码至少一种，断言代码集合与位置都对）与 `tests/unit/test_static.py`；`load_candidate` 先做静态检查，通过后才导入候选代码。改了 M1a 的三处：schema 要求 `objects`、`stages` 非空；`errors.py` 加 `CandidateCheckError`；`candidate/__init__.py` 导出新接口。静态检查从不导入或执行候选代码（有测试：`predicates.py` 顶层写 `raise` 也不触发）。我重跑测试：96 个全部通过；逐行核对了 `static.py`、`pyinfo.py`；另测了 Codex 测试之外的几种情形（文字里的多余空格、YAML 中不加引号的 `2e-2`、多处错误同时出现），结果都对。任务说明见 [briefs/m1b.md](briefs/m1b.md)。

## 5. M2 ManiSkill 适配层（用 GPU）

先只做 PickCube 用到的部分；其余任务的读数扩展时再补（第 9 节）。快照的 schema 在 M1a 已按 00 第 3.6 节留出全部字段，补读数时不用改 M1。
- **内容：**
  - 环境创建：N > 1 时用 physx_cuda；资产目录指到 `outputs/` 下。
  - 绑定接口：actor、site、夹爪末端；附加属性可以是每步重读的函数。
  - 每步的张量快照。
  - 场景清单：包括 `evaluate()` 用到的属性的实际值。做法是用 `ast` 找出 `evaluate()`（含内嵌函数）读到的 `self.<属性>`，再从运行中的环境读值，不需要逐任务手写。
  - 辅助函数对照表：PickCube 的 `evaluate()` 用到的条目（`is_grasping`、`Panda.is_static`）。
- **集成测试：** PickCube 开一个子进程，按场景清单绑定全部动态物体，检查读数的形状、设备和数值是否合理；`w.grasping` 与 `agent.is_grasping` 一致；场景清单中 `goal_thresh` 的实际值正确（按机器人取，见 01 §4.3）。
- 场景清单照示例 `resources/example/scene_inventory.md` 的格式生成。
- **M2 之后：** 我按实际接口补全 candidate_api.md 的绑定一节，并核对示例中绑定的写法；核对完删去该节开头的提醒注释。
- **完成情况（2026-10-26）：** Codex 一次做完，审查通过。新建 `vpmkit/adapters/maniskill/` 下的 `env.py`（`make_env`）、`binding.py`（`api.gripper / actor / site` 与校验）、`adapter.py`（`ManiSkillAdapter.snapshot()`）、`inventory.py`（`scene_inventory()`）、`helpers_table.py`（辅助函数对照表，PickCube 两条），`errors.py` 加 `BindingError`；单元测试 3 个文件，集成测试 `tests/integration/`（每个环境一个子进程，`VPM_INTEGRATION=1` 才跑）。我重跑：单元测试 110 个、集成测试 4 个全部通过（集成 34 秒）。集成测试把每项读数与 ManiSkill 自己的读法对照（TCP 位姿与速度、手臂关节速度、开度、抓取、接触力、隐藏时 goal_site 的真实位姿），并用脚本控制机械臂抓方块：第 51 步抓住，此后 20 步保持，每一步 `w.grasping` 都与 `agent.is_grasping` 相同，抓住时接触力为正。桌面高度：桌子的碰撞体顶面在 8 个环境中都正好是 z = 0。生成的场景清单在 `outputs/stage1/m2/scene_inventory_PickCube-v1.md`。
- **收尾（2026-10-26）：** 照实际接口补全了 candidate_api.md 第 4.3、7 节，删去提醒注释；示例的绑定写法与实际接口一致，不用改。补全时定的三处接口细节见 00 第 3.6 节、附录 B 与 01 §4.13，你已同意。任务说明见 [briefs/m2.md](briefs/m2.md)。

## 6. M3 参照候选与第一层（用 GPU）

- **PickCube 参照候选：** 我写规格（00 第 3.2 节的 YAML、各谓词照 `evaluate()` 的公式、模板、notes.md 的四段），Codex 写代码。它是第一层在真实环境上的测试样例，也是 PickCube 试跑的答案，所以我逐行审查，官方对应也照第二层的做法对照源码逐项核对。它不放进任何输入包。
- **第一层的运行检查：** 在一个 GPU 子进程中建一个环境（8 个并行环境），用 3 个种子各重置一次，各走 30 步随机动作，检查全部谓词实例、所有阶段的 progress 和自动机更新：不报错、形状为 `[N]`、没有 NaN 或 Inf。只建一次环境，避开“同一进程第二次建 GPU 场景会崩溃”的问题。
- **串起来：** 把第一层的四项串成 `scripts/check_candidate.py`，并写好 `check.sh` 的模板。
- **测试：** 参照候选通过第一层；几个故意写坏的变体（形状不对、新建的张量不在 GPU 上、除以零出 NaN）被运行检查拦下。
- **需要你：** 看一眼参照候选。
- **完成情况（2026-10-26）：** Codex 一次做完，审查通过。新建参照候选 `candidates/reference/PickCube-v1/`（照我写的规格，见 [briefs/m3.md](briefs/m3.md) 末尾）；`vpmkit/validate/` 下的 `run_worker.py`（运行检查：一个 GPU 环境，8 个并行环境 × 3 个种子 × 31 个状态 = 744 个状态；第一个状态上把每个谓词、每段 progress 分开算，一次报出全部出错的函数，之后遇到第一个错误就停；traceback 只保留候选文件里的帧）、`layer1.py`（`run_layer1`：静态检查通过后在子进程中跑运行检查，沿用调用方的 `CUDA_VISIBLE_DEVICES`，禁止写崩溃文件）、`check_sh.py` 与模板 `vpmkit/resources/check.sh.template`；`scripts/check_candidate.py`。`Report` 加 `layer1_passed`（四组都通过）与用时，Markdown 的首行按它写；Teacher 把 progress 的计算拆成两个辅助函数供运行检查逐段调用，行为不变。我重跑：单元测试 123 个、集成测试 9 个全部通过；照第二层的做法对照 `evaluate()` 核对了参照候选；在只有 HOME、PATH、LANG、`CUDA_VISIBLE_DEVICES` 的环境下跑 `check.sh`：参照候选通过，冷启动共 12.8 秒（远在 agent 的 shell 工具默认的 2 分钟以内），写坏的候选一次报出两个问题，带参数时拒绝运行。

## 7. M4 生成（用 GPU；M4b 调用 DeepSeek）

### 7.1 M4a 输入包

先只为 PickCube 生成输入包；删奖励函数的逻辑在 16 个源文件上都测（只读源码，不用建环境）。
- **先由我写：** TASK.md 的模板与设计规则（英文，00 第 5 节）。
- **内容：**
  - 删奖励函数：用 `ast` 定位行号，从原文删去；剩下的文本中还有 reward，就报错；
  - TASK.md：环境名、文档字符串、回合上限、要产出什么、设计规则、怎么运行检查；
  - helpers.py（照示例 `resources/example/helpers.py` 的格式）、scene_inventory.md、`example/`（示例，取自 `vpmkit/resources/`）、manifest.json（各文件的来源、版本、哈希）；
  - candidate_api.md 的绑定一节还留着 M2 的提醒注释时，拒绝生成。
- **测试：**
  - 已核对过的 5 个源文件，删完后的行数与记录一致：216→186、144→111、186→145、360→300，StackPyramid 不变；
  - PullCubeTool、TurnFaucet、PushT 被拦下（00 第 6.2 节）；
  - 同一任务生成两次，哈希相同。
- 这三个任务怎么处理，扩展到其余任务时再定。
- **完成情况（2026-10-26）：** TASK.md 的模板由我先写好（`vpmkit/resources/TASK_template.md`，你定保留说明之后流程的那段，01 §4.15）。Codex 一次做完，审查通过：新建 `vpmkit/package/` 下的 `strip.py`（删奖励函数、查残留）、`helpers.py`（照示例格式渲染辅助函数对照表）、`build.py`（`build_package`，在子进程中生成场景清单，先在临时目录建好再整体换上，manifest 不含时间等随运行变化的内容），以及 `scripts/build_packages.py`。我重跑：单元测试 135 个、集成测试 10 个全部通过。16 个源文件的删除结果与记录一致（PickCube 216→186、LiftPegUpright 144→111、StackCube 186→145、PegInsertionSide 360→300，StackPyramid、PlugCharger、AssemblingKits 不变；PullCubeTool、TurnFaucet、PushT 被拦下，其余 8 个通过）。PickCube 的包在 `outputs/stage1/packages/PickCube-v1/`，`package_sha256` = 611246a2…cd29；两次生成的文件与哈希完全相同。我逐个文件看过：TASK.md 填对了，`env_source.py` 186 行、不含 “reward”，`example/` 与 `candidate_api.md` 与仓库中的原件逐字节相同，场景清单与 M2 生成的相同。任务说明见 [briefs/m4a.md](briefs/m4a.md)。

### 7.2 M4b harness 与第二层

- **先由我写：** 第二层审查的提示词（英文，00 第 8.3 节的 a–j 和 JSON 格式）。
- **内容：**
  - 运行目录与由代码构造的环境变量；
  - Claude Code 后端：00 第 7.3 节的参数、stream-json 的解析、会话编号，成败看退出码与 `is_error`；
  - 脚本后端；
  - 轮次：第一层 → 第二层 → 修复，最多 4 轮；harness 故障重试 2 次；
  - 记录；第二层的调用与 JSON 解析。
- **测试（不调用 DeepSeek）：**
  - 用脚本后端在 PickCube 的输入包上跑完整的循环：直接给出 PickCube 的参照候选，一轮通过；先给出写坏的候选，第一层不过，修复轮再给出好的，最后通过；
  - 参数与环境变量的单元测试，其中检查不含 `CLAUDE*`、`ANTHROPIC*`；
  - 第二层输出的解析：合法、缺字段、不是 JSON 三种情况。
- **完成情况（2026-10-26）：** 审查提示词由我先写好（`vpmkit/resources/review_prompt.md`，你定报错误须引用代码行、拿不准的降为提醒，01 §4.16）；取值你定（生成 80 turn、每轮 40 分钟，审查 40 turn、15 分钟，01 §4.17）。Codex 写好 `vpmkit/harness/`（`env.py`、`rundir.py`、`backends.py`、`review.py`、`run.py`）、`configs/default.yaml` 与 `scripts/run_generation.py`；我审查后交回两次：第一次改四处（超时时结束整个进程组；`run_generation.py` 启动时把缓存、资产与临时目录指到 `outputs/`；审查结果的宽松解析；上一轮的错误保留到下一次审查），第二次让记录中形似密钥的字段值抹成 `[REDACTED]`（与 10-21 实测时一样）。两次都一次改好。我重跑：单元测试 166 个、集成测试 15 个全部通过；从只有最少环境变量的 shell 用脚本后端跑完整流程，参照候选一轮通过。任务说明见 [briefs/m4b.md](briefs/m4b.md)（含两次返工的说明）。
- **PickCube 试跑（调用 DeepSeek，开始前问你）：** 用 PickCube 的输入包端到端跑一次。“走通”的标准见 00 第 10.3 节：harness 把生成和两层检查完整走完一遍，候选通过与否都算，暂不考虑候选的性能。从你的终端和从我这边各启动一次，确认两边都能登录、工具限制一致、都能走完。生成的候选与参照候选逐项对比：阶段划分、守卫与不变量、官方对应与阈值、progress、模板、notes.md。我写一份对比报告，你看过再定怎么扩展。

## 8. M5 PBRS 奖励包装（用 GPU）

- **内容：** 先用 PBRS 包装包住 ManiSkill 环境，再套 `ManiSkillVectorEnv`，与官方 PPO 的 `FlattenActionSpaceWrapper` 同一层（00 第 4.6 节）。套在 `ManiSkillVectorEnv` 外面不行：它在 step 中当场重置结束的环境，截断那一步的 Φ(s′) 会算在重置后的状态上。包装要做的：
  - 每步用 Teacher 算一次 Φ 并复用；
  - 奖励为 γΦ(s′) − Φ(s) 加成功奖励；成功终止时 Φ(s′) 取 0；超时截断时照常用 Φ(s′)，由 RL 算法自举；
  - 部分重置的环境，按 env_idx 重置阶段。
- **测试：**
  - 单元测试：用合成的 Φ 序列，检查一个回合的塑形总和等于 −Φ(s₀) 加上终止项，并覆盖截断的情形；
  - 不训练的冒烟测试：用 PickCube 参照候选，随机动作跑几个回合，检查形状与逐项相消；至少经过一次自动重置，核对截断那一步的 Φ(s′) 用的是回合结束时的状态。
- **顺带测一次开销：** N 取 1024 或 2048 时，比较 teacher 每步的耗时与仿真每步的耗时，用来检验 00 第 12 节的【假设】。

## 9. 扩展到其余 15 个任务（PickCube 走通之后）

- 前提：你看过 PickCube 试跑的结果，同意扩展。
- 先补适配层（00 第 9.4 节）：带关节物体的关节读数（TurnFaucet）、没有夹爪的末端（PushT）、各并行环境尺寸不同的物体（PickSingleYCB、PegInsertionSide）、其余任务用到的辅助函数对照表条目，以及各任务的读数集成测试。PickSingleYCB、AssemblingKits、TurnFaucet 要下载资产包，先问你。
- 定 PullCubeTool、TurnFaucet、PushT 的输入包怎么处理（00 第 6.2 节）。
- 开始生成前问你，因为要调用 DeepSeek。
- 按 00 第 9.1 节的六组顺序。同一组的任务在空闲的卡上并行跑，每个运行占一张卡，最多同时 3 个。
- 每组跑完，我汇报一次：每个任务是否通过、用了几轮、各轮的错误类别、有没有 harness 故障、需不需要人工介入。发现的基础设施问题（如适配层缺了读数、提示词说得不清），先交 Codex 修好，再跑下一组。
- 运行失败的任务（K = 1 时，就是这个任务失败），按 00 第 8.4 节由人修到通过，记为一次人工介入，保存修改的 diff 与理由。
- 全部跑完，写一份 Stage1 的结果汇总，交给 Stage2。

## 10. 三处实现细节【决定，2026-10-21，你全部同意，已写进 00】

1. **运行目录拆成两个：**
   - `workspace/`：agent 的工作目录，放输入包副本、`candidate/`、`check.sh`，在这里 `git init`；
   - `records/`：本次运行的记录，放在 agent 能访问的范围之外。

   理由：agent 有 `Write(./**)` 的许可，记录放在它的工作目录里，可能被改掉。这会改动 00 第 7.2 节的写法。
2. **AST 限制补几条安全项：** 候选中所有 `.py` 文件不许读写文件、起进程、联网，不许用 `exec`、`eval`、`__import__` 和双下划线属性。理由：候选是 agent 写的代码，会在我们的进程里执行。谓词与 progress 的 import 白名单 00 已经定了，这几条主要针对 `bindings.py`。
3. **实现层面的四个约定：**
   - progress 的参数命名为 `progress.<阶段名>.<参数名>`；
   - 模板的占位符用谓词的参数名，如 `{g}`、`{o}`，渲染时句首大写；
   - `not p` 的真值是 p 的真值取反，margin 取 −margin(p)；正好落在阈值上时，算 p 成立；
   - 阈值的默认值同时写在函数签名和 `params` 中时，两处必须相同，否则第一层报错。

## 11. 风险

- **Codex 的结果与 00 不符：** 每步对照 00 审查；返工两次仍不行，就停下来。
- **资产下载、DeepSeek 的耗时与费用：** 下载前、生成前都问你；生成按组进行，随时可以停。
- **适配层满足不了某个任务的读数需求：** 在生成那一组之前补上，记在 02。
- **真实运行时 DeepSeek 的表现与实测不同**（如上下文过长、工具调用出错）：先在 PickCube 试跑中暴露出来，再调提示词或参数。
