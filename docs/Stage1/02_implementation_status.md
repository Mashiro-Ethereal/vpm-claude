# Stage1 实现现状（2026-10-21）

> **用途：** 交接用。说明 `stage1-impl` 分支上的代码现状、重写时要用到的环境事实和经验，以及委托 Codex 的做法。设计结论以 [技术方案](00_technical_plan.md) 为准，本文只记实现。
>
> **现状：** 2026-10-21，议程全部定完（G1 推迟），[技术方案](00_technical_plan.md) 定为执行标准。此前写的全部 Stage1 实现代码已删除，理由（你的意见）：那些代码写在逐点讨论之前，基本都要大改，不如重写。重写按 00 第 10.3 节的实现阶段 M1–M5 进行，分步与验收见 [05](05_implementation_plan.md)（2026-10-21 确认），还没有开始。

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
