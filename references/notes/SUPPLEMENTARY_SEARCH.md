# 补充检索记录

日期：2026-10-06。检索由已有阅读中暴露的问题驱动；只将读取的原始来源用于研究结论。初始150篇的获取地址在各篇笔记中。

## 主智能体检索

- 目的：核对TPAMI范围及与视觉/具身/一般RL的实际联系。
- 查询：`site.computer.org IEEE Transactions on Pattern Analysis and Machine Intelligence scope robotics machine learning`；`"TPAMI" "robotic manipulation" "reward"`；`"TPAMI" "reward learning"`；`"TPAMI" "robot" "2025" reinforcement`；`"Constraint-Aware Zero-Shot Vision-Language Navigation" TPAMI`；`"On the Benefit of Optimal Transport for Curriculum Reinforcement Learning"`。
- 使用来源：IEEE Computer Society官方范围、CA-Nav作者原文与代码库、Klink等作者接受稿与DFKI机构书目。分别建立阅读笔记，见TPAMI_SCOPE.md。
- 顺带检索到JARVIS-1并读取作者项目页摘要；仅作邻接领域初筛笔记。检索中的其他无关页面不作为入选证据。

## 从进度到可达性

- 查询：`Dynamical Distance Learning`、`Replacing Rewards with Examples Recursive Classification`，并沿成功示例与视觉奖励的原文相关工作追溯。
- 读取：DDL 正文方法、实验和理论条件；RCE 正文方法、假设和实验。分别保存为 `added_hartikainen2020_ddl.md`、`added_eysenbach2021_rce.md`。
- 对判断的影响：时间距离、未来成功预测和成功示例分布假设已有明确研究；不能以更名 progress/reachability 作为新贡献。

## 主动观察与奖励验证

- 查询：`robot active success verification vision`、`robot active task verification language`、`robot reward viewpoint verification`、`reward model active sensing robot`、`Training Robots to Evaluate Robots`、`Know Where You're Uncertain When Planning`。
- 读取：LIRF 正文与关键附录；MLSys 2025 不确定性分解与主动观察方法/实验；WoMAP 作者项目；Adaptive querying 正式摘要、方法概述与问题设置。
- 对判断的影响：互动奖励、按不确定性重观测、信息价值与查询成本分别已有基础，后续需研究这些观察是否实际改变任务判断/学习，以及同等成本下的收益。

## 奖励学习效用与候选选择

- 查询：`reward model evaluation downstream predict robotics`、`reward design bi-level`、`reward shaping meta-gradient`、`reward selection multi-fidelity`、`On Learning Intrinsic Rewards for Policy Gradient Methods`、`Exploration-Guided Reward Shaping`；技术结论仅采用论文原始来源。
- 读取：LIRPG 核心方法和实验设置；ExploRS 摘要与方法片段；URDP、RE-GoT、Language-Model-Assisted Bi-Level Programming 的完整作者摘要。与集合内 ORSO、CARD、LaRes、FLORA、MLREF、RoboReward、EPIC/DARD 交叉比较。
- 对判断的影响：按下游收益优化奖励、短训分配预算、用离线代理筛选均非空白。候选问题收窄到在给定学习器和预算下，能否跨奖励家族与任务预测相对学习效用。

以上是问题驱动的补检索，不是穷尽数据库的系统综述。搜索返回但未进入实际阅读的无关条目不计为已读文献。各主题代理的补充查询与新文献记录见其 `cluster_*.md` 和 `added_*.md`。
