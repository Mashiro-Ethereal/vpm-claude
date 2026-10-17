# huang2025rekep

## 选择性精读：奖励学习必要性的强对照（第二轮）
来源：[arXiv v2](https://arxiv.org/html/2409.01652v2)，实际读§3–5；保存 deep/deep_part2.web.txt。

**方法。** DINOv2+SAM关键点提议，校准RGB-D转世界点，GPT-4o生成阶段目标/路径几何约束，优化末端SE(3)目标和轨迹。初次全局+局部约1秒，后局部约10Hz；20Hz点跟踪。抓取点随末端短时刚体、其余点静止的局部模型。不学习任务奖励，仍有人工通用控制代价和AnyGrasp。

**实验。** 两真机平台7任务×10随机初始试验；Table1自动44.3%、人工约束68.6%、VoxPoser10.0%；扰动3任务Table2自动26.7%。§3.3失败可回溯此前阶段，但骨架仍固定；§5限制遮挡跟踪和复杂接触模型。可见训练外对象策略，不构成任意接触/实时自然扰动全面可靠性。

**关联。** 对可用几何关系、短时模型充分的任务，学奖励/学策略并非必要；新RL研究需证明低层复杂接触、策略频率或训练后低部署成本等收益。用户只有固定/腕RGB相机的现有声明，不可默认具备该方法所需校准深度。

**标题**：ReKep: Spatio-Temporal Reasoning of Relational Keypoint Constraints for Robotic Manipulation

**书目登记**：Wenlong Huang; Chen Wang; Yunzhu Li; Ruohan Zhang; Li Fei-Fei；2025；CoRL 2024; PMLR 270:4573–4602 (2025)。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2409.01652)。版本记录：[Submitted on 3 Sep 2024 (v1 ), last revised 12 Nov 2024 (this version, v2)]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：约束表达需通用、免标注、可实时解算。

**原文方法/输入监督**：RGBD+VLM自动生成3D关键点Python数值constraint，分层优化SE3动作序列。

## 初筛记录：摘要证据

摘要：轮式单臂与双臂，多阶段/inwild/bimanual/reactive，无task-specificdata/model。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：依赖视觉keypoint跟踪与几何solver，接触动力学/遮挡边界需全文。

**阅读者推断/关联**：视觉程序进度/约束代码最强规划近邻；研究必要性需对比。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/huang2025rekep.abs.web.txt`（若首轮批量来源为 `huang2025rekep.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
