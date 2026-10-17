# On the Benefit of Optimal Transport for Curriculum Reinforcement Learning

- 作者：Pascal Klink, Carlo D’Eramo, Jan Peters, Joni Pajarinen。
- 发表：TPAMI 46(11), 7191–7204, 2024；DOI 10.1109/TPAMI.2024.3390051。
- 来源：[作者机构书目](https://www.dfki.de/web/forschung/projekte-publikationen/publikation/16381)、[作者接受稿](https://www.ias.informatik.tu-darmstadt.de/uploads/Team/PascalKlink/benefit-ot-crl-pami-with-ap.pdf)、[代码](https://github.com/psclklnk/optimal-transport-curricula)。读取日2026-10-06；DOI入口本次返回内部错误，作者接受稿与机构记录可取得。
- 阅读范围：摘要、§3–5问题与方法、§6实验设置及6.3–6.5、Fig.12–15相关讨论；未完整读附录证明与参数表。用途为TPAMI方法研究实例及对“只改奖励”解释的挑战。

**WHY/HOW/WHAT（原文）。** 稀疏RL的训练难度可通过任务分布课程改变。本文把课程构造成任务分布间受约束的最优传输，分析KL插值和平均性能约束的缺陷，提出CURROT并与GRADIENT及多种课程基线比较。实验涉及离散/连续任务空间、不同距离与可达性，说明任务几何和能力约束影响学习效率。

**假设与验证。** 需要可采样的任务上下文、目标任务分布、距离和任务回报；通过不同环境、精确/近似解及多种基线考察机制。并非视觉奖励识别或真实机械臂奖励学习论文。

**阅读者推断。** 这是TPAMI可接纳一般RL方法贡献的直接实例，不能断言该刊只接纳视觉方法。对候选方向的启示是：若进度奖励收益实际源自训练状态/任务分布改变，应加入同预算课程对照，避免把探索覆盖收益都归因于奖励表示。
