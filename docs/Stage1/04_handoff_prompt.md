# 新会话的交接说明（2026-10-21）

> **用途：** 换新会话继续 Stage1 时，把下面代码块中的文字原样贴到新会话的第一条消息。
>
> **状态：** 2026-10-21 改为“只写示例”：你的目标是先让 Stage1 在 PickCube 上走完一条完整的路径，这需要输入包里有示例，所以先新开一个会话写示例。示例不依赖 Stage1 的代码：它和 candidate_api.md 是规格，代码（M1 起）照它们实现。同日的上一版把 M1 也放进了这个会话，已改掉；更早的通用版（从 M1 开始）留在 git 历史中（d253b71）。

```text
这是 VPM 项目 Stage1（在 ManiSkill 上自动构建过程 teacher）的接续会话。设计已全部定完（G1 推迟）。实现的目标是先让 Stage1 在 PickCube 上走完一条完整的路径，再扩展到其余任务。走这条路径时，输入包里要有一个给 agent 参考的示例，所以这个会话只做一件事：写好这个示例（一个虚构的典型抓放任务），以及它所依据的接口说明 candidate_api.md。

现在还没有 Stage1 的代码，写示例也不依赖代码：示例和 candidate_api.md 是规格，之后的代码（M1 起）照它们实现。

【硬约束】
- /home/zxh/projects_dir/vpm-claude 是我们唯一的工作目录，未经允许不要访问这台服务器上的其他位置，如果确实需要访问其他位置必须得到我的允许。例外：conda 环境 vpm-mani 可以只读使用（其中的 mani_skill 3.0.1 以可编辑方式装自 /home/zxh/projects_dir/ManiSkill，也只读，可以读它的任务源码作参照），不装包、不改环境。
- 不要修改设计文档（VPM_idea.md 和 docs/ 下的文件），docs/Stage1/ 除外。遇到需要改动整体设计的问题，记在 01 §5，告诉我，讨论之后再决定。
- 不使用 /home/zxh/projects_dir/vpm（以前的失败尝试）。
- 提交前先问我；不推送；不合并到 master。当前分支是 stage1-impl。references/ 整个不进 git。
- 这一步不写 Stage1 的代码，不调用 DeepSeek，不下载资产，不用 GPU。

【先读，按顺序】
1. docs/Stage1/00_technical_plan.md：技术方案，执行标准。这一步重点看第 3、4、5 节（候选的写法、运行语义、设计规则）、第 6 节（输入包，尤其 6.2 场景清单、6.4 示例、6.5 输出）和第 8.2 节（第一层的静态规则）；各项决定的理由在第 11 节。
2. docs/Stage1/05_implementation_plan.md 第 4.1 节（“准备”这一步）。
3. docs/Stage1/01_design_discussion.md §4.11：示例为什么这样定。需要其他讨论经过时再查 01。
4. docs/Stage1/02_implementation_status.md：环境事实（欧拉角的约定、两种 is_static 的定义等）。

【这次要做的】
1. 先定接口，写 candidate_api.md（英文）：按 05 第 4.1 节，写文件格式、YAML 写法、世界视图与对象视图的字段、谓词装饰器、progress 的写法、运行语义和静态规则。绑定一节先按设想的接口写，M2 之后再按实际接口核对。
2. 写示例（英文），按 00 第 6.4 节：虚构的抓放任务（抓起方块、放到目标垫上、松手）。包括：
   - 按 ManiSkill 风格写的虚构 env_source.py（含 evaluate()），可以参照 vpm-mani 中真实任务的源码（如 pick_cube.py、stack_cube.py）；
   - 一小段场景清单，内容照 00 第 6.2 节（以后 M2 生成的场景清单照这个格式）；
   - 完整的候选：stage_graph.yaml、bindings.py、predicates.py、progress.py、notes.md。
   示例要严格遵守每一条设计规则，因为 agent 会照它的风格写。它可以和评测任务相似，不用刻意避嫌。
3. 自查，不依赖 Stage1 代码：Python 文件能编译，YAML 能解析，照 00 第 3–5 节和第 8.2 节逐条核对。完整的运行验证留到 M1：M1 拿示例作合法候选，在合成快照上跑。
4. 两者放在 vpmkit/resources/ 下（candidate_api.md 和 example/，见 05 第 3 节）。
5. 写完停下来给我看：示例的全部文件，以及你定下的接口（列一张清单，以后 M1 照它实现）。不要开始 M1。

【做法】
- 中文，技术名词用英文；标注【事实】【推导】【假设】【决定】【待定】；不用打分表；需要我决定的地方一次只提一点，停下来等我决定。
- 开始前先看 git status：工作区有未提交的改动，先问我是否提交。
- 允许使用 Codex（codex-delegate 技能，按我的 CLAUDE.md）；但示例和接口说明是规格，内容由你定。
- 新的决定先改 00（包括附录 B 的修改记录），再在 01 中记下讨论经过，05 随之更新。决定写进文档，记忆里只放指针。

【其他待办（这一步不做）】
- docs/Stage1/03_idea_session_messages.md：给 idea 会话的合并消息（27 处要改、2 处建议补充），等我转。
- 之后的步骤：M1（核心，示例作合法候选）→ M2（只做 PickCube）→ M3（PickCube 参照候选与第一层）→ M4（PickCube 试跑）→ M5，见 05。
```
