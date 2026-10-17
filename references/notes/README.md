# 文献阅读笔记索引

原阅读日期：2026-10-06；迁移整理日期：2026-10-15。

本目录收录两篇基础论文的精读笔记、原有 150 篇参考文献与补充 14 篇文献的阅读记录，以及主题综合和来源材料。

## 阅读入口

- [PRM4RL 独立精读笔记](base_progress_reward.md)。
- [RF-Agent 独立精读笔记](base_rf_agent.md)。
- [两篇已有工作的综合分析](../../docs/exploration/01_existing_work_synthesis.md)。
- 各篇文献的入口与实际阅读范围见下表；主题综合和检索记录见“主题证据与来源”。

## 覆盖与实际阅读深度

初始集合 **150/150** 条均已取得并实际读取原始摘要或正文，每篇均有以引用键命名的独立笔记：

- 两篇用户基础论文完整阅读正文及相关附录，另有详细基础笔记。
- 70 篇进一步阅读正文方法、实验或理论及必要附录；主要是选择性阅读，R*补读了正式正文与附录。
- 1 篇详细读取作者项目页（ROSETTA）；77 篇停留在原始摘要或引言/方法片段初筛。
- 另补充 14 篇，实际范围逐篇列于后表。初始集合的两篇基础论文不重复计数。

完整取得全文与完整阅读全文分别记录；上面的70篇不等于全部附录逐页读完。三组分工交叉形成主题，不作为方向评分或排名。

## 主题证据与来源

- [任务结构、理论、恢复与评价](cluster_structure_evaluation.md)：49篇；22篇重点正文阅读。
- [视觉、进度与过程奖励](cluster_visual_progress.md)：54篇；30篇重点正文阅读。
- [自动奖励搜索、平台与策略](cluster_search_policy.md)：47篇；含两基础篇、18篇重点正文及1篇作者项目页。
- [补充检索记录](SUPPLEMENTARY_SEARCH.md)、[TPAMI范围与实际发表依据](TPAMI_SCOPE.md)、[阅读方法与用户资源](READING_PROTOCOL.md)。

PDF/HTML/原始提取片段保存在 `_sources/`；各笔记中的实际来源链接和节、表、公式定位是结论依据。原始书目与用户论文未修改。

## 获取限制

ROSETTA正式PDF在网页和显式联网下载时仍受验证/HTTP403限制，采用作者完整项目页；SPARS与DyCoT-Re出版社正文受限，采用可取得的原始摘要/导言。GTCC使用CVF官方搜索返回的完整摘要。R*最初受工具限制，随后通过正式PMLR PDF补完，当前已非未读全文状态。详细障碍与版本见各篇笔记。

## 初始150篇逐篇入口

“正文重点”表示读到具体正文节，精确范围以笔记为准；年份取原书目，正式发表与预印本状态按笔记核验记录区分。

| 文献 | 书目年份 | 实际阅读层级 |
|---|---|---|
| [Policy Invariance Under Reward Transformations: Theory and Application to Reward Shaping](ng1999.md) | 1999 | 正文重点 |
| [Potential-Based Shaping and Q-Value Initialization are Equivalent](wiewiora2003.md) | 2003 | 摘要/初步正文 |
| [Between MDPs and Semi-MDPs: A Framework for Temporal Abstraction in Reinforcement Learning](sutton1999.md) | 1999 | 摘要/初步正文 |
| [Hierarchical Reinforcement Learning with the MAXQ Value Function Decomposition](dietterich2000.md) | 2000 | 摘要/初步正文 |
| [Using Reward Machines for High-Level Task Specification and Decomposition in Reinforcement Learning](icarte2018.md) | 2018 | 正文重点 |
| [Dynamic Potential-Based Reward Shaping](devlin2012.md) | 2012 | 摘要/初步正文 |
| [Reward Shaping in Episodic Reinforcement Learning](grzes2017.md) | 2017 | 正文重点 |
| [HPRS: Hierarchical Potential-Based Reward Shaping from Task Specifications](berducci2025.md) | 2025 | 摘要/初步正文 |
| [Text2Reward: Reward Shaping with Language Models for Reinforcement Learning](xie2024text2reward.md) | 2024 | 正文重点 |
| [Eureka: Human-Level Reward Design via Coding Large Language Models](ma2024eureka.md) | 2024 | 正文重点 |
| [Plan-Seq-Learn: Language Model Guided RL for Solving Long Horizon Robotics Tasks](dalal2024planseqlearn.md) | 2024 | 摘要/初步正文 |
| [Automated Rewards via LLM-Generated Progress Functions](sarukkai2024progress.md) | 2024 | 正文重点 |
| [RF-Agent: Automated Reward Function Design via Language Agent Tree Search](gao2025rfagent.md) | 2025 | 基础论文全文 |
| [Progress Reward Model for Reinforcement Learning via Large Language Models](zhang2025prm4rl.md) | 2025 | 基础论文全文 |
| [ELEMENTAL: Interactive Learning from Demonstrations and Vision-Language Models for Reward Design in Robotics](chen2025elemental.md) | 2025 | 摘要/初步正文 |
| [ROSETTA: Constructing Code-Based Reward from Unconstrained Language Preference](srivastava2026rosetta.md) | 2026 | 作者完整项目页 |
| [VIP: Towards Universal Visual Reward and Representation via Value-Implicit Pre-Training](ma2023vip.md) | 2023 | 正文重点 |
| [LIV: Language-Image Representations and Rewards for Robotic Control](ma2023liv.md) | 2023 | 正文重点 |
| [DrS: Learning Reusable Dense Rewards for Multi-Stage Tasks](mu2024drs.md) | 2024 | 正文重点 |
| [Subtask-Aware Visual Reward Learning from Segmented Demonstrations](kim2025reds.md) | 2025 | 正文重点 |
| [VICtoR: Learning Hierarchical Vision-Instruction Correlation Rewards for Long-horizon Manipulation](hung2025victor.md) | 2025 | 正文重点 |
| [SARM: Stage-Aware Reward Modeling for Long Horizon Robot Manipulation](chen2026sarm.md) | 2026 | 正文重点 |
| [General Process Reward Modeling for Robotic Reinforcement Learning](tan2026dopamine.md) | 2026 | 正文重点 |
| [Unpacking Failure Modes of Generative Policies: Runtime Monitoring of Consistency and Progress](agia2024sentinel.md) | 2025 | 摘要/初步正文 |
| [RARM: Confidence-Gated Progress Reward Modeling for RL in Manipulation](yang2026rarm.md) | 2026 | 正文重点 |
| [ProcVLM: Learning Procedure-Grounded Progress Rewards for Robotic Manipulation](feng2026procvlm.md) | 2026 | 正文重点 |
| [SARM2: Multi-Task Stage Aware Reward Modeling for Self Improving Robotic Manipulation](chen2026sarm2.md) | 2026 | 正文重点 |
| [GORDON: Graph-based Object-centric Rewards for Decomposition of Long-Horizon Manipulation](protopapa2026gordon.md) | 2026 | 正文重点 |
| [RoboProcessBench: Benchmarking Process-Aware Understanding in Vision-Language Robotic Manipulation](xia2026roboprocess.md) | 2026 | 摘要/初步正文 |
| [Progress Reward Modeling for Robotic Learning: A Comprehensive Survey](zhang2026survey.md) | 2026 | 摘要/初步正文 |
| [Asymmetric Actor Critic for Image-Based Robot Learning](pinto2018aac.md) | 2018 | 摘要/初步正文 |
| [Learning by Cheating](chen2020cheating.md) | 2020 | 摘要/初步正文 |
| [Demonstrating GPU Parallelized Robot Simulation and Rendering for Generalizable Embodied AI with ManiSkill3](tao2025maniskill3.md) | 2025 | 摘要/初步正文 |
| [LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning](liu2023libero.md) | 2023 | 摘要/初步正文 |
| [The Effects of Reward Misspecification: Mapping and Mitigating Misaligned Models](pan2022misspecification.md) | 2022 | 摘要/初步正文 |
| [Concrete Problems in AI Safety](amodei2016safety.md) | 2016 | 摘要/初步正文 |
| [Scaling Laws for Reward Model Overoptimization](gao2023overoptimization.md) | 2023 | 摘要/初步正文 |
| [The Perils of Optimizing Learned Reward Functions: Low Training Error Does Not Guarantee Low Regret](fluri2025perils.md) | 2025 | 正文重点 |
| [Temporal Cycle-Consistency Learning](dwibedi2019tcc.md) | 2019 | 摘要/初步正文 |
| [XIRL: Cross-embodiment Inverse Reinforcement Learning](zakka2022xirl.md) | 2022 | 正文重点 |
| [Video Prediction Models as Rewards for Reinforcement Learning](escontrela2023viper.md) | 2023 | 摘要/初步正文 |
| [RoboCLIP: One Demonstration is Enough to Learn Robot Policies](sontakke2023roboclip.md) | 2023 | 摘要/初步正文 |
| [Vision-Language Models are Zero-Shot Reward Models for Reinforcement Learning](rocamonde2024vlmrm.md) | 2024 | 摘要/初步正文 |
| [Video-Language Critic: Transferable Reward Functions for Language-Conditioned Robotics](alakuijala2025vlc.md) | 2025 | 摘要/初步正文 |
| [Vision Language Models are In-Context Value Learners](ma2025gvl.md) | 2025 | 正文重点 |
| [PROGRESSOR: A Perceptually Guided Reward Estimator with Self-Supervised Online Refinement](ayalew2025progressor.md) | 2025 | 正文重点 |
| [ReWiND: Language-Guided Rewards Teach Robot Policies without New Demonstrations](zhang2025rewind.md) | 2025 | 正文重点 |
| [Language to Rewards for Robotic Skill Synthesis](yu2023l2r.md) | 2023 | 摘要/初步正文 |
| [Learning Reward for Robot Skills Using Large Language Models via Self-Alignment](zeng2024selfalign.md) | 2024 | 摘要/初步正文 |
| [Neural Task Graphs: Generalizing to Unseen Tasks From a Single Video Demonstration](huang2019ntg.md) | 2019 | 摘要/初步正文 |
| [Learning Reward Machines for Partially Observable Reinforcement Learning](icarte2019learningrm.md) | 2019 | 正文重点 |
| [Reward Machines for Deep RL in Noisy and Uncertain Environments](li2024noisyrm.md) | 2024 | 正文重点 |
| [Privileged Sensing Scaffolds Reinforcement Learning](hu2024scaffolder.md) | 2024 | 正文重点 |
| [TOPReward: Token Probabilities as Hidden Zero-Shot Rewards for Robotics](chen2026topreward.md) | 2026 | 正文重点 |
| [Learning Language-Conditioned Robot Behavior from Offline Data and Crowd-Sourced Annotation](nair2022lorel.md) | 2022 | 摘要/初步正文 |
| [Graph Inverse Reinforcement Learning from Diverse Videos](kumar2023graphirl.md) | 2023 | 摘要/初步正文 |
| [VIRL: Self-Supervised Visual Graph Inverse Reinforcement Learning](huang2025virl.md) | 2025 | 摘要/初步正文 |
| [Adaptive Reward Design for Reinforcement Learning](kwon2025adaptive.md) | 2025 | 摘要/初步正文 |
| [Learning to Predict Activity Progress by Self-Supervised Video Alignment](donahue2024gtcc.md) | 2024 | 摘要/初步正文 |
| [ProgressCompass: Embodied Progress Reward Models Are Lost Without the Right Context](zhang2026progresscompass.md) | 2026 | 正文重点 |
| [Rewarding DINO: Predicting Dense Rewards with Vision Foundation Models](krack2026dino.md) | 2026 | 正文重点 |
| [ARM: Advantage Reward Modeling for Long-Horizon Manipulation](mao2026arm.md) | 2026 | 正文重点 |
| [ViVa: A Video-Generative Value Model for Robot Reinforcement Learning](lv2026viva.md) | 2026 | 正文重点 |
| [From Passive Observer to Active Critic: Reinforcement Learning Elicits Process Reasoning for Robotic Manipulation](liu2026primo.md) | 2026 | 摘要/初步正文 |
| [Large Reward Models: Generalizable Online Robot Reward Generation with Vision-Language Models](wu2026lrm.md) | 2026 | 摘要/初步正文 |
| [DenseReward: Dense Reward Learning via Failure Synthesis for Robotic Manipulation](fang2026densereward.md) | 2026 | 正文重点 |
| [RynnValue: Scaling Robotic Value Foundation Models with Temporal Distance](huang2026rynnvalue.md) | 2026 | 正文重点 |
| [Scaling Vision-Language Reward Learning for Robot Manipulation in Parallel Simulation](joualy2026rapid.md) | 2026 | 正文重点 |
| [Intrinsic Robot Rewarding: Reusing VLA Representations for Autonomous Evaluation and Policy Improvement](schaffer2026irr.md) | 2026 | 摘要/初步正文 |
| [RL-VLM-F: Reinforcement Learning from Vision Language Foundation Model Feedback](wang2024rlvlmf.md) | 2024 | 摘要/初步正文 |
| [ARS: Agentic Reward System for Robot Learning](hu2026ars.md) | 2026 | 正文重点 |
| [Dream2Reward: Transition-Alignment Reward Models from Positive Demonstrations for Robotic Manipulation](zhang2026dream2reward.md) | 2026 | 正文重点 |
| [Robometer: Scaling General-Purpose Robotic Reward Models via Trajectory Comparisons](liang2026robometer.md) | 2026 | 正文重点 |
| [SOLE-R1: Video-Language Reasoning as the Sole Reward for On-Robot Reinforcement Learning](schroeder2026soler1.md) | 2026 | 正文重点 |
| [Recurrent Reasoning with Vision-Language Models for Estimating Long-Horizon Embodied Task Progress](zhang2026r2vlm.md) | 2026 | 正文重点 |
| [ProgressLM: Towards Progress Reasoning in Vision-Language Models](zhang2026progresslm.md) | 2026 | 摘要/初步正文 |
| [TaRL: Learning General and Physical Rewards from Tactile Demonstrations](wu2026tarl.md) | 2026 | 摘要/初步正文 |
| [TrAct: Bridging Robot Control and Visual Prediction with Visual Tracks](cao2026tract.md) | 2026 | 摘要/初步正文 |
| [TimeRewarder: Learning Dense Reward from Passive Videos via Frame-wise Temporal Distance](liu2026timerewarder.md) | 2026 | 正文重点 |
| [A Vision-Language-Action-Critic Model for Robotic Real-World Reinforcement Learning](zhai2026vlac.md) | 2026 | 正文重点 |
| [RoboReward: General-Purpose Vision-Language Reward Models for Robotics](lee2026roboreward.md) | 2026 | 正文重点 |
| [MLREF: Efficient Module Reuse for Reward Design in Reinforcement Learning via Large Language Models](liu2026mlref.md) | 2026 | 正文重点 |
| [Beyond Pixels: Learning Invariant Rewards for Real-World Robotics From a Few Demonstrations](xu2026flora.md) | 2026 | 正文重点 |
| [AURA: Autonomous Upskilling with Retrieval-Augmented Agents](zhu2025aura.md) | 2026 | 摘要/初步正文 |
| [RDA: Reward Design Agent for Reinforcement Learning](lee2026rda.md) | 2026 | 正文重点 |
| [When LLM Reward Design Fails: Diagnostic-Driven Refinement for Sparse Structured RL](wang2026diagnostic.md) | 2026 | 正文重点 |
| [PHIRL: Aligning Learned Rewards with Task Progress for Inverse Reinforcement Learning](yu2026phirl.md) | 2026 | 摘要/初步正文 |
| [SD-KRE: A Method for Structural Decoupling and Knowledge Reuse Evolution of Reinforcement Learning Reward Functions Assisted by Large Language Models](cao2026sdkre.md) | 2026 | 摘要/初步正文 |
| [R*: Efficient Reward Design via Reward Structure Evolution and Parameter Alignment Optimization with Large Language Models](li2025rstar.md) | 2025 | 正文重点 |
| [CARD: A Large Language Model-Driven Reward Design Framework via Dynamic Feedback for Reinforcement Learning](sun2024card.md) | 2025 | 正文重点 |
| [ORSO: Accelerating Reward Design via Online Reward Selection and Policy Optimization](zhang2025orso.md) | 2025 | 正文重点 |
| [LaRes: Evolutionary Reinforcement Learning with LLM-based Adaptive Reward Search](li2025lares.md) | 2025 | 正文重点 |
| [Code as Reward: Empowering Reinforcement Learning with VLMs](venuto2024codeasreward.md) | 2024 | 摘要/初步正文 |
| [SPARS: Structure-informed progress-aware reward shaping for fabric manipulation learning from demonstration](he2026spars.md) | 2026 | 摘要/初步正文 |
| [DyCoT-RE: Chain-of-Thought-enhanced LLM reward engineering with dual-dynamic optimization for reinforcement learning](zhu2026dycotre.md) | 2026 | 摘要/初步正文 |
| [ARM-FM: Automated Reward Machines via Foundation Models for Compositional Reinforcement Learning](castanyer2026armfm.md) | 2026 | 正文重点 |
| [PRM-as-a-Judge: A Dense Evaluation Paradigm for Fine-Grained Robotic Auditing](ji2026prmjudge.md) | 2026 | 正文重点 |
| [PRM-as-a-Judge 1.5: A Toolkit for Robot Process Assessment](liu2026prmjudge15.md) | 2026 | 正文重点 |
| [Same Trajectory, Contradictory Rewards (ROBORMBENCH): Paraphrase Fragility in Vision Language Reward Models](jeung2026robormbench.md) | 2026 | 正文重点 |
| [LIBERO-RECOVER: Beyond Task Success Towards Failure Recovery in Robotic Manipulation Models](liu2026liberorecover.md) | 2026 | 正文重点 |
| [RoboRecover: Benchmarking Robot Policy Recovery under Execution Deviations](li2026roborecover.md) | 2026 | 正文重点 |
| [REBOOT: From Failure to Recovery - A Dataset and Benchmark for Precision Assembly](oforiamopo2026reboot.md) | 2026 | 摘要/初步正文 |
| [Reward Machines for Signal Temporal Logic](bozkurt2026stlrm.md) | 2026 | 摘要/初步正文 |
| [Reinforcement Learning with Symbolic Reward Machines](krug2026srm.md) | 2026 | 摘要/初步正文 |
| [From Reaction to Anticipation: Proactive Failure Recovery through Agentic Task Graph for Robotic Manipulation](xu2026agentchord.md) | 2026 | 正文重点 |
| [Semantic-Geometric Task Representations for Bimanual Manipulation from Human Demonstrations to Robot Action Planning](herbert2026semanticgraph.md) | 2026 | 摘要/初步正文 |
| [Improving the Effectiveness of Potential-Based Reward Shaping in Reinforcement Learning](muller2025effectivepbrs.md) | 2025 | 正文重点 |
| [Action-Dependent Optimality-Preserving Reward Shaping](forbes2025adops.md) | 2025 | 摘要/初步正文 |
| [Quantifying Differences in Reward Functions](gleave2021epic.md) | 2021 | 正文重点 |
| [Dynamics-Aware Comparison of Learned Reward Functions](wulfe2022dard.md) | 2022 | 正文重点 |
| [An Unexpected Robot Policy: Early Evaluations of GPT-6 Astra on RoboDojo and Beyond](zhang2026unexpectedpolicy.md) | 2026 | 摘要/初步正文 |
| [Systematically Exploring the Capabilities of GPT-6 Astra as Embodied Policies](galbot2026astrapolicy.md) | 2026 | 正文重点 |
| [RoboICL: Embodied In-Context Learning with GPT-6 Astra](liu2026roboicl.md) | 2026 | 正文重点 |
| [Fewer Tokens, Better Action: GPT-6 Astra Robot Agents with 14% Higher Success Rate but 65% Fewer Tokens](si2026pyrua.md) | 2026 | 正文重点 |
| [Maximum Entropy Inverse Reinforcement Learning](ziebart2008maxent.md) | 2008 | 摘要/初步正文 |
| [Generative Adversarial Imitation Learning](ho2016gail.md) | 2016 | 摘要/初步正文 |
| [Learning Robust Rewards with Adversarial Inverse Reinforcement Learning](fu2018airl.md) | 2018 | 摘要/初步正文 |
| [Deep Reinforcement Learning from Human Preferences](christiano2017preferences.md) | 2017 | 摘要/初步正文 |
| [Extrapolating Beyond Suboptimal Demonstrations via Inverse Reinforcement Learning from Observations](brown2019trex.md) | 2019 | 摘要/初步正文 |
| [Better-than-Demonstrator Imitation Learning via Automatically-Ranked Demonstrations](brown2020drex.md) | 2020 | 摘要/初步正文 |
| [Hindsight Experience Replay](andrychowicz2017her.md) | 2017 | 摘要/初步正文 |
| [Reward Machines: Exploiting Reward Function Structure in Reinforcement Learning](icarte2022rm.md) | 2022 | 正文重点 |
| [A Composable Specification Language for Reinforcement Learning Tasks](jothimurugan2019spectrl.md) | 2019 | 摘要/初步正文 |
| [Ground-Compose-Reinforce: Grounding Language in Agentic Behaviours using Limited Data](li2025gcr.md) | 2025 | 正文重点 |
| [Automating the Refinement of Reinforcement Learning Specifications](ambadkar2026autospec.md) | 2026 | 正文重点 |
| [REvolve: Reward Evolution with Large Language Models using Human Feedback](hazra2025revolve.md) | 2025 | 摘要/初步正文 |
| [Reward Design with Language Models](kwon2023rewarddesign.md) | 2023 | 摘要/初步正文 |
| [Evolving Rewards to Automate Reinforcement Learning](faust2019autoreward.md) | 2019 | 摘要/初步正文 |
| [Reinforcement Learning with Temporal Logic Rewards](li2017tltl.md) | 2017 | 摘要/初步正文 |
| [DrEureka: Language Model Guided Sim-To-Real Transfer](ma2024dreureka.md) | 2024 | 摘要/初步正文 |
| [Reward Machine Inference for Robotic Manipulation](baert2024rminference.md) | 2024 | 正文重点 |
| [Unsupervised Perceptual Rewards for Imitation Learning](sermanet2017upr.md) | 2017 | 摘要/初步正文 |
| [Time-Contrastive Networks: Self-Supervised Learning from Video](sermanet2018tcn.md) | 2018 | 摘要/初步正文 |
| [Learning Reward Functions for Robotic Manipulation by Observing Humans](alakuijala2023hold.md) | 2023 | 摘要/初步正文 |
| [Rank2Reward: Learning Shaped Reward Functions from Passive Video](yang2024rank2reward.md) | 2024 | 正文重点 |
| [Diffusion Reward: Learning Rewards via Conditional Video Diffusion](huang2024diffusionreward.md) | 2024 | 摘要/初步正文 |
| [DecisionNCE: Embodied Multimodal Representations via Implicit Preference Learning](li2024decisionnce.md) | 2024 | 正文重点 |
| [OpenGVL -- Benchmarking Visual Temporal Progress for Data Curation](budzianowski2025opengvl.md) | 2025 | 摘要/初步正文 |
| [Reward Machines for Vision-Based Robotic Manipulation](camacho2021visionrm.md) | 2021 | 正文重点 |
| [Learning Generalizable Robotic Reward Functions from “In-The-Wild” Human Videos](chen2021dvd.md) | 2021 | 摘要/初步正文 |
| [Robot Fine-Tuning Made Easy: Pre-Training Rewards and Policies for Autonomous Real-World Reinforcement Learning](yang2024robofume.md) | 2024 | 摘要/初步正文 |
| [FuRL: Visual-Language Models as Fuzzy Rewards for Reinforcement Learning](fu2024furl.md) | 2024 | 摘要/初步正文 |
| [VLA-RL: Towards Masterful and General Robotic Manipulation with Scalable Reinforcement Learning](lu2025vlarl.md) | 2025 | 摘要/初步正文 |
| [PIVOT: Iterative Visual Prompting Elicits Actionable Knowledge for VLMs](nasiriany2024pivot.md) | 2024 | 摘要/初步正文 |
| [ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation](huang2025rekep.md) | 2025 | 正文重点 |
| [Do As I Can, Not As I Say: Grounding Language in Robotic Affordances](ichter2023saycan.md) | 2023 | 摘要/初步正文 |
| [Code as Policies: Language Model Programs for Embodied Control](liang2023codeaspolicies.md) | 2023 | 摘要/初步正文 |
| [VoxPoser: Composable 3D Value Maps for Robotic Manipulation with Language Models](huang2023voxposer.md) | 2023 | 摘要/初步正文 |
| [Inner Monologue: Embodied Reasoning through Planning with Language Models](huang2023innermonologue.md) | 2023 | 摘要/初步正文 |
| [RoboDojo: A Unified Sim-and-Real Benchmark for Comprehensive Evaluation of Generalist Robot Manipulation Policies](chen2026robodojo.md) | 2026 | 摘要/初步正文 |

## 补充14篇逐篇入口

| 文献 | 实际阅读范围 |
|---|---|
| [Adaptive querying for reward learning from human feedback](added_anand2026_adaptive_query.md) | 摘要、方法概述与问题设置 |
| [Know Where You’re Uncertain When Planning with Multimodal Foundation Models: A Formal Framework](added_bhatt2025_uncertainty.md) | 选择性正文：定义、方法与关键实验 |
| [Constraint-Aware Zero-Shot Vision-Language Navigation in Continuous Environments](added_chen2025_canav.md) | 选择性正文：方法、实验与表 |
| [Exploration-Guided Reward Shaping for Reinforcement Learning under Sparse Rewards](added_devidze2022_explors.md) | 摘要、引言及方法片段 |
| [Replacing Rewards with Examples: Example-Based Policy Search via Recursive Classification](added_eysenbach2021_rce.md) | 选择性正文：假设、方法、理论与实验 |
| [Dynamical Distance Learning for Semi-Supervised and Unsupervised Skill Discovery](added_hartikainen2020_ddl.md) | 选择性正文：方法、实验及理论条件 |
| [Training Robots to Evaluate Robots: Example-Based Interactive Reward Functions for Policy Learning](added_huang2023_lirf.md) | 正文方法/实验及附录A.1–A.9 |
| [On the Benefit of Optimal Transport for Curriculum Reinforcement Learning](added_klink2024_curriculum_ot.md) | 选择性正文：方法与关键实验 |
| [Language-Model-Assisted Bi-Level Programming for Reward Learning from Internet Videos](added_mahesheka2024_bilevel_video.md) | 完整作者摘要 |
| [JARVIS-1: Open-World Multi-task Agents with Memory-Augmented Multimodal Language Models](added_wang2023_jarvis1.md) | 作者项目页摘要与概要 |
| [Uncertainty-aware Reward Design Process](added_yang2025_urdp.md) | 完整摘要与引言片段 |
| [Reward Evolution with Graph-of-Thoughts: A Bi-Level Language Model Framework for Reinforcement Learning](added_yao2025_regot.md) | 完整作者摘要 |
| [WoMAP: World Models For Embodied Open-Vocabulary Object Localization](added_yin2025_womap.md) | 作者项目页摘要、方法与实验说明 |
| [On Learning Intrinsic Rewards for Policy Gradient Methods](added_zheng2018_lirpg.md) | 选择性正文：核心方法与实验设置 |
