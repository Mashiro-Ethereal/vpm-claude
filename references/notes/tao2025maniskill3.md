# tao2025maniskill3

**标题**：Demonstrating GPU Parallelized Robot Simulation and Rendering for Generalizable Embodied AI with ManiSkill3

**书目登记**：Stone Tao; Fanbo Xiang; Arth Shukla; Yuzhe Qin; Xander Hinrichsen; Xiaodi Yuan; Chen Bao; Xinsong Lin; Yulin Liu; Tse-Kai Chan; Yuan Gao; Xuanlin Li; Tongzhou Mu; Nan Xiao; Arnav Gurha; Viswesh Nagaswamy Rajesh; Yong Woo Choi; Yen-Ru Chen; Zhiao Huang; Roberto Calandra; Rui Chen; Shan Luo; Hao Su；2025；Robotics: Science and Systems XXI。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2410.00425)。版本记录：[Submitted on 1 Oct 2024 (v1 ), last revised 30 May 2025 (this version, v2)]。

阅读日期：2026-10-06。范围：**原始摘要初筛**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：现有模拟场景窄且视觉渲染不适合规模化。

**原文方法/输入监督**：state+visual GPU并行物理/渲染、heterogeneous场景、pointcloud/voxel与示范。

## 已读证据

arXiv v2摘要：10–1000倍速、2–3倍低显存、最高30000+FPS、12domain。

## 边界与基础关联

**边界**：这些是特定benchmark平台结果；与硬件/任务/图像分辨率关联。

**阅读者推断/关联**：8A100适合可控视觉实验，但平台速度不是奖励算法贡献。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/tao2025maniskill3.abs.web.txt`（若首轮批量来源为 `tao2025maniskill3.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

