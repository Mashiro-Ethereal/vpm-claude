# Stage1 实现现状（2026-10-20）

> **用途：** 交接用。说明 `stage1-impl` 分支上已经实现了什么、暂停了什么、有哪些已知问题，以及怎么跑测试。设计结论以 [讨论记录](01_design_discussion.md) 为准，本文只记实现。
>
> **背景：** 2026-10-20 你授权我自主推进（第 3–9 点由我先定第一版，随即实现）。做完 M1、M2、M3a 后，你要求暂停，改为逐点确认议程。下面列的未实现部分，都要等议程确认后再做。

## 1. 分支与提交

分支 `stage1-impl`，从 master 的 5cdd64e 分出，没有推送，也没有合并到 master。

| 提交 | 内容 |
| --- | --- |
| 07ca738 | 记录：第 2 点定完 |
| 2c825e7 | 记录：第 3–9 点第一版 |
| e90a127 | M1：核心 |
| 4ad5a75 | M2：ManiSkill 适配层 |
| 1b0212c | M3a：两层 validator |
| e2e6acc | 记录：你对第 3 点的三个问题 |
| 27fccc1 | 记录：完成状态改为直接跟随环境的 success |

此后本文和交接说明另有一次提交。

## 2. 已实现的部分

代码由 Codex 按 [briefs/](briefs/) 中的任务说明编写。每个里程碑我都复跑了测试、审查了关键代码，然后提交。

- **M1 核心**：与仿真器无关，只用合成数据测试。
  - `vpmkit/world.py`：张量快照式的世界状态 `WorldState`；谓词能用的 `WorldView` 和 `ObjView`，不提供按名字取物体或读官方字段的接口；绑定接口 `BindingAPI`。
  - `vpmkit/api.py`：谓词装饰器 `@predicate`，以及 `bool_margin`。
  - `vpmkit/geometry.py`：四元数、位姿、有向包围盒等几何工具。其中 `quat_to_euler_xyz` 与 ManiSkill 的同名换算一致，已在集成测试中核对。
  - `vpmkit/artifact/`：文字解析、`stage_graph.yaml` 的 pydantic 模型与语义检查、候选目录加载、AST 限制。
  - `vpmkit/runtime/`：自动机更新（不变量防闪烁、回退到最早目标、同一步连续前进、完成状态）和 Teacher（无状态地算谓词实例，计算 progress、Φ、guidance、事件，按轨迹回放）。注意：这里的完成状态还是第一版的规则，见第 6 节。
- **M2 ManiSkill 适配层**（`vpmkit/adapters/`）：
  - 环境创建 `make_env`、绑定接口的实现、张量快照；
  - 与候选无关的里程碑读数 `MilestoneTracker`（按第 8 点第一版：官方布尔字段，加上每个动态物体的“被抓住”和“被抬起”）；
  - 场景清单。
- **M3a 两层 validator**（`vpmkit/validate/`）：
  - 第一层六项检查，默认在独立子进程中运行；
  - 官方对应的逐帧核对（一致率 ≥ 99.5%，官方字段恒定时记“未覆盖”）和轨迹检查；
  - 轨迹的保存与回放、回放摘要；
  - 第二层审查的提示词、结果解析，以及脚本化的审查后端。
- **测试**：单元测试 86 个，另有 13 个集成测试默认跳过；打开开关后跑 ManiSkill 集成测试 13 个，约 110 秒。合成候选在 `tests/fixtures/toy/`。
- **给生成 agent 看的接口说明**：[vpmkit/resources/candidate_api.md](../../vpmkit/resources/candidate_api.md)。其中“Bindings”“Limitations”两节还停留在 M1 的写法，计划在 M4 更新。

## 3. 怎么跑测试

```bash
cd /home/zxh/projects_dir/vpm-claude
ulimit -c 0; export XDG_CACHE_HOME=$PWD/outputs/cache PYTHONDONTWRITEBYTECODE=1
/home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests -t .
CUDA_VISIBLE_DEVICES=0 VPM_RUN_MANISKILL=1 /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest tests.integration.test_maniskill_adapter tests.integration.test_validate_maniskill
```

`ulimit -c 0` 和 `XDG_CACHE_HOME` 的作用：进程崩溃时不往 /var/crash 写文件，缓存留在项目的 outputs/ 里。

## 4. 环境事实（2026-10-20 核对）

- conda 环境 vpm-mani，只用不改：
  - Python 3.10.20、torch 2.12.0+cu126、sapien 3.0.3、gymnasium 1.2.3、pydantic 2.13、PyYAML 6、h5py；
  - mani_skill 3.0.1 以可编辑方式装自 /home/zxh/projects_dir/ManiSkill，只读使用。
- 本机 4 张 RTX 3090，实现中只用 0 号卡。
- mplib 与 NumPy 2 不兼容，导入失败，所以 ManiSkill 的运动规划脚本跑不了。
- 没有 pytest，测试用标准库 unittest。

## 5. 已知问题与约束

1. **同一进程里第二次创建 GPU 场景，SAPIEN 会崩溃。** 处理方式：第一层校验默认在子进程里跑；集成测试每个任务开一个进程。后面所有用到 GPU 仿真的代码和测试都要这样做。
2. **项目外留了一个文件。** M2 测试时有一次进程崩溃，系统的崩溃收集器写了 `/var/crash/_usr_lib_python3.8_unittest___init__.py.1018.crash`。我没有动它，需要的话请你删除。
3. **第一层的轨迹检查暂时没有真实数据。** 你决定先不下载官方示范，mplib 又不可用，所以这一项目前只用合成轨迹测过。
4. outputs/ 下有 Codex 运行时留下的调试日志和缓存，不进 git，可以随时删。
5. 审查 M3a 时我改过一行：第一层的子进程原来写死用 0 号卡，现在沿用调用方的 `CUDA_VISIBLE_DEVICES`，没设置时才用 0 号卡。

## 6. 已确认、但代码还没跟上的改动

**完成状态直接跟随环境的 success**（记录 §4.1 第 7 条，你 2026-10-20 确认）。要改的地方：
- 运行时：Teacher 从快照的 `official["success"]` 读成功信号。success 一成立就进入完成状态，不管当前在哪个阶段；连续 m 步不成立，就回到最后一个阶段。“最后一个守卫成立就进入完成状态”这条规则取消，最后一个守卫只用于 guidance 和 progress。
- 第一层的轨迹检查：原来的判定是“走完各阶段并进入完成状态”。现在进入完成状态不再要求走完各阶段，判定要改，比如改为“进入完成状态之前到达过最后一个阶段，且中途没有回退”。
- 相应的单元测试、candidate_api.md，以及 M5 任务说明中关于完成状态的描述。

## 7. 暂停的里程碑

任务说明都在 [briefs/](briefs/) 里。它们是在第一版设计下写的：议程逐点确认之后，要先按确认结果修改，再派发。

| 里程碑 | 内容 | 任务说明 |
| --- | --- | --- |
| M3b | 五个任务的参照候选，以及给生成 agent 看的 PushCube 示例；用 `set_pose` 摆出成功状态，核对照抄的官方公式 | m3b.txt |
| M4 | 生成 harness：输入包、Claude Code（DeepSeek）后端与脚本后端、修复循环、运行记录、命令行 | m4.txt |
| M5 | PBRS 奖励包装与冒烟测试 | m5.txt |
| M6 | 基于 rollout 的语义检验：守卫的必要性与充分性、预测性、闪烁、阶段是否只由当前状态决定 | m6.txt |

已完成的 M1、M2、M3a，任务说明也在同一目录（m1.txt、m2.txt、m3a.txt），供核对实现时参考。

## 8. 委托 Codex 的做法

- 按你的 CLAUDE.md，写代码的活交给 Codex，我写任务说明、审查，提交前问你。
- 用 codex-delegate 技能。它的脚本：

  ```bash
  node ~/.claude/skills/codex-delegate/scripts/relay.mjs --brief <任务说明> --cd /home/zxh/projects_dir/vpm-claude --timeout 2h
  ```

  跑 ManiSkill 或用 GPU 的任务，加 `--sandbox danger-full-access`，派发前工作区要干净。
- 任务说明里写明：只用 0 号卡；不装包；不联网；不改 ManiSkill 和 conda 环境；不写项目以外的位置。
