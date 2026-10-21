# 新会话的交接说明（2026-10-21）

> **用途：** 换新会话继续 Stage1 时，把下面代码块中的文字原样贴到新会话的第一条消息。
>
> **状态：** 2026-10-21 按技术方案重写。设计已全部定完（G1 推迟），下一步从实现阶段 M1 开始。2026-10-20 那一版（逐点确认议程时用的）留在 git 历史中（c19097d）。

```text
这是 VPM 项目 Stage1（在 ManiSkill 上自动构建过程 teacher）的接续会话。设计已全部定完（G1 推迟），接下来按技术方案实现。

【硬约束】
- /home/zxh/projects_dir/vpm-claude 是我们唯一的工作目录，未经允许不要访问这台服务器上的其他位置，如果确实需要访问其他位置必须得到我的允许。例外：conda 环境 vpm-mani 可以只读使用（其中的 mani_skill 3.0.1 以可编辑方式装自 /home/zxh/projects_dir/ManiSkill，也只读），不装包、不改环境。
- 不要修改设计文档（VPM_idea.md 和 docs/ 下的文件），docs/Stage1/ 除外，那里放我们的讨论记录。遇到需要改动整体设计的问题，记在讨论记录 §5，告诉我，我们讨论之后再决定。
- 不使用 /home/zxh/projects_dir/vpm（以前的失败尝试）。
- 提交前先问我；不推送；不合并到 master。当前分支是 stage1-impl。
- references/ 整个不进 git。
- DeepSeek 版 Claude Code（/home/zxh/.local/bin/claude-deepseek）只由 harness 的代码调用：不读包装脚本的源码；它的配置文件含密钥，不读取、不打印、不记录；不打印环境变量的值，需要时只列名字。
- 下载资产包（YCB 物体、AssemblingKits、PartNet 水龙头），以及调用 DeepSeek 跑任务生成之前，先问我。

【先读，按顺序】
1. docs/Stage1/00_technical_plan.md：技术方案，Stage1 的执行标准。写任务说明以它为准；各项决定的理由在它的第 11 节。
2. docs/Stage1/02_implementation_status.md：代码现状、重写时要用的环境事实与经验、委托 Codex 的做法。
3. 需要讨论经过或依据时，查 docs/Stage1/01_design_discussion.md（00 各节末尾注明了对应的章节）。整体设计见 VPM_idea.md §3。

【这次要做的】
按 00 第 10.3 节的实现阶段推进，从 M1（核心）开始：写 M1 的任务说明，交给 Codex，审查结果。M1 用合成数据测试，不用 GPU，用默认沙箱。每完成一个实现阶段，停下来向我汇报。

【做法】
- 中文，技术名词用英文；标注【事实】【推导】【假设】【决定】【待定】；不用打分表；需要我决定的地方停下来，等我决定。
- 写代码按我的 CLAUDE.md 交给 Codex（codex-delegate 技能）：你写任务说明、审查结果；审查通过后不自动提交，等我说；同一任务返工两次仍不行，停下来告诉我。
- 用 GPU 的阶段（M2 起）用 danger-full-access 沙箱交给 Codex，交出去时说明“这次关了沙箱”：交出去前工作区要干净；用 nvidia-smi 挑空闲的卡，用 CUDA_VISIBLE_DEVICES 指定；只改项目目录内的文件，不装包，不改 conda 环境与 ManiSkill。
- 同一个进程里不要两次创建 GPU 场景，否则 SAPIEN 会崩溃；命令前加 ulimit -c 0，并把 XDG_CACHE_HOME 指到 outputs/cache。其余环境事实见 02。
- 新的决定先改 00（包括它附录 B 的修改记录），再在 01 中记下讨论经过。决定写进文档，记忆里只放指针。

【其他待办】
- docs/Stage1/03_idea_session_messages.md：给 idea 会话的一份合并消息（28 处要改、2 处建议补充），等我转。
- PullCubeTool 的 evaluate() 中自带 reward 与进度公式，输入包生成程序会报错停下，到时由我决定怎么处理。
```
