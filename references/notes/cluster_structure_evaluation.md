# 任务结构、视觉接口、恢复与奖励评价：49篇文献综合

阅读日期：2026-10-06。此文件提供原始文献证据与可检验问题，不决定最终TPAMI方向。研究起点为用户PRM4RL与RF-Agent；资源约束为8×A100 80GB及真实机械臂，期限未定。使用ARS的两轮文献筛选/主题综合方法，先读再归纳；不以标题或评分表决定方向。

## 阅读覆盖与来源状态

49/49篇已尝试取得原始来源并实际读取完整摘要或正文。49份独立笔记均在本目录以citation_key命名。本子智能体21篇选择性精读，主智能体再补读Müller正文方法/设置，因此团队累计22篇，其余27篇仅作为初筛证据；“取得全文”不等于“读完全文”。精读清单为Ng1999、Grzes2017、Müller2025、RM2018/2019/2022、VisionRM2021、NoisyRM、GORDON、Baert、ARM-FM、GCR、AutoSpec、AgentChord、EPIC、DARD、Fluri、PRM-as-Judge1.0/1.5、ROBORMBENCH、LIBERO-Recover、RoboRecover。精读范围逐篇记录，主要为方法/理论、实验与必要附录，不声称逐字读所有长附录。

完全未获取：0。Sutton出版社/数个作者存档直连失败，最终从Barto课程的原论文PDF取得并读摘要。ARM-FM OpenReview访问有验证码，但arXiv v3全文取得；其ICLR2026状态为作者arXiv comments确认。AutoSpec与AgentChord分别在[ICLR正式出版页](https://proceedings.iclr.cc/paper_files/paper/2026/hash/396ea38391e8b96a3add6126006f1a53-Abstract-Conference.html)和[RSS正式出版页](https://www.roboticsproceedings.org/rss22/p180.html)独立确认。DARD PDF明确Published as a conference paper at ICLR2022，原书目仅arXiv。GCR arXiv v2注明NeurIPS2025。VisionRM书目arXiv链接是五作者早版“Disentangled Planning and Control…”；精读改用六作者正式ICRA2021作者PDF“Reward Machines for Vision-Based Robotic Manipulation”。原书目未修改。

当前新增2026论文均按实际arXiv版本阅读；未把预印本默认视为录用，也未把论文中的release计划视为资源已下载/可运行。未新增独立论文笔记：重要近邻已在49篇中，父智能体另行查DDL/RCE等。局部网页提取保存在_sources/structure_*_web.txt；不是完整原文镜像。未用本地PDF页码，因此没有执行本地pdf_read_preflight；定位采用节/公式/表。

## 从内容得到的主题

### 1. 固定势的策略不变性与有限预算学习效果是两件事

Ng、Wiewiora、Devlin、Grzes、HPRS、Adaptive Shaping、Müller、ADOPS讨论势差、初始化、动态更新、episodic边界、任务部分序和动作依赖势。核心结论不是“更聪明的进度分数总有更好策略”，而是固定势差满足条件时不改变原奖励的策略排序，实际学习速度仍由表示、探索、优化和初始化决定。[Ng定理与证明](https://people.eecs.berkeley.edu/~russell/papers/icml99-shaping.pdf)，[Grzes Eq3/§4.1](https://www.ifaamas.org/Proceedings/aamas2017/pdfs/p565.pdf)

在轨迹或历史扩展空间令F_t=γΦ(h_{t+1})−Φ(h_t)，则折扣总和为−Φ(h_0)+γ^TΦ(h_T)。固定任意有界视觉/历史势，即使数值不符合人的“真实进度”，在无限折扣/正确终止边界仍相消。感知误差不是破坏PBRS最优性的充分理由。需要分开检查：原任务奖励本身被学错；每步用不同参数且相邻势未一致配对；成功/失败/timeout的终端势；势差之外的额外bonus/门控/惩罚；有限预算RL表现。动态势也不是一概不允许，Devlin给的是具有相应形式与条件的动态扩展，不能等同任意参数漂移。

重要实际差异：GCR正文算法使用γ势差，但附录B2明确实验证实λ(v′−v)更好，省略下一势的折扣，并承认损失理论性质。ARM-FM附录A5把无正循环与终奖支配非终奖当作策略保持理由；这不足以推出一般折扣稀疏目标的最优性，更不能推出PBRS形式。例如γ=.9，直接成功奖1，另一无环路径先奖.2下一步成功奖1；shaped分别1和1.1，原sparse分别1和.9，终奖1仍大于非终奖.2。这是阅读者对原命题的反例，不是视觉感知的反例。[GCR B2](https://arxiv.org/html/2507.10741v2)，[ARM-FM A5](https://arxiv.org/html/2510.14176v3)

### 2. “同一当前观测，任务历史不同”已是RM体系的核心问题

Sutton/options和MAXQ区分动作时间抽象与任务奖励结构。RM2018显式编码序列、分支和不必要顺序的解除；RM2019通过历史压缩寻找perfect RM，令(o,u)具有后继分布充分性，并从新经验改图。RM2022统一反事实经验、层级控制和自动势。SpectRL/TLTL把形式规范变成学习目标，2026 STL-RM又加入timing/clocks，SymbolicRM尝试直接observations中的guards。因此“加入历史记忆/自动机/任务图”没有新颖性空间。[RM2019 §4/§7](https://proceedings.neurips.cc/paper/2019/file/532435c44bec236b471a47a88d63513d-Paper.pdf)

NoisyRM进一步证明简单独立belief更新无法处理反复出现的相关不确定事件：重复观察同一事实可把进度belief虚增；直接history→RMstate posterior的TDM在一般POMDP具有所述一致性。其实验仍依赖大量groundtruth标签/部分在线oracle数据，故留出的实质差异可能在弱监督视觉动作历史及组合泛化，而非第一次发现历史重要。[NoisyRM §5–6](https://arxiv.org/html/2406.00120v4)

### 3. 当前关系图、视觉演示自动RM、语言生成结构都有非常近的实证

NTG从演示构造可复用神经任务图。VisionRM2021把演示映成planning graph并配势/视觉DQRM；示例图可回退、多路径，feature detectors预给。Baert用视觉ResNet/DBSCAN驻留原型自动提event和RM，在全可观测桌面、少量覆盖可行顺序的algorithmicexpert演示验证。ARM-FM从语言生成RM、Python labeling和每状态语言嵌入，已有人工纠正掉钥匙回退边、MetaWorld逆向进度边及新组合zero-shot。Semantic-Geometric Task Graph以时序物体关系图/MPNN/Transformer和动作表示处理bimanual。[VisionRM §IV–VI](https://www.cs.toronto.edu/~acamacho/papers/cam-var-zen-jai-isc-kal-icra21.pdf)，[Baert §3–5](https://arxiv.org/html/2412.10096v1)，[ARM-FM A4/A10.1](https://arxiv.org/html/2510.14176v3)

GORDON已经是“物体图+视觉奖励+自动阶段+RL”：bbox/语义图编码、活动加权与robot masking、TCC+重建、final latent distance与goal bonus，再用reward梯度切阶段训练分策略。ManiSkill中用模拟器标注boxes/classes/robot identity，长任务每task25条演示；比较有同体系oracle，也有取已发表结果的RoboHorizon，不能都视为相同训练控制。其奖励不是PBRS。[GORDON §III–IV](https://arxiv.org/html/2608.03753v1)

GCR尤其反驳“将剩余可达性换成势”这一宽泛候选：literal reachability PVFs经max/min逻辑组合、RM后继bootstrap近似V*(s,u)，由有限标注轨迹学习后支持从未示范的任务组合。DrawerWorld用78维物体/夹爪位置，预训练刻意含掉落/抓取失败；GeoGrid才是结构化图像。它已能同时使用当前可撤销谓词和任务历史RM state。[GCR §6/§7与B1/B2](https://arxiv.org/html/2507.10741v2)

### 4. 修规范、补恢复枝与改奖励代码的语义并不相同

AutoSpec由失败edge的成功/失败轨迹做reach/avoid refinement、加waypoint、前驱集合拆分和替代路径。其soundness是refined⇒original，不是规范等价，不保证全部原最优行为；需要有限witness且可能找不到refinement。AgentChord在执行前预编译failure monitors/recovery branches，持续视觉几何监控与IK/约束solver执行。Eq8“forward moving”依据图到terminal的cost，不是数据估计的条件恢复成功率；但其solver已有IK/reachability penalty，不能宣称从未考虑物理可行性。[AutoSpec §3/§4/A4](https://arxiv.org/html/2512.01047v2)，[AgentChord §III/C-E](https://arxiv.org/html/2605.11951v1)

AgentChord直接报告错误恢复节点、IK不可行、grasp monitor选择失误；这提供可测失败事实。它也已生成恢复数据改善学习：总40条训练数据固定，半数成功轨迹换为恢复轨迹，单仿真任务26/50→39/50。因此“图+视觉+修订+恢复示范”组合不够构成论文贡献。[AgentChord IV-D/E](https://arxiv.org/html/2605.11951v1)

### 5. 失败之后的任务状态恢复是真难题，但定义和基础干预已经被测过

Sentinel以动作一致性/视觉进度检测失败，不直接解决恢复。RoboProcessBench测试phase/contact/localprogress/temporalorder等12类过程QA；OpenGVL关注开源进度评估和数据清理。LIBERO-Recover已区分L1重试、L2动作/姿态调整、L3物体状态恢复、L4环境阻碍恢复。RoboRecover已区分WrongTarget/Pose/StageRollback/SceneChange，并以真实交互前缀/replay、参考政策恢复率筛选场景；还训练monitor+corrector。REBOOT则提供precisionassembly各phase的专家恢复数据与几何容差标注。[LIBERO-Recover §2/4](https://arxiv.org/html/2609.05178v3)，[RoboRecover §4–5](https://arxiv.org/html/2609.28952v1)，[REBOOT摘要](https://arxiv.org/html/2609.22591v1)

较强证据是LIBERO-Recover的转移落差：恢复训练改善评测失败态，却几乎不改善正常LIBERO自发失败；初始帧历史提高OpenVLA-OFT恢复率20.8→26.8，而混合恢复训练为20.8→25.4、正常97.1→96.6（两种不同干预）。这支持评价自然policy失败/记忆价值，不支持“首次同观测历史不同”。RoboRecover的best-per-state恢复oracle是回看上界；Reversion回退30步改变评测初态，不能与same-state方法直接合并排名。[LIBERO-Recover §4.2.3](https://arxiv.org/html/2609.05178v3)，[RoboRecover §5.5](https://arxiv.org/html/2609.28952v1)

### 6. 离线奖励误差与被优化后的行为存在差距，也有成熟前驱

MaxEntIRL/GAIL/AIRL、偏好学习、T-REX/D-REX、HER代表不同监督/目标回溯，不宜把示范顺序/偏好/进度/可达性标签混为同一种信息。Pan、Amodei、Gao分别讨论proxy能力放大、具体reward问题类别与LM overoptimization；这些不能直接当机器人闭环定量规律。Fluri给精确理论：有限MDP固定正覆盖分布在足够小误差下有保证，门槛依赖minD；弱覆盖坏政策支持可低误差高regret，正则不提供无条件修复。它不是“所有低误差都无用”。[Fluri §3–5/C2](https://arxiv.org/html/2406.15753)

EPIC已用势差不变距离预测policyregret并给coverage条件界；DARD又用transitionmodel减轻不物理样本评价，代价是模型误差/小步smoothreward的敏感性。ROBORMBENCH不只测paraphrase静态一致性，也用N20同离线candidatepool选policy、发现SCR与selection regret相关。因此“从静态指标迈向行为决策”也有近邻；仍可测的是对真正RL优化/搜索后新行为的排序预测和预算收益。[EPIC §4/6.3](https://arxiv.org/html/2006.13900v3)，[DARD §4–5](https://arxiv.org/pdf/2201.10081)，[ROBORMBENCH §4.5](https://arxiv.org/html/2609.05401v1)

PRM-as-Judge1.0给OPD过程指标，1.5已加入DRR恢复/failed-near-success/SQS。任意scalar的相对差自然可加，作者附录D也明确这不保证物理真值；1.0选择较清晰单调pairs，1.5以Rising/Falling interval避免跨任务绝对百分比无一致groundtruth。其后验曲线回升不等于当前可恢复概率，但不能把恢复评价本身当首次。[PRM1.0 §3/D](https://arxiv.org/html/2603.21669v1)，[PRM1.5 §2/C](https://arxiv.org/html/2608.14284v1)

## 会直接反驳候选新颖性的近邻

| 宽泛主张 | 已有直接证据 | 真正需要验证的区别 |
|---|---|---|
| 非单调/不同历史的任务进度 | RM2018/2019、NoisyRM、ARM-FM lostkey反向边 | 学习监督、低权限视觉、未见组合上的效率，而非RM表达能力 |
| 视觉演示自动推任务图/奖励 | VisionRM、Baert、NTG、GORDON | 可见事件不足时的history充分性、标签成本与闭环性能 |
| 剩余任务可达价值作为势 | RM2022高层value、GCR物理PVF组合 | 既有value方法失效的具体条件及同预算优势 |
| 失败反馈修图/增加恢复 | AutoSpec、AgentChord、RM2019在线更新 | 改的是约束、任务含义、物理state还是学习器；收益不能来自放宽任务 |
| 恢复数据训练更鲁棒策略 | AgentChord IV-E、RoboRecover、LIBERO-Recover、REBOOT数据 | 自发失败的转移/闭环处理时机，控制回退初态与data预算 |
| 奖励指标预测选择后行为 | EPIC、DARD、ROBORMBENCH | RL优化后新occupancy/搜索选择偏差下的rank与算力节省 |
| 进度曲线识别恢复 | PRM-as-Judge1.5 | 干预可用性/条件恢复预测，不仅后验诊断 |

## 可检验开放问题（不是已确立的新颖性）

**义务表示是否能在弱监督视觉动作历史下学得更省数据？** 当前可撤销关系（物体又掉落）与已发生历史事件（曾检查/按规定顺序操作）语义不同，任务定义有实质意义。显式RM与GCR已经能表达这两者，因此贡献只能来自学习/泛化能力。可比较相同标签与轨迹预算的显式RM+视觉谓词+TDM、Baert式视觉RM、GCR、historyVLM；holdout重复阶段/分支组合，并控制物理场景/动作技能。既要量义务判断，也要量true任务成功/学习样本量。若手工RM或直接historyVLM同预算已足够，不能凭结构解释性判成功。

**偏离后的条件可执行性是否比图distance更有用？** AgentChord有实际错恢复节点/IK不可行，LIBERO/RoboRecover有状态恢复场景，因此存在可测案例。但GCR与更广的value/success-prediction文献已覆盖future value；不是新目标。可以固定controller、失败state/history、预算，比较图cost、IK几何、PVF/任务value与学习的恢复选择；区别“逻辑剩余义务”与“这个policy此时能做到”的条件能力。可检验是否提高自发失败恢复，并且不削弱原任务或借回退初态获益。现有证据不足以确认这一组合超越现有recovery/value方法。

**便宜的行为评价能否可靠筛掉RF-Agent候选中的优化后错误？** 不以offline误差或单次judge一致性替代最终真实任务。需要超过EPIC/DARD/SCR及短RLprobe在候选排序、错选率、总GPUbudget上的结果；候选搜索和finalseed/task分离。即使offline指标已有best-of-N证据，真正RL改变occupancy后仍可能错排。该问题与RF-Agent延续自然，但还需用户两文方法细节及其它代理近邻共同判断。

**结构/势怎样改善有限预算，而不是重复策略保持证明？** Müller已经直接分析initialQ/external reward/scale-shift对学习的影响，“目标等价但有限训练不同”本身不是新发现。需要跨视觉reward family/task/learner可预测性和省预算选择，并以简单scale/offset/critic初始化作为强控制。固定势比较应保持base sparse真奖励和正确terminal处理；在线更新应说明配对一致性，额外bonus另作目标。价值校准、RM-only势与物理PVF已是强基线。若改善仅来自更多标签、privilegedstate、不同controller或取消折扣，不能归因于新结构。[Müller §3–5（主智能体补读）](https://arxiv.org/html/2502.01307)

## 与两篇既有工作的连接

PRM4RL现有优势是任务语义→分阶段可执行progress→势差辅助RL；延展须明确其原状态接口如何换成视觉/历史后获得可测试的新能力。RF-Agent已有预算化奖励代码搜索/独立behavioral feedback；延展可研究候选结构或评价信息是否改变搜索结果，而不是简单把任务图接到树搜索。以上是阅读者推断，不是用户已决定路线。资源可支持多seed/同预算仿真比较及选择性真机检验；算力规模本身不替代任务辨析。

## 限制与未解决事项

27篇停留在摘要/引言级，只用于主题初筛，不能援引为方法细节审计；各笔记明确范围。团队22篇为选择性精读，并非全部附录逐证。未下载训练数据、复现代码或运行闭环实验，因而不能证明新方法收益，也不能以本文声称失败普遍发生率。2026新预印本结论视为作者当前证据，真实资源可用性需实施时确认。表中的潜在区别均为工作假设，目前不足以证明全领域无人覆盖，更不能由“图+视觉+修订”拼装直接推导TPAMI新颖性。
