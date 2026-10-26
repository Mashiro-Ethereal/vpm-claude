# 新会话的交接说明（2026-10-26）

> **用途：** 换新会话继续 Stage1 时，把下面代码块中的文字原样贴到新会话的第一条消息。
>
> **状态：** 2026-10-26 改为“PickCube 效果的验证与调整”会话的交接说明。PickCube 试跑（M1–M5 与 DeepSeek 试跑）已经做完；生成的 teacher 能接入 RL 训练，但用它的 PBRS 奖励学不会 PickCube。前一版（PickCube 试跑会话）留在 git 历史中（df892b1），更早的版本见 09234cf、d253b71。

```text
这是 VPM 项目 Stage1（在 ManiSkill 上自动构建过程 teacher）的接续会话，专门验证并调整 PickCube 上 teacher 作 RL 奖励的效果。PickCube 试跑已经做完：M1–M5 都已提交，DeepSeek 生成的 teacher 第 1 轮就通过了两层检查。这个 teacher 能接入 PPO 和 SAC，但用它的 PBRS 奖励，PPO 在 1000 万步内一直没学会 PickCube：γ = 0.8 与 0.99、成功奖励 1 与 10、Φ 除以 K 与不除以 K 都试过（后两项只在 γ = 0.99 下试过）。同样设置下，ManiSkill 的稠密奖励在 γ = 0.8 时能学会。SAC 那次还在跑。这次要弄清原因，找到能学会的用法。

【硬约束】
- /home/zxh/projects_dir/vpm-claude 是我们唯一的工作目录，未经允许不要访问这台服务器上的其他位置，如果确实需要访问其他位置必须得到我的允许。例外：conda 环境 vpm-mani 可以只读使用（其中的 mani_skill 3.0.1 以可编辑方式装自 /home/zxh/projects_dir/ManiSkill，也只读，可以读它的源码），不装包、不改环境。
- 不要修改设计文档（VPM_idea.md 和 docs/ 下的文件），docs/Stage1/ 除外。遇到需要改动整体设计的问题，记在 01 §5，告诉我，讨论之后再决定。
- 不使用 /home/zxh/projects_dir/vpm（以前的失败尝试）。
- 提交前先问我；不推送；不合并到 master。当前分支是 stage1-impl。references/ 整个不进 git。
- DeepSeek 版 Claude Code（/home/zxh/.local/bin/claude-deepseek）只由 harness 的代码调用：不读包装脚本的源码；它的配置文件含密钥，不读取、不打印、不记录；不打印环境变量的值，需要时只列名字。
- 调用 DeepSeek（例如重新生成 teacher）和下载任何资产之前，先问我。PickCube 用不到需要下载的资产。
- 0 号卡上有别的用户的任务，不要用。训练用 1、2、3 号卡，用前先用 nvidia-smi 看是否空闲。
- wandb：项目 vpm-stage1，团队用我的默认账号，在线模式；登录由我处理。不要读取或打印凭据，不要运行 wandb login。冒烟测试用离线模式。

【开始前】
- git status 应该干净，git log 里有 58117bd（第三轮检验的代码）和其后的文档提交（含这份交接说明）。不是这样就停下来问我。
- 看第三轮的 SAC 是否跑完：3 号卡上的进程（ps、nvidia-smi），以及输出目录里有没有 eval.json（07 第 8 节）。没跑完就等它跑完，不要停掉它。

【先读，按顺序】
1. docs/Stage1/07_ppo_check.md：PPO 接入检查的全部经过：设置、三轮结果、两次分析、可做的检验。
2. docs/Stage1/01_design_discussion.md：§5 中“teacher 作 RL 奖励时，PBRS 在 PPO 上学不动”一条；§4.19（成功奖励 r_bonus）；§4.20（先做 PPO 接入检查、wandb 的配置）。
3. docs/Stage1/00_technical_plan.md 第 4.6 节（PBRS 的定义，成功终止与截断时怎么自举）；VPM_idea.md §3.3（teacher 作奖励的规则）。
4. docs/Stage1/02_implementation_status.md：代码现状（第 8 节）、环境事实与经验（第 3、4 节）、委托 Codex 的做法（第 7 节）。
5. 需要时再读：docs/Stage1/06_pickcube_trial.md（生成的候选与参照候选的对比）；references/notes/base_progress_reward.md（PRM4RL 的做法：Φ 不除以 K、策略看得到阶段、用 SAC 或小规模 PPO）。

【现状】
- teacher：outputs/stage1/runs/PickCube-v1/20261026-184803/records/round_1/candidate（reach、grasp、carry、hold 四个阶段）。人写的参照候选：candidates/reference/PickCube-v1/。
- 训练脚本：scripts/ppo_check.py（照官方 ppo.py 改写）与 scripts/sac_check.py（照官方 sac.py 改写），奖励可选 teacher、dense、sparse。两者都只建一个 GPU 环境，默认只对截断自举，训练后在同一环境上做确定性评估，记下 train.jsonl 与 eval.json，可接 wandb。PBRS 包装在 vpmkit/rewards/pbrs.py，phi_scale 可以放大 Φ。
- 运行记录在 outputs/stage1/ppo_check/（不进 git）。交给 Codex 的任务说明与汇报在 outputs/stage1/codex/<步骤>/；其中 ppo_analysis/brief.md 是分析训练记录的任务说明，可以照着写。

【这次要做的】
1. SAC 跑完后，把第三轮三次训练的分析交给 Codex（只读），核对关键数字后更新 07，向我汇报。问题至少包括：
   - 每次的训练成功率、最终评估（剔除“方块一开始就在目标附近”的平凡成功，做法见 07 第 2 节）、策略熵、阶段占比与平均 Φ 随步数的变化；
   - 两次 PPO 与第 5 节的 teacher 那次（成功奖励 1）比：退化到 reach 的时间与过程有没有变化，Φ 放大后前期进入 grasp、carry 的比例有没有增加；
   - SAC 学会了接近、抓取、搬运中的哪几步，Q 值的量级与 Φ、成功奖励是否相符；
   - 有没有像程序错误的地方，如奖励与记下的 Φ、塑形项、成功奖励对不上，回放中的自举标记不对；
   - 建议与事实分开写。
2. 和我讨论原因与下一步的检验，一次只提一点。可选的方向（07 第 6、7 节，01 §5）：
   - 策略的输入拼上 teacher 的阶段（PRM4RL 的做法）；
   - 用参照候选跑同样的设置，分清问题出在生成的 teacher，还是出在 PBRS 的用法；
   - grasp 段的守卫是布尔的，没有阶段内进度，near 的阈值又宽（约 5.5 cm）；
   - SAC 是否照官方不在成功时结束回合；γ 与并行环境数（PRM4RL 的小规模 PPO 只用 8 个环境）。
   每次检验先说明改什么、为什么，问我之后再跑。
3. 找到能学会的用法后，如果要改 00 第 4.6 节或 VPM_idea §3.3，先记入 01 §5，和我讨论之后再定。
- 不做的：其余 15 个任务（05 第 9 节，等 PickCube 有结论再说）；重新生成 teacher（除非确认问题出在 teacher 本身，并且我同意）。

【做法】
- 中文，技术名词用英文；标注【事实】【推导】【假设】【决定】【待定】；不用打分表；需要我决定的地方一次只提一点，停下来等我决定。
- 写代码按我的 CLAUDE.md 交给 Codex（codex-delegate 技能）：你写任务说明、审查结果（逻辑代码逐行看 diff，自己重跑测试）；审查通过后不自动提交，等我说；同一任务返工两次仍不行，停下来告诉我。
- 读训练记录、分析原因的活也交给 Codex，用只读模式：你写问题，核对关键数字。Codex 的只读沙箱看不到主机进程和 GPU，查进程、看卡用几条只读的 ps、nvidia-smi 命令自己查。
- 用 GPU 的任务用 danger-full-access 沙箱交给 Codex，交出去时说明“这次关了沙箱”：交出去前工作区要干净；用 CUDA_VISIBLE_DEVICES 指定卡；只改项目目录内的文件，不装包，不改 conda 环境与 ManiSkill。
- 同一个进程里不要两次创建 GPU 场景，否则 SAPIEN 会崩溃。命令前加 ulimit -c 0，并把 XDG_CACHE_HOME、MS_ASSET_DIR、TMPDIR 指到 outputs/ 下。长时间的训练用 setsid nohup 脱离会话启动，日志写在输出目录旁的 .log；正常运行的训练不要停掉。
- 结果记进 07（篇幅大了可另开 08）；代码有改动时更新 02；新的决定先改 00（包括附录 B 的修改记录），再在 01 中记下讨论经过，05 随之更新。决定写进文档，记忆里只放指针。要换会话时，更新 04 的交接说明。

【其他待办（这一步不做）】
- 第二层审查用了时间上限的八成（06 第 4.2 节），扩展前要定是否放宽。
- 扩展到其余 15 个任务（05 第 9 节）。
```
