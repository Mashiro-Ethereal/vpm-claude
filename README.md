# VPM：阶段化任务过程模型的构建、优化与视觉迁移

## 项目目标

承接 PRM4RL 与 RF-Agent，研究阶段化任务过程模型的自动构建、反馈优化与视觉迁移，为机器人学习与执行提供过程反馈，目标期刊为 IEEE Transactions on Pattern Analysis and Machine Intelligence（TPAMI）。

## 当前状态（2026-10-17）

idea 已定稿于 [VPM_idea.md](VPM_idea.md)。Stage1 的设计与实现在单独的会话中进行，代码将放在本项目。

## 目录说明

- [README.md](README.md)：项目入口，说明当前状态、阅读顺序和工作约定。
- [VPM_idea.md](VPM_idea.md)：唯一的权威设计，记录 VPM 的总体路线与已定稿的决定。
- [docs/](docs/)：存放对话总结、探索过程和历史版本。
- [docs/00_conversation_digest.md](docs/00_conversation_digest.md)：记录讨论时间线、决策理由和恢复上下文所需的信息。
- [docs/exploration/](docs/exploration/)：保留文件名不变的 01–07 七份过程文档。
- [docs/archive/](docs/archive/)：保存初始化 git 之前 VPM_idea 的九个历史版本。
- [references/](references/)：集中存放原文、阅读笔记和文献索引。
- [references/own_papers/](references/own_papers/)：存放 [PRM4RL 原文](references/own_papers/Progress_reward_model_for_RL.pdf)和 [RF-Agent 原文](references/own_papers/RF_Agent.pdf)。
- [references/notes/](references/notes/)：存放文献阅读笔记及主题综合。
- [references/notes/_sources/](references/notes/_sources/)：保存原文提取、图表和检索记录等来源材料。
- [references/references.bib](references/references.bib)：保存 BibTeX 书目。
- [references/sources.csv](references/sources.csv)：保存论文、DOI、代码及项目页面等来源索引。
- [.gitignore](.gitignore)：规定原文 PDF、来源材料、实验产物和开发缓存等文件的忽略规则。

## 阅读顺序

[对话总结](docs/00_conversation_digest.md) → [VPM_idea.md](VPM_idea.md) → [07 优化建议与讨论](docs/exploration/07_vpm_optimization.md)、[06 构想评审](docs/exploration/06_vpm_idea_review.md) → [05 五个方向](docs/exploration/05_five_directions.md)、[04 八篇精读](docs/exploration/04_close_reading_8papers.md)、[02 文献综述](docs/exploration/02_literature_review.md)、[03 候选方向](docs/exploration/03_candidate_directions.md)。

文献入口是 [references/notes/README.md](references/notes/README.md)。

## 约定

- VPM_idea.md 是唯一的设计依据，修改需经用户确认。
- 文档用中文。
- 代码放在项目根目录下的代码包、`configs/`、`scripts/`、`tests/`；实验产物放在 `outputs/`，不进版本管理；大文件不进 git。这些代码与实验目录按实现需要创建。
- `/home/zxh/projects_dir/vpm` 是废弃的旧实现，不作参考；`vpm-v2` 中的材料，使用前要先经用户确认。
- 初始化 git 之前的版本历史保存在 [docs/archive/](docs/archive/)。

## 工作原则

- 项目背景以本目录和用户当前明确提供的资料为准。
- 分别标明事实依据、工作假设和用户决定，尚未确定的事项保持开放。
- 引用文献结论时核对原始来源，准确说明实际阅读范围。
- 用具体理由比较候选方向，避免用评分表代替研究判断。
- 根据实际问题选择必要的方法与验证，保持工作范围与当前任务相称。

## 辅助检索材料

- [sources.csv](references/sources.csv)：已有文献的论文、DOI、代码及项目页面等来源索引。
- [references.bib](references/references.bib)：对应的 BibTeX 书目。

这些材料作为检索入口，按具体研究问题选用。书目信息与研究结论应核对原始来源，并按需要补充检索。

## 阅读笔记

- [文献阅读笔记索引](references/notes/README.md)：原有 150 篇与补充 14 篇文献的逐篇入口、阅读范围和主题综合。
- [PRM4RL 精读笔记](references/notes/base_progress_reward.md)与[RF-Agent 精读笔记](references/notes/base_rf_agent.md)。
- [两篇已有工作的综合分析](docs/exploration/01_existing_work_synthesis.md)。

可先利用笔记定位相关方法与证据，再按需要查阅原文。笔记保留原阅读日期和范围，原文提取及图表等材料保存在 `references/notes/_sources/`。
