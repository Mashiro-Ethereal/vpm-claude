# Stage1 实现现状（2026-10-26）

> **用途：** 交接用。说明 `stage1-impl` 分支上的代码现状、重写时要用到的环境事实和经验，以及委托 Codex 的做法。设计结论以 [技术方案](00_technical_plan.md) 为准，本文只记实现。
>
> **现状：** 2026-10-21，议程全部定完（G1 推迟），[技术方案](00_technical_plan.md) 定为执行标准。此前写的全部 Stage1 实现代码已删除，理由（你的意见）：那些代码写在逐点讨论之前，基本都要大改，不如重写。重写按 00 第 10.3 节的实现阶段 M1–M5 进行，分步与验收见 [05](05_implementation_plan.md)（2026-10-21 确认）。M1 之前的“准备”已做完：2026-10-21 写好 `vpmkit/resources/candidate_api.md` 与 `vpmkit/resources/example/`（规格，不是代码），你已看过并同意，已提交（df892b1）。2026-10-26 起 PickCube 试跑会话按 05 执行：M1a、M1b 已提交（adcd518、97bc833）；M2 已提交（c423943）；M3 已提交（96ad2d5），参照候选你已看过同意；TASK.md 的模板已提交（5a7691d）；M4a 已提交（c1a3580）；M4b 已提交（077ac58）；PickCube 试跑已走通，见 [06](06_pickcube_trial.md)；M5 已提交；PickCube 试跑的 M1–M5 全部完成（第 8 节）。

## 1. 分支与提交

分支 `stage1-impl`，从 master 的 5cdd64e 分出，没有推送，也没有合并到 master。

- 删除前的代码在这三个提交里，需要时可以查看：e90a127（M1 核心）、4ad5a75（M2 ManiSkill 适配层）、1b0212c（M3a 两层 validator）。
- 2026-10-21 删去 `vpmkit/`（21 个文件，含 `resources/candidate_api.md`）、`tests/`（18 个文件）和 `docs/Stage1/briefs/`（7 个文件），随 b664da5 提交。
- 其余提交都是文档：07ca738、2c825e7、e2e6acc、27fccc1、581905c、b664da5、d5bed7d（讨论记录与交接），c19097d（技术方案）。

## 2. 删掉的代码原来是什么（供重写时参照）

代码由 Codex 按 m1–m3a 的任务说明编写，都是第一版设计下的写法。这些任务说明原在 `docs/Stage1/briefs/`，2026-10-21 一并删除，旧版留在 git 历史中（581905c）。
- M1 核心：张量快照式的世界状态与视图、谓词装饰器、几何工具、`stage_graph.yaml` 的 schema 与加载、AST 限制、自动机运行时与 Teacher。
- M2 ManiSkill 适配层：环境创建、绑定接口、张量快照、里程碑读数、场景清单。
- M3a 两层 validator：第一层六项检查（在子进程中运行）、逐帧核对与轨迹检查、回放摘要、第二层的提示词与解析。
- 测试：单元测试 86 个，ManiSkill 集成测试 13 个。

议程确认后改动了其中很多写法，例如图中没有完成节点、不输出事件、m 取 1、回退后同一步照样前进、删去逐帧核对、Stage1 不用示范（00 第 4、8 节）。

## 3. 重写时要用到的环境事实（2026-10-20、10-21 核对）

- conda 环境 vpm-mani，只用不改：Python 3.10.20、torch 2.12.0+cu126、sapien 3.0.3、gymnasium 1.2.3、pydantic 2.13、PyYAML 6、h5py；mani_skill 3.0.1 以可编辑方式装自 /home/zxh/projects_dir/ManiSkill，只读使用。
- 本机 4 张 RTX 3090。
- mplib 与 NumPy 2 不兼容，导入失败，ManiSkill 的运动规划脚本跑不了。
- 没有 pytest，测试用标准库 unittest。
- 系统自带的 python3 是 3.8，缺少一些新的标准库接口；脚本统一用 vpm-mani 的 Python。

## 4. 重写时要记住的经验

1. **同一进程里第二次创建 GPU 场景，SAPIEN 会崩溃。** 所有用到 GPU 仿真的代码和测试，都要每个环境开一个子进程。
2. **崩溃文件。** 跑测试时在命令前加 `ulimit -c 0`，并把 `XDG_CACHE_HOME` 指到项目的 `outputs/cache`，避免往 /var/crash 写文件。M2 测试时曾留下 `/var/crash/_usr_lib_python3.8_unittest___init__.py.1018.crash`（约 470 MB），2026-10-21 已按你的要求删除。
3. **`make_env`：** 环境数大于 1 时用 GPU 后端（`physx_cuda`），等于 1 时用 CPU 后端。
4. **欧拉角：** ManiSkill 的判定用 `matrix_to_euler_angles(quaternion_to_matrix(q), "XYZ")`；旧代码的 `quat_to_euler_xyz` 照此实现，并在集成测试中核对过。
5. **手臂静止：** `Panda.is_static` 用除两个手指外的关节速度（`qvel[..., :-2]`），取绝对值的最大值；`Actor.is_static` 用线速度和角速度的范数。
6. **DeepSeek 版 Claude Code：** 从 Claude Code 的进程（以及从这里启动的 Codex）里调用时，会继承外层的 `CLAUDE*`、`ANTHROPIC*` 变量，导致 “Not logged in”。子进程的环境要由代码构造（讨论记录 §4.4）。
7. **审查 M3a 时改过的一处：** 第一层的子进程原来写死用 0 号卡，改为沿用调用方的 `CUDA_VISIBLE_DEVICES`。
8. **导入顺序（2026-10-26）：** 直接 `from mani_skill.utils.geometry import rotation_conversions` 会因循环导入报错；先 `import mani_skill.envs` 就没有问题。导入不建场景、不写 `~/.maniskill`。
9. **隐藏物体的位姿（2026-10-26，读源码）：** GPU 仿真中，`_hidden_objects`（如 PickCube 的 goal_site）在渲染时被挪到很远处；`Actor.pose` 会返回真实位姿，所以适配层一律经 `Actor.pose` 读，不直接读 physx 的缓冲区。

## 5. 任务说明

原来的 m1–m6 任务说明是在第一版设计下写的，2026-10-21 已删除。重写的任务说明，按 [技术方案](00_technical_plan.md) 重新写；分步、各步交给 Codex 的内容和验收方式见 [05](05_implementation_plan.md)。

## 6. outputs/ 中的文件

`outputs/` 不进 git。2026-10-21 按你的要求整理过两次：先删去旧实现留下的 Codex 调试日志、trace 与缓存；再删去作废的记录，把文献移进 `references/`。现在只有：
- `outputs/stage1/probe_claude_deepseek/20261021-111820/`：DeepSeek 版 Claude Code 的实测原始记录（00 第 7.7 节、01 §4.4 的依据）。那次由 Codex 跑、全部登录失败的实测（`20261021-010804/` 与 `outputs/stage1/codex/`），结论作废，已删除。
- `outputs/stage1/env_inventory/`：核对任务与示范情况时取得的清单，包括 ManiSkill 的任务表（00 第 9.1 节的来源）、示范目录、PPO 配置的任务名单，以及 MetaWorld、LIBERO 的目录与源文件（01 §4.5、§4.6 的依据）。
- `outputs/cache/`：缓存目录，`XDG_CACHE_HOME` 指到这里（第 4 节第 2 条）。

文献对照（01 §4.3.1）用到的原文和检索记录，已移到 `references/notes/_sources/granularity_2026-10-20/`；其中 SARM 的 PDF 和 PRM4RL 的文字在 `references/` 中原本就有相同的副本（`added3_chen2026sarm.pdf`、`base_progress_reward.txt`），重复的那份已删除。`references/` 自 2026-10-21 起整个不进 git。

## 7. 委托 Codex 的做法

- 按你的 CLAUDE.md，写代码的活交给 Codex，我写任务说明、审查，提交前问你。
- 用 codex-delegate 技能。它的脚本：

  ```bash
  node ~/.claude/skills/codex-delegate/scripts/relay.mjs --brief <任务说明> --cd /home/zxh/projects_dir/vpm-claude --timeout 2h
  ```

  跑 ManiSkill 或用 GPU 的任务，加 `--sandbox danger-full-access`，派发前工作区要干净。
- 任务说明里写明：指定使用的显卡；不装包；不联网（需要调用 DeepSeek 的除外）；不改 ManiSkill 和 conda 环境；不写项目以外的位置。

## 8. 重写的进展（2026-10-26 起）

PickCube 试跑会话按 [05](05_implementation_plan.md) 执行。任务说明在 [briefs/](briefs/)，Codex 的运行记录（任务说明原文、事件流、最终汇报）在 `outputs/stage1/codex/<步骤>/`，不进 git。

| 步骤 | 状态 | 代码 | 测试 |
| --- | --- | --- | --- |
| M1a 运行时 | 已提交（adcd518） | `vpmkit/`：`world.py`、`geometry.py`、`predicate.py`、`literal.py`、`automaton.py`、`teacher.py`、`render.py`、`errors.py`、`api.py`，`candidate/` 中的 `schema.py` 与 `modules.py` | `tests/unit/`，68 个，全部通过 |
| M1b 静态检查 | 已提交（97bc833） | `vpmkit/candidate/`：`codes.py`、`pyinfo.py`、`report.py`、`static.py`，`load_candidate` | `tests/unit/test_static.py` 与 `tests/fixtures/mutations.py`（119 种改法）；单元测试共 96 个，全部通过 |
| M2 ManiSkill 适配层 | 已提交（c423943） | `vpmkit/adapters/maniskill/`：`env.py`、`binding.py`、`adapter.py`、`inventory.py`、`helpers_table.py`；`errors.py` 加 `BindingError` | 单元测试共 110 个；`tests/integration/` 4 个（GPU，`VPM_INTEGRATION=1`），全部通过 |
| M3 参照候选与第一层 | 已提交（96ad2d5） | `candidates/reference/PickCube-v1/`；`vpmkit/validate/`：`run_worker.py`、`layer1.py`、`check_sh.py`；`vpmkit/resources/check.sh.template`；`scripts/check_candidate.py` | 单元测试共 123 个；集成测试共 9 个，全部通过 |
| M4a 输入包 | 已提交（c1a3580） | `vpmkit/package/`：`strip.py`、`helpers.py`、`build.py`；`scripts/build_packages.py`；模板 `vpmkit/resources/TASK_template.md`（我写） | 单元测试共 135 个；集成测试共 10 个，全部通过 |
| M4b harness 与第二层 | 已提交（077ac58） | `vpmkit/harness/`：`env.py`、`rundir.py`、`backends.py`、`review.py`、`run.py`；`configs/default.yaml`；`scripts/run_generation.py`；提示词 `vpmkit/resources/review_prompt.md`（我写） | 单元测试共 166 个；集成测试共 15 个（脚本后端，不调用 DeepSeek），全部通过 |
| M5 PBRS 奖励包装 | 已提交 | `vpmkit/rewards/pbrs.py`；`Teacher.step` 加 `env_mask`；`configs/default.yaml` 加 `pbrs`；`scripts/pbrs_smoke.py` | 单元测试共 171 个；集成测试共 16 个，全部通过 |

M1a 的要点：
- 世界快照 `Snapshot` 是张量的数据类：各对象的 `BodyState`（位姿、速度、尺寸、附加属性，夹爪另有开度与手臂关节速度，预留关节读数）、桌面高度、成对的抓取与接触力读数，以及 `evaluate()` 的字段（`official`）。谓词看到的是只读视图，世界视图拿不到 `official`。快照可以拼接、切片、保存与读取（`torch.save`，读取时 `weights_only=True`）。
- 谓词调用时没有显式传入的阈值，取当前生效的值：Teacher 在每次调用候选代码时，用 contextvars 设定本 Teacher 的阈值，所以几个参数不同的 Teacher 可以共用一份加载的候选。
- Teacher 每次调用候选代码后，检查快照中的张量有没有被原地修改（比较 `tensor._version`），被改了就报 `CandidateRuntimeError`；候选的返回值不是 `[N]` 的浮点张量或不在同一设备上，报 `CandidateOutputError`。M3 的运行检查把这两种错误分别报为 `run.error`、`run.output`。
- 候选的 Python 文件按每次加载一个新的包名导入，`progress.py` 能 `from .predicates import ...`，导入时不写 `__pycache__`。
- 小问题，不影响使用：取反的文字恰好在 margin = 0 时不成立，默认 progress 给它记 1（照 00 第 3.5 节的公式，只在 margin 正好为 0 时出现）；装饰器允许 `w` 写成仅限位置的参数，比 M1b 的静态规则宽。

M1b 的要点：
- 第一层的前三组（解析、schema 与引用、代码限制）只读 YAML 和 Python 的语法树，不导入、不执行候选代码；谓词的签名、阈值默认值和模板都从语法树读出。后一组不通过就不跑，同一组内报出全部问题。
- 报告的 Markdown 就是 agent 运行 `./check.sh` 时看到的：首行 “Check report: PASSED/FAILED”，各组状态，再逐条列出错误代码、位置（YAML 路径或文件与行号）和说明。
- 实现上的取舍（都不改设计）：谓词的导入只认 `from vpmkit.api import ...` 与 `import vpmkit.api`；progress 的 `w`、`o` 可以写成仅限位置的参数；异步函数一律不行；`from __future__ import ...` 会因双下划线被 `ast.unsafe` 拦下。

M2 的要点：
- `make_env(env_id, num_envs)`：N > 1 用 `physx_cuda`，N = 1 用 `physx_cpu`；默认 `obs_mode="state"`、`reward_mode="sparse"`。
- `ManiSkillAdapter(env, bind)` 在构造时调用一次 `bind(env.unwrapped, api)`；`snapshot(info=None)` 每步读一份快照，所有张量都复制出来，不与仿真器的缓冲区共用内存。夹爪：位姿取 `agent.tcp`（`panda_hand_tcp`），开度是两个手指关节位置之和，最大开度是它们上限之和，`arm_qvel` 是去掉两个手指的关节速度。actor 的位姿一律经 `Actor.pose` 读。只支持 Panda 一族（panda、panda_wristcam），其他机器人报 `NotImplementedError`。
- 快照中 `evaluate()` 的字段一律转成 float32（成功信号为 0 或 1）；`grasping` 仍是布尔。
- 绑定或读数出错报 `BindingError`（M3 的运行检查报为 `run.bind`）。
- 场景清单从运行中的环境生成，格式同示例；PickCube 的 `goal_site` 标为 visual only，半尺寸从显示用的网格读出（[0.025, 0.025, 0.025]）；`evaluate()` 读到的属性只有 `self.goal_thresh` = 0.025。
- 集成测试的跑法：

  ```bash
  cd /home/zxh/projects_dir/vpm-claude && ulimit -c 0 && VPM_INTEGRATION=1 TMPDIR=$PWD/outputs/tmp XDG_CACHE_HOME=$PWD/outputs/cache MS_ASSET_DIR=$PWD/outputs/maniskill CUDA_VISIBLE_DEVICES=1 /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/integration -t . -v
  ```

M3 的要点：
- 第一层的入口：`run_layer1(candidate_dir, env_id)`（Python）或 `scripts/check_candidate.py --env <env_id> <candidate_dir>`（命令行，退出码 0 通过、1 不通过、2 出错）。运行检查在子进程中进行，沿用调用方的 `CUDA_VISIBLE_DEVICES`。
- `check.sh` 由 `write_check_sh(workspace, env_id)` 按模板写出，写死仓库与 Python 的绝对路径，自己设好 `XDG_CACHE_HOME`、`MS_ASSET_DIR`、`TMPDIR`、`PYTHONPATH` 并关掉崩溃文件，所以在 harness 构造的最小环境里也能跑。带参数时直接拒绝。
- 用时：PickCube 参照候选一次完整的第一层冷启动约 12–13 秒，其中运行检查约 9 秒。
- agent 看到的失败报告，每条带错误代码、位置（候选文件与行号，算出 NaN 时是函数名）、异常类型与消息、出错的函数与实例、种子与步数，以及候选文件里的 traceback 行。

M4a 的要点：
- 生成输入包：`scripts/build_packages.py --env PickCube-v1 [--out outputs/stage1/packages] [--overwrite]`，或 `vpmkit.package.build.build_package(env_id)`。场景清单在子进程中生成（要建一个 GPU 环境，沿用调用方的 `CUDA_VISIBLE_DEVICES`）。
- 包的内容：TASK.md、`env_source.py`（删去两个奖励函数，其余逐字保留，所以被删处前后会留下几行空行）、`helpers.py`、`scene_inventory.md`、`candidate_api.md`、`example/`（8 个文件）、`manifest.json`（各文件的来源与 sha256，`package_sha256` 由各文件的路径与哈希算出，不含时间）。
- PickCube 的包：`outputs/stage1/packages/PickCube-v1/`，`package_sha256` = 611246a2c74dc8724270a93d9af91ec7df3d3fdaf6cdb05c22651da60835cd29。
- 会被拦下的三个任务（PullCubeTool、TurnFaucet、PushT）报 `ResidualRewardError` 并列出残留的行，等扩展时再定怎么处理。

M4b 的要点：
- 启动一次生成：`scripts/run_generation.py --env PickCube-v1 --gpu <卡号> [--backend claude|scripted]`。它启动时把 `CUDA_VISIBLE_DEVICES` 设为所选的卡（agent 的 `check.sh` 与 harness 自己的第一层用同一张卡），并把 `XDG_CACHE_HOME`、`MS_ASSET_DIR`、`TMPDIR` 指到 `outputs/`；DeepSeek 子进程的环境由代码构造，只有 HOME、PATH、LANG、LANGUAGE、LC_ALL、三个代理变量与 `CUDA_VISIBLE_DEVICES`。所以从你的终端和从我这边启动，结果相同。
- 运行目录 `outputs/stage1/runs/<任务>/<时间>/`：`workspace/`（输入包副本只读，`candidate/` 可写，`check.sh`，`git init`）与 `records/`（`run.json`：包的哈希、取值、环境变量名单、CLI 版本、会话编号；每轮一个目录：prompt、stream-json、stderr、本轮结束时的候选、两层的报告、审查的原始输出与解析结果；`verdict.json`：结论、用了几轮、每轮的第一层错误代码与审查错误类别、agent 运行 `check.sh` 的次数）。
- 判定：生成会话正常结束、用完 `--max-turns`、到了时间上限，这一轮都照常进入两层检查；没有结果事件或其他出错算 harness 故障，最多重试 2 次（有会话编号时续接原会话）。审查输出解析不了也算 harness 故障。
- 超时时结束整个进程组（先 SIGTERM，宽限 5 秒后 SIGKILL）；正常结束后也清理进程组。
- stream-json 与 stderr 保存后，把名字像密钥的字段值（如 init 事件的 `apiKeySource`）抹成 `[REDACTED]`，token 用量的计数保留。

PickCube 试跑（2026-10-26）：`scripts/run_generation.py --env PickCube-v1 --gpu 1`，运行目录 `outputs/stage1/runs/PickCube-v1/20261026-184803/`，第 1 轮通过，约 15 分钟（生成约 2.7 分钟，审查约 11.9 分钟）。结果与对比见 [06](06_pickcube_trial.md)。试跑时确认的事实：DeepSeek 子进程由代码构造环境后登录正常；`dontAsk` 模式下工作区内的只读 Bash 命令会被自动放行，读工作区以外的路径都被拒绝（06 第 4.1 节）；审查会话用了时间上限的八成（06 第 4.2 节）。

M5 的要点：
- 用法：`ManiSkillVectorEnv(PBRSWrapper(make_env(env_id, N), candidate, gamma, r_bonus), auto_reset=True, ignore_terminations=False)`。包装套在 `ManiSkillVectorEnv` 里面，与官方 PPO 的 `FlattenActionSpaceWrapper` 同一层；环境自己的奖励不用。
- 每步：读快照，Teacher 更新一次，奖励 = γΦ(s′) − Φ(s) + 成功 × r_bonus；成功终止时 Φ(s′) 取 0，截断时照常用 Φ(s′)。`info["pbrs"]` 中记下 Φ、上一步的 Φ、阶段、塑形项与算 Φ 时的 `elapsed_steps`。
- 部分重置（`options["env_idx"]`）时，Teacher 只重置并更新被重置的环境，它们的 Φ(s) 换成新回合初始状态的值。
- 开销：N = 1024 时仿真每步约 40.9 ms，读快照加 Teacher 每步约 5.0 ms。
- Stage2 要改的：ManiSkill 官方 PPO 对成功终止也自举，用本包装时要改成只对截断自举（00 第 4.6 节）。

PPO 接入检查（2026-10-26，05 第 8.1 节）：`scripts/ppo_check.py --reward {teacher,dense,sparse} [--candidate <dir>] [--track ...]`，照官方 `ppo.py` 改写；判断自举的函数在 `vpmkit/ppo_bootstrap.py`，单元测试 `tests/unit/test_ppo_check.py`（单元测试共 174 个）。还没有提交。第一次检查的结果见 [07](07_ppo_check.md)。
