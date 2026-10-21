# 新会话的交接说明（2026-10-21）

> **用途：** 换新会话继续 Stage1 时，把下面代码块中的文字原样贴到新会话的第一条消息。
>
> **状态：** 2026-10-21 改为 PickCube 试跑会话的交接说明：在 PickCube 上走通 M1–M5（包括 agent 生成和两层检查）。前一版是“只写示例”的会话用的，留在 git 历史中（09234cf）；更早的通用版见 d253b71。

```text
这是 VPM 项目 Stage1（在 ManiSkill 上自动构建过程 teacher）的接续会话，专门做 PickCube 的试跑：让 Stage1 在 PickCube 一个任务上走完一条完整的路径，包括 agent 生成和两层检查。设计已全部定完（G1 推迟）；示例（虚构的抓放任务）和接口说明 candidate_api.md 已由另一个会话写好，在 vpmkit/resources/。

【硬约束】
- /home/zxh/projects_dir/vpm-claude 是我们唯一的工作目录，未经允许不要访问这台服务器上的其他位置，如果确实需要访问其他位置必须得到我的允许。例外：conda 环境 vpm-mani 可以只读使用（其中的 mani_skill 3.0.1 以可编辑方式装自 /home/zxh/projects_dir/ManiSkill，也只读，可以读它的源码），不装包、不改环境。
- 不要修改设计文档（VPM_idea.md 和 docs/ 下的文件），docs/Stage1/ 除外。遇到需要改动整体设计的问题，记在 01 §5，告诉我，讨论之后再决定。
- 不使用 /home/zxh/projects_dir/vpm（以前的失败尝试）。
- 提交前先问我；不推送；不合并到 master。当前分支是 stage1-impl。references/ 整个不进 git。
- DeepSeek 版 Claude Code（/home/zxh/.local/bin/claude-deepseek）只由 harness 的代码调用：不读包装脚本的源码；它的配置文件含密钥，不读取、不打印、不记录；不打印环境变量的值，需要时只列名字。
- 调用 DeepSeek（PickCube 试跑）和下载任何资产之前，先问我。PickCube 用不到需要下载的资产。

【开始前】
- 确认示例和 candidate_api.md 我已经看过并提交：git log 里有对应的提交，git status 干净。不是这样就停下来问我。
- 从 02、05 的状态和 git log 看做到了哪一步（M1 可能已在别的会话做完），从下一个没做的阶段开始。

【先读，按顺序】
1. docs/Stage1/00_technical_plan.md：技术方案，执行标准；各项决定的理由在第 11 节。
2. docs/Stage1/05_implementation_plan.md：执行计划，每一步做什么、测什么、怎么验收、什么时候停下来问我。
3. docs/Stage1/02_implementation_status.md：代码现状、环境事实与经验、委托 Codex 的做法。
4. vpmkit/resources/candidate_api.md 与 vpmkit/resources/example/：接口与示例，是 M1 起各步的规格。
5. 需要讨论经过或依据时，查 docs/Stage1/01_design_discussion.md（§4.9–§4.12 是最近的决定）。

【这次要做的】
按 05 的步骤在 PickCube 上走通：M1a、M1b → M2（只做 PickCube）→ M3（PickCube 参照候选、第一层、check.sh）→ M4a（PickCube 的输入包）→ M4b（harness、第二层、PickCube 试跑）→ M5（PBRS 奖励包装）。
- “走通”的标准（00 第 10.3 节）：harness 把生成 Stage Graph 的完整流程走完一遍，包括生成和两层检查；候选通过与否都是有用的反馈，暂不考虑候选的性能。
- 由你自己写的英文材料（05 第 2 节）：PickCube 参照候选的规格（M3 之前）、TASK.md 的模板与设计规则（M4a 之前）、第二层审查的提示词（M4b 之前）。
- 到这几步时问我取值：--max-turns 与每轮的时间上限（M4b），成功奖励 r_bonus（M5）。
- PickCube 试跑：开始前问我；由你自己启动，不交给 Codex；从我的终端和从你这边各启动一次（给我在终端运行的命令）；生成的候选与参照候选逐项对比，写一份对比报告。
- 每完成一个实现阶段，停下来向我汇报，我同意后再做下一个。
- 不做的：其余 15 个任务（适配层的其余读数、资产下载、三个被拦下的任务）；试跑之后往哪个方向走，等试跑做完再说。

【做法】
- 中文，技术名词用英文；标注【事实】【推导】【假设】【决定】【待定】；不用打分表；需要我决定的地方一次只提一点，停下来等我决定。
- 写代码按我的 CLAUDE.md 交给 Codex（codex-delegate 技能）：你写任务说明、审查结果（逻辑代码逐行看 diff，自己重跑测试）；审查通过后不自动提交，等我说；同一任务返工两次仍不行，停下来告诉我。
- 用 GPU 的阶段（M2 起）用 danger-full-access 沙箱交给 Codex，交出去时说明“这次关了沙箱”：交出去前工作区要干净；用 nvidia-smi 挑空闲的卡，用 CUDA_VISIBLE_DEVICES 指定；只改项目目录内的文件，不装包，不改 conda 环境与 ManiSkill。
- 同一个进程里不要两次创建 GPU 场景，否则 SAPIEN 会崩溃；命令前加 ulimit -c 0，并把 XDG_CACHE_HOME 指到 outputs/cache。其余环境事实见 02。
- 新的决定先改 00（包括附录 B 的修改记录），再在 01 中记下讨论经过，05 随之更新。决定写进文档，记忆里只放指针。
- 每完成一个阶段，更新 02 的代码现状；要换会话时，更新 04 的交接说明。

【其他待办（这一步不做）】
- docs/Stage1/03_idea_session_messages.md：给 idea 会话的合并消息（27 处要改、2 处建议补充），等我转。
```
