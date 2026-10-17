# From Reaction to Anticipation: Proactive Failure Recovery through Agentic Task Graph for Robotic Manipulation

引用键：xu2026agentchord。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2605.11951v1)。
- 版本、发表状态与实际范围：arXiv v1/正式RSS2026 proceedings p180已核；实际读§III/IV-A–E/V，附录C-A/C-C–E feature与solver。书目所列年份：2026；venue：Robotics: Science and Systems 2026（除明确写已核验者，书目状态不视为独立确认）。
- WHY：反应式恢复反复推理延迟高。。
- HOW：LLM nominal图+提前failure/recovery枝，编译constraintsolvers/持续监控；Eq8图terminalcost筛forwardrecovery。
- WHAT：6real任务20trial/任务，平均77.5% vs CaM72.5%；单仿真task恢复数据定量改策略。
- 假设、监督与输入：RGBD+SAM3/AnyGrasp、手工featuretools/IK；simulationprivilegedposes；现成atomiccontroller，不是RL奖励学习。
- 验证依据：IV-E总40traces固定，用20recovery替换20success，26/50→39/50；real与sim扰动设置有别。
- 边界：图distance不是经验conditionalreachability；IV-D错恢复节点/IK不可行/monitor选择失误是真失败；solver已有reachabilitypenalty。
- 关联（阅读者推断）：图+视觉+修订+恢复策略数据不能拼装当新；有意义差异需在预算控制下改善实际回退可执行性。
