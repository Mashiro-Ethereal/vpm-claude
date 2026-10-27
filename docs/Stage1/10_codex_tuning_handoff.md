# 给 Codex 的调参交接说明（2026-10-27）

> **用途：** 把 PickCube 上的调参交给 Codex 单独做。此前由 Claude 的会话主持调参（[07](07_ppo_check.md) 第 11 节）；从这份说明起，由 Codex 定配置、跑实验、分析、定下一组，并向用户汇报。
>
> **怎么用：** 在仓库根目录启动 Codex。它要用 GPU，还要联网给 wandb 上传记录，所以沙箱要用 danger-full-access：
>
> ```bash
> cd /home/zxh/projects_dir/vpm-claude && codex --sandbox danger-full-access
> ```
>
> 第一句话说：“读 `docs/Stage1/10_codex_tuning_handoff.md`，照它做。”下面是写给 Codex 的。

## 1. 任务

- **目标：** 用生成的 PickCube teacher 作奖励，让 PPO 在 PickCube-v1 上学会：一个配置的 3 个种子，各训练 100 万步，最终评估的成功率平均高于 95%。
  - 最终评估是 500 个确定性回合，剔除平凡成功（方块一开始就在目标点 2.5 cm 以内）。看 `eval.json` 的 `without_trivial.success_once`。
- **你主持调参：** 在第 2.2 节的范围内定每一组的配置；需要时改脚本；启动训练，分析结果，再定下一组。每组都记进 `docs/Stage1/11_tuning_log.md`（由你新建），并向用户汇报。
- **什么时候停下来：** 达到目标，或者遇到第 2.3 节列出的情况。停下来就汇报，等用户决定。

## 2. 规则

### 2.1 硬约束（照 04 的交接说明，一直有效）

- “`/home/zxh/projects_dir/vpm-claude` 是我们唯一的工作目录，未经允许不要访问这台服务器上的其他位置，如果确实需要访问其他位置必须得到我的允许。例外：conda 环境 vpm-mani 可以只读使用（其中的 mani_skill 3.0.1 以可编辑方式装自 `/home/zxh/projects_dir/ManiSkill`，也只读，可以读它的源码），不装包、不改环境。”
- “不要修改设计文档（`VPM_idea.md` 和 `docs/` 下的文件），`docs/Stage1/` 除外。遇到需要改动整体设计的问题，记在 01 §5，告诉我，讨论之后再决定。”
- “不使用 `/home/zxh/projects_dir/vpm`（以前的失败尝试）。”
- “提交前先问我；不推送；不合并到 master。当前分支是 stage1-impl。`references/` 整个不进 git。”
- “DeepSeek 版 Claude Code（`/home/zxh/.local/bin/claude-deepseek`）只由 harness 的代码调用：不读包装脚本的源码；它的配置文件含密钥，不读取、不打印、不记录；不打印环境变量的值，需要时只列名字。”
- “调用 DeepSeek（例如重新生成 teacher）和下载任何资产之前，先问我。PickCube 用不到需要下载的资产。”
- “0 号卡上有别的用户的任务，不要用。训练用 1、2、3 号卡，用前先用 nvidia-smi 看是否空闲。”
- “wandb：项目 vpm-stage1，团队用我的默认账号，在线模式；登录由我处理。不要读取或打印凭据，不要运行 wandb login。冒烟测试用离线模式。”

### 2.2 调参的范围

用户已经定的【决定，07 第 11.1、11.7 节】：
- 只用 PPO，不用 SAC。
- 只用现有的环境输入：策略的输入不拼子任务嵌入，不下载 SimCSE，不完整复现 PRM4RL。
- 必要时可以改 teacher 的接近阈值。
- 每次运行只训练 100 万步：“统一只训练到 100 万步即可。再多的训练没有意义了，我们先看个早期趋势，有表现比较好的再说。”

据此，你可以自己定的：
- PPO 的超参数：学习率与退火、KL 阈值、clip、epoch 数、minibatch、并行环境数与每轮步数、熵系数、log_std 初值、输出层的增益、value loss 系数、梯度裁剪、γ 与 GAE λ。
- 奖励包装的选项：`--shaping-scale`、`--r-bonus`、`--shaping-gamma`、`--terminal-phi`、`--shaping-clip`、`--phi-scale`、`--reward-scale`。
- 接近阈值：只用 `--teacher-param near.max_dist=<值>`，在 teacher 声明的范围 [0, 0.05] 内（默认 0.02），不改候选的文件。
- CPU 仿真还是 GPU 仿真；种子；同一配置下用 `--reward dense` 或 `--reward sparse` 跑对照。

### 2.3 要先问用户的

- 第 2.2 节以外的改动，包括：
  - 换算法；
  - 改策略的输入，包括拼上 teacher 的阶段；
  - 改 teacher 的其他参数（如 `progress.*.d0`、`runtime.debounce`）；
  - 改候选的文件（谓词、progress、stage graph）；
  - 改 `vpmkit/` 中 teacher 的运行语义（`teacher.py`、`automaton.py` 等）。
- 单次训练超过 100 万步。
- 重新生成 teacher（要调用 DeepSeek）。
- 提交代码或文档。
- 怀疑有程序错误，例如奖励与记下的 Φ、塑形项、成功奖励对不上。
- 连续两组都没有比当时最好的配置更好。这时先写下分析和可选的方向，再问用户。

### 2.4 能改的文件

- 可以改：
  - `scripts/ppo_tune.py` 与 `tests/unit/test_ppo_tune.py`；
  - `vpmkit/rewards/pbrs.py` 与 `tests/unit/test_pbrs.py`，只能加按关键字传的新选项，默认行为逐位不变；
  - 新建并维护 `docs/Stage1/11_tuning_log.md`；
  - `outputs/` 下的文件。
- 改了代码，就重跑全部单元测试（命令见第 6.4 节），全部通过才能用来训练；在记录里写明改了什么。
- 其余文件都不改，包括 `docs/Stage1/` 下的 00–10、`scripts/teacher_check.py` 等其他会话的文件。设计层面的问题按第 2.1 节记入 01 §5；改 01 之前先看它的最新内容，不要覆盖别人的改动。

### 2.5 资源

- GPU：只用 1、2、3 号卡，用前看 `nvidia-smi`；每张卡同时最多跑 3 个训练进程，与此前的用量相同。
- CPU：CPU 仿真的运行每个占 1 个核（`--torch-threads 1`）；同时跑的不超过 24 个。机器有 64 个核。
- 不停掉不是你启动的进程。

## 3. 开始前

1. `git status`：除了你自己的 `11_tuning_log.md`，不应有未提交的改动。有的话停下来问用户，因为你要在关掉沙箱的情况下改代码、跑训练。
2. 查有没有正在跑的训练：

   ```bash
   ps -eo pid,etime,args | grep "[p]po_tune.py" | sed -E 's/.*(--out [^ ]+).*/\1/'
   ```

   有的话，不要动它们，问用户。2026-10-27 09:30（JST）时还在跑的有两批：
   - 第三组的 3 个 CPU 运行：启动时设的是 400 万步，按用户的决定要在约 100 万步时停，约 09:50 到；
   - 第四组按 100 万步重开的 6 个 GPU 运行（AB64 与 B64），预计 10:00 前跑完。
3. 按第 4 节读背景。

## 4. 背景：先读什么

1. **[07](07_ppo_check.md)：** 全文，重点是第 6 节（PBRS 在 PPO 上学不动的解释）、第 9 节（第三轮的分析）、第 10.1 节（PRM4RL 代码中的实际设置）和第 11 节（调参到现在的全部经过）。07 可能还在被更新，以工作区的最新内容为准。
2. **[08](08_teacher_check.md)：** 结论与第 3 节。teacher 作为进展的度量基本没问题，弱点在设计层面：
   - grasp 段的 Φ 不变；
   - 搬运中抓取读数闪断一步，阶段就从 carry 退回 grasp（m = 1）；
   - 离方块 30 cm 以外 Φ = 0。

   这些不在调参范围内改（接近阈值除外），但分析现象时会用到。
3. **[09](09_code_reading_handoff.md) 第 3–5、8 节：** 代码地图、训练时一步之内的数据流、测试命令。09 第 1 节是给阅读会话的规则，不适用于你。
4. **设计的依据：** [00](00_technical_plan.md) 第 4.6 节（PBRS 的定义，成功终止与截断时怎么自举）；`VPM_idea.md` §3.3。调参用的奖励不是势函数形式，不符合 §3.3 第 1 条（07 第 11.2 节）：这是用户为调参定的，可以照用；最后若要采用，要先记入 01 §5 讨论。

## 5. 到现在为止的经过（摘要，细节以 07 为准）

【事实】
- **PBRS（第 1–3 轮）：** 奖励 R = γΦ(s′) − Φ(s) + 成功 × r_bonus，Φ ∈ [0, 1]，用官方的 GPU PPO（1024 个环境）。γ = 0.8 与 0.99、成功奖励 1 与 10、Φ 放大 4 倍都试过，1000 万步内都没学会，最后都退回 reach，夹爪离方块越来越远。同样设置下，环境的稠密奖励在 γ = 0.8 时达到 99.4%。SAC 那次在 γ = 0.99 下发散。
- **调参第一组：** 照 PRM4RL 代码中的 SB3 PPO 设置：1 个环境、CPU 仿真、每次更新 3200 步、15 个 epoch、学习率 2e-4、γ 0.8，控制 `pd_ee_delta_pos`。奖励 r = 10 × (Φ′ − Φ) + 50 × 成功，Φ = k + p_k ∈ [0, 4]，Φ 的差不打折扣，成功那一步的 Φ′ 取实际值。三个种子都在 70 万步前学会（中途评估 10/10），但不稳定：种子 2 在约 84 万步崩溃过。
- **第二组**（约 100 万步时，最近 10 次中途评估的平均）：
  - A，学习率线性退火到 0：0.99、0.99、0.99；
  - B，奖励整体缩小 10 倍（塑形系数 1、成功奖励 5）：0.98、1.00、0.97；
  - C，学习率 5e-5、KL 阈值 0.03：0.03–0.05，太慢；
  - D，PRM4RL 的裁剪形式 clip(10 × (0.8Φ′ − Φ), −1, 1) + 50 × 成功：0，一次也没成功。
  - 第一、二组后来在 100 万步以后被停掉，没有做 500 个回合的最终评估。
- **第三组（A 与 B 合用，CPU）：** 启动时设的是 400 万步，按用户的决定跑到约 100 万步时用 SIGINT 停。用 SIGINT 停掉的运行不做最终评估，第一、二组也是这样：只有 `eval.jsonl` 里的中途评估（每 12,800 步 10 个回合），以及最后一次中途评估时存下的 `latest.pt`。
- **第四组（GPU 多环境）：** 按 100 万步重开，跑完时做 500 个回合的最终评估（`eval.json`）。三个配置：
  - AB64：64 个环境 × 50 步，其余同第三组；
  - B64：同 AB64，学习率不退火；
  - AB1024：1024 个环境 × 50 步，32 个 minibatch、8 个 epoch、学习率 3e-4 退火、KL 阈值 0.1。每次更新 51,200 步，100 万步只够更新 19 次。
- 第三、四组的结果都还没有整理进 07。输出在 `outputs/stage1/ppo_tune/group3AB-seed{1,2,3}/` 与 `group4-{AB64,B64,AB1024}-1M-seed{1,2,3}/`。不带 `-1M` 的 `group4-*` 是按旧步数设定、中途停掉的，不用。

【待定】哪一个配置在 100 万步时最好；能不能达到 95%；GPU 多环境能不能复现 CPU 单环境的学习效果。

## 6. 工具

### 6.1 `scripts/ppo_tune.py`

- 从官方 `ppo.py` 改写，默认值是第一组的设置。开头的 docstring 与 `parse_args` 里写着全部选项。
- 奖励由 `PBRSWrapper` 算，再乘以 `--reward-scale` 交给 PPO：
  - 塑形 = shaping_scale × (shaping_gamma × Φ_used(s′) − Φ(s))，有 `--shaping-clip` 时再裁剪；
  - 奖励 = 塑形 + 成功 × r_bonus；
  - Φ = phi_scale × teacher 的 Φ。teacher 的 Φ ∈ [0, 1]；phi_scale 默认等于阶段数 4，所以 Φ ∈ [0, 4]；
  - `--terminal-phi keep`（默认）时，成功那一步的 Φ_used(s′) 取实际值；`zero` 时取 0。
- 默认值：shaping_scale 10，r_bonus 50，shaping_gamma 1，terminal_phi keep。第三、四组用的是 shaping_scale 1、r_bonus 5。
- 只对截断自举，成功终止不自举（`--no-bootstrap-terminations`，默认）。
- CPU 仿真只能 1 个环境，另建一个评估环境，每 12,800 步做 10 个确定性回合的中途评估。GPU 仿真必须 `--eval-freq 0`：同一进程里不能建第二个 GPU 场景，所以只在训练结束后用训练环境做最终评估。
- 输出目录里有：`config.json`；`train.jsonl`（每次更新一行，含阶段占比、塑形项均值等）；CPU 运行还有 `eval.jsonl` 与 `latest.pt`、`best.pt`；训练结束后有 `eval.json`（500 个回合，逐回合的记录在 `per_episode`）与 `final_model.pt`。

### 6.2 启动

都在仓库根目录、用 vpm-mani 的 Python。长时间的训练用 `setsid nohup` 脱离会话启动，日志写在输出目录旁的同名 `.log`。启动后记下 PID 和预计跑完的时间。

GPU 运行的例子（`ppo_tune.py` 的参数照抄第四组 B64 种子 1 的实际运行；用时换成新的取值、卡号与目录）：

```bash
cd /home/zxh/projects_dir/vpm-claude && ulimit -c 0 && CUDA_VISIBLE_DEVICES=2 setsid nohup /home/zxh/anaconda3/envs/vpm-mani/bin/python -u scripts/ppo_tune.py --reward teacher --candidate outputs/stage1/runs/PickCube-v1/20261026-184803/records/round_1/candidate --sim-backend gpu --device cuda --torch-threads 1 --control-mode pd_ee_delta_pos --gamma 0.8 --gae-lambda 0.9 --clip-coef 0.2 --ent-coef 0.0 --vf-coef 1.0 --max-grad-norm 0.5 --norm-adv --no-clip-vloss --init-logstd 0.0 --action-head-gain 0.01 --value-head-gain 1.0 --no-finite-horizon-gae --no-bootstrap-terminations --phi-scale 4 --terminal-phi keep --shaping-gamma 1.0 --shaping-scale 1.0 --r-bonus 5.0 --eval-freq 0 --final-eval-episodes 500 --total-timesteps 1000000 --track --wandb-project vpm-stage1 --wandb-group pickcube-tuning --wandb-mode online --num-envs 64 --num-steps 50 --num-minibatches 8 --update-epochs 15 --learning-rate 0.0002 --target-kl 0.15 --no-anneal-lr --seed 1 --out outputs/stage1/ppo_tune/group4-B64-1M-seed1 > outputs/stage1/ppo_tune/group4-B64-1M-seed1.log 2>&1 &
```

- CPU 运行：改成 `--sim-backend cpu --device cpu --num-envs 1`，用 `--eval-freq 12800 --eval-episodes 10` 做中途评估。
  - `CUDA_VISIBLE_DEVICES` 也要设成 1–3 号卡之一：此前的 CPU 运行在可见的卡上各占约 24 MiB 显存。
  - 不设的话所有卡都可见，这块显存可能落到 0 号卡上。【推导】
- 脚本自己把 `XDG_CACHE_HOME`、`MS_ASSET_DIR`、`TMPDIR` 设到 `outputs/` 下。
- 新的运行都设 `--total-timesteps 1000000`，让脚本自己跑完并做最终评估。不要靠 SIGINT 停：那样不做最终评估。
- 命名：`outputs/stage1/ppo_tune/group<n><配置名>-1M-seed<s>`，n 从 5 起。wandb 分组都用 `pickcube-tuning`。
- 冒烟测试用很小的 `--total-timesteps`，加 `--wandb-mode offline` 或不加 `--track`。

### 6.3 速度（实测，带 teacher）

- CPU 单环境：每秒约 95–125 步，100 万步约 2.2–3 小时；同时跑的进程多时偏慢。
- GPU 64 个环境（三个进程共用一张卡）：每个每秒约 400 步，100 万步约 42 分钟。
- GPU 1024 个环境：每秒约 4400 步，100 万步约 4 分钟。
- GPU 只开 1 个环境时比 CPU 慢约 4.5 倍（07 第 11.6 节）。

### 6.4 单元测试

```bash
cd /home/zxh/projects_dir/vpm-claude && mkdir -p outputs/tmp && ulimit -c 0 && TMPDIR=$PWD/outputs/tmp XDG_CACHE_HOME=$PWD/outputs/cache MS_ASSET_DIR=$PWD/outputs/maniskill CUDA_VISIBLE_DEVICES="" /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/unit -t . -v
```

### 6.5 已知的环境事实

- 一个进程里第二次创建 GPU 场景，SAPIEN 会崩溃。
- GPU 仿真重置后的第一个状态上，抓取读数是旧的，会进入策略的第一个观测（02 第 4 节第 12 条）。所以在训练进程里做的评估，换一个进程不能逐步复现。
- 用 GPU 仿真的进程，即使 `CUDA_VISIBLE_DEVICES` 指了别的卡，也会在 0 号卡上建一个约 4 MiB 的图形上下文。这不是残留进程，不用处理（02 第 4 节第 10 条）。
- 其他环境事实与经验见 [02](02_implementation_status.md) 第 3、4 节。

## 7. 建议的做法

1. **先整理起点：** 分析第四组的最终评估，以及第一、二、三组在 100 万步附近的中途评估，写成 11 的第一节。
   - 按配置列出各种子的成功率，以及到达各阶段的情况与学习曲线的走向。
   - 中途评估只有 10 个回合，与 500 个回合的最终评估分开写。
   - 要给第三组补 500 个回合的评估，可以在 `ppo_tune.py` 里加一个只评估 checkpoint 的选项（CPU、单环境），评估它的 `latest.pt`。
2. **每组只改一两处：** 以当时最好的配置为基线；每个配置跑 3 个种子（1、2、3）。启动之前，在 11 里写下改什么、为什么、预期会看到什么。
3. **一组跑完：**
   - 记下事实：设置、命令、wandb 的 run、结果的数字；
   - 写分析：哪些是推导，哪些是假设；
   - 写下一组的决定和理由；
   - 向用户简短汇报。
4. **汇报与记录的写法：** 中文，技术名词用英文；标【事实】【推导】【假设】【决定】【待定】；不用打分表。

## 8. 记录：`docs/Stage1/11_tuning_log.md`

- 开头写用途与当前结论（哪个配置最好、离目标还差多少），每组跑完更新。
- 每组一节：设置（与基线的差别）、命令、wandb 的 run、结果、分析、下一步。
- 文末一节“待讨论”：需要用户决定或涉及设计的问题。
