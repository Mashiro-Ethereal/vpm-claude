# PickCube 试跑与对比报告（2026-10-26）

> **用途：** 记录 Stage1 在 PickCube 上第一次端到端运行（agent 生成加两层检查）的结果，以及生成的候选与人写的参照候选的逐项对比，供你决定之后怎么走。做法见 [00](00_technical_plan.md) 第 7、8、10.3 节，执行计划见 [05](05_implementation_plan.md) 第 7.2 节。
>
> **结论：** 按 00 第 10.3 节的标准，Stage1 在 PickCube 上走通了：harness 把生成和两层检查完整走完一遍，候选第 1 轮就通过（第一层四组全过，第二层没有错误、也没有提醒）。生成的候选与参照候选在阶段划分、守卫、不变量与回退、官方对应与阈值上完全相同，差别只在细节（第 3 节）。另发现 00 第 7.7 节有一句写得不准：Claude Code 会自动放行工作区内的只读 Bash 命令；回查 10-21 的实测记录，工作区以外照样被拒绝，隔离成立（第 4.1 节）。

## 1. 运行概况【事实】

只由我这边启动一次（你定，01 §4.18），用 1 号卡。原始记录在 `outputs/stage1/runs/PickCube-v1/20261026-184803/`（不进 git）。

| 项 | 值 |
| --- | --- |
| 输入包 | `outputs/stage1/packages/PickCube-v1/`，`package_sha256` = 611246a2…cd29 |
| CLI | Claude Code 2.1.223，模型 `deepseek-flash[1m]`，权限模式 `dontAsk`，工具 Read、Write、Edit、Glob、Grep、Bash |
| 子进程的环境变量 | CUDA_VISIBLE_DEVICES、HOME、HTTP_PROXY、HTTPS_PROXY、LANG、LANGUAGE、NO_PROXY、PATH（只记名字） |
| 用时 | 18:48:03 – 19:02:52，共约 15 分钟 |
| 结论 | passed，用了 1 轮 |
| 生成会话 | 23 个 turn，约 2.7 分钟；读 14 个文件、写 5 个文件、Bash 3 次；输入 3.3 万 token、输出 2.9 万 token、缓存命中 26 万 token；被拒绝的工具调用 0 |
| `check.sh` | agent 跑了 1 次，第一次就全部通过（约 11 秒） |
| 第一层（harness 再跑一次） | 四组全过，11.2 秒 |
| 第二层审查 | 23 个 turn，约 11.9 分钟（时间上限 15 分钟）；读 20 个文件、Glob 2 次；输出 `[]`；输出 14 万 token（多为推理） |
| 记录 | 每轮的完整对话、候选、两层报告都在；`apiKeySource` 已抹成 `[REDACTED]`；stderr 为空；没有 “Not logged in” |

agent 的工作顺序与 TASK.md 一致：先读 TASK.md、candidate_api.md、示例的全部文件、环境源码、`helpers.py`、场景清单和 `check.sh`，再一次写出五个文件，跑一次 `check.sh`，通过后写总结结束。

## 2. 生成的候选

`stage_graph.yaml`：

```yaml
task: Grasp the red cube with the gripper, carry it to the goal point, and hold it there until the robot arm comes to rest.
objects:
  g: {name: the gripper}
  cube: {name: the red cube}
  goal: {name: the goal point}
stages:
  - name: reach
    exit: ["near(g, cube)"]
  - name: grasp
    exit: ["grasped(g, cube)"]
    invariants:
      - {literal: "near(g, cube)", regress_to: reach}
  - name: carry
    exit: ["at_goal(cube, goal)"]
    invariants:
      - {literal: "grasped(g, cube)", regress_to: reach}
  - name: hold
    exit: ["arm_static(g)"]
    invariants:
      - {literal: "at_goal(cube, goal)", regress_to: carry}
official:
  - {literals: ["grasped(g, cube)"], key: is_grasped}
  - {literals: ["at_goal(cube, goal)"], key: is_obj_placed}
  - {literals: ["arm_static(g)"], key: is_robot_static}
  - {literals: ["at_goal(cube, goal)", "arm_static(g)"], key: success}
params:
  - {name: near.max_dist, default: 0.02, range: [0.0, 0.05]}
  - {name: progress.reach.d0, default: 0.3, range: [0.1, 0.6]}
  - {name: progress.carry.d0, default: 0.4, range: [0.1, 0.8]}
```

其余文件在运行目录的 `workspace/candidate/`，与 `records/round_1/candidate/` 相同。

## 3. 与参照候选逐项对比

参照候选在 `candidates/reference/PickCube-v1/`（00 第 3.2 节）。

| 项 | 参照候选 | 生成的候选 | 判断 |
| --- | --- | --- | --- |
| 阶段划分 | reach → grasp → carry → settle | reach → grasp → carry → hold | 相同，只有最后一段的名字不同 |
| 守卫 | `near`；`grasped`；`at_goal`；`arm_static` | 相同 | 相同 |
| 不变量与回退 | grasp 保持 `near` → reach；carry 保持 `grasped` → reach；settle 保持 `at_goal` → carry | 相同 | 相同 |
| 官方对应 | `grasped` ↔ is_grasped，`at_goal` ↔ is_obj_placed，`arm_static` ↔ is_robot_static，success = 最后一段守卫加不变量 | 相同（success 的两条文字次序不同，按集合比较相同） | 相同 |
| 阈值 | 官方的 0.025、0.2 照抄；`near.max_dist` 默认 0.02、范围 [0, 0.05] | 相同 | 相同 |
| 谓词的写法 | `at_goal` = 0.025 − ‖t.pos − o.pos‖；`arm_static` = 0.2 − max\|arm_qvel\| | 相同的公式；把距离写成测量函数 `goal_dist`，供 progress 共用 | 相同 |
| `goal` 的绑定 | `api.site(lambda env: env.goal_site.pose)` | `api.actor(env.goal_site, half_size=env.goal_thresh)`：按没有碰撞体的 actor 绑定，半尺寸取标记小球的半径 | 都对。生成的写法正好走到 M2 定的“没有碰撞体的 actor”这条路（01 §4.13），抓取读数恒为假、接触力恒为 0，谓词没有用到这两项 |
| progress | reach 自写（d0 = 0.3）；carry、settle 用默认（`at_goal` scale 0.3，`arm_static` scale 1） | reach 自写（d0 = 0.3）；carry 也自写，1 − 距离/0.4，`progress.carry.d0` 默认 0.4、范围 [0.1, 0.8]；hold 用默认（`arm_static` scale 0.2） | 都合理。生成的 carry 有自己的尺度参数，可交给 BO 调；`arm_static` 的 scale 0.2 比参照候选的 1 陡，hold 的进度在关节速度降到 0.4 rad/s 以下才开始上升 |
| 模板 | `at_goal`：“… is not at the goal position; move …”；`arm_static`：“The gripper is still moving; hold the gripper still.” | `at_goal`：“The red cube is not at the goal point; move the red cube to the goal point.”；`arm_static`：“The gripper is still moving; stop moving the gripper and let its arm come to rest.” | 都是“状态加补救办法”，显示名带冠词 |
| notes.md | 四段齐全；其他做法：目标低时推过去 | 四段齐全，写得更细：解释了为什么没有松手阶段、每条回退的理由；其他做法列了四种（推、抛、初始状态就满足、到目标后松手） | 生成的更详细。有两处小的不准确，见下 |

notes.md 中两处不准确（都不影响候选本身）：
- 说 reach 与 grasp 之间来回切换时 “Φ 约变 0.25”。【推导】在 `near` 的边界上，reach 的 progress 约为 1 − 0.055/0.3 ≈ 0.82，Φ ≈ 0.20；进入 grasp 后 Φ = 0.25，实际只变约 0.05。
- 说必要时可以用 `runtime.debounce` 平滑这种切换。candidate_api.md 写明 `runtime.debounce` 不属于候选，m = 1 是定下的做法（00 第 11 节第 10 项）。

第二层没有报出这两处，也没有给任何提醒。它们不在 a–j 的类别里（notes.md 的准确性只在 f 类“多条文字的守卫有没有写理由”与 j 类“其他做法”中涉及），这与提示词的约定一致。

## 4. 观察到的问题

### 4.1 Claude Code 自动放行工作区内的只读 Bash 命令【事实】；工作区以外照样拒绝【事实】

- 这次 agent 用 Bash 跑了 `find …/workspace/example -type f | sort` 和 `ls -la …/workspace/candidate`，都没有被拒绝。
- 回查 10-21 的实测记录（`outputs/stage1/probe_claude_deepseek/20261021-111820/raw/`）：
  - `p3`：在工作目录里 `ls -la` 也被放行；被拒的是 `command -v curl; command -v wget` 与带参数的 `./check.sh`。
  - `iso_v1`（与现在一样不给通用的读许可）：`Bash cat ../forbidden/answer.txt`、`Bash ls ..` 都被拒绝；Read、Glob、Grep 读工作区以外也都被拒绝。
- 所以 Claude Code 会自动放行工作区内的只读命令，读工作区以外的路径则一律拒绝；00 第 7.7 节“读和写都限于运行目录内”成立，只是“凡未被允许的操作一律拒绝”一句不准确，已订正（00 附录 B）。agent 拿不到参照候选，也拿不到带奖励函数的原始源码。
- 【推导】实测只覆盖了 `cat` 与 `ls ..` 两种写法；其余只读命令（`find`、`grep`、`head` 等）读外部路径，按同一套路径检查，应当同样被拒。harness 的记录保存了 agent 的每一条 Bash 命令，扩展到其余任务时，可以在汇报中顺带核对。

### 4.2 审查会话用了时间上限的八成【事实】

审查用了 11.9 分钟，上限 15 分钟，输出 14 万 token，大多是推理。PickCube 是最简单的任务之一；文件更多、`evaluate()` 更复杂的任务（如 PegInsertionSide、StackPyramid），审查可能超时。超时算 harness 故障，会重试两次，仍超时就把这次运行记为 harness 故障。扩展到其余任务之前，可以把审查的时间上限放宽（比如 30 分钟），或者先看第 1 组任务的实际用时再定。

### 4.3 这次没有走到修复轮

候选第 1 轮就通过，`--resume` 续接修复没有在真实运行中用到。续接本身 10-21 实测过（00 第 7.7 节），轮次逻辑有脚本后端的测试覆盖（第一层不过后修复、审查报错后修复、四轮都不过）。扩展到其余任务时，修复轮多半会出现。

### 4.4 PickCube 与示例很接近

示例是虚构的抓放任务，PickCube 是“抓起后送到目标点”，结构几乎相同，agent 基本照着示例写，第一次就对，在意料之中。这次试跑主要验证的是流程，不说明 agent 在结构不同的任务上（推、拉、滚，工具，插入，多步骤）会怎样；00 第 12 节的【假设】“一个抓放示例够用”要在第 1 组（PushCube、PullCube、RollBall）上看。

## 5. 待定

- 第 4.2 节：审查的时间上限是否放宽。
- 之后往哪个方向走（扩展到其余 15 个任务，或先跑一次 PPO），你在任务说明中说等试跑做完再说。执行计划中还剩 M5（PBRS 奖励包装）。
