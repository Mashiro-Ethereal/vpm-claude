# The Perils of Optimizing Learned Reward Functions: Low Training Error Does Not Guarantee Low Regret

引用键：fluri2025perils。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2406.15753)。
- 版本、发表状态与实际范围：正式ICML2025出版页已核；实际读摘要/引言、§2–5关键命题/定理、§6概述、附录C2 PropositionC5构造；未逐证所有附录。书目所列年份：2025；venue：ICML 2025 / PMLR 267（除明确写已核验者，书目状态不视为独立确认）。
- WHY：低测试误差仍可能大regret。。
- HOW：有限MDP数据分布下rewarderror与优化后regret，覆盖/坏策略占用支持决定error-regret mismatch。
- WHAT：固定正覆盖分布，ε足够小有positive保证；ε门槛依赖minD。弱覆盖坏policy可低误差高regret；KL正则同样非普遍补救。
- 假设、监督与输入：worstcase模型/最优策略，有限MDP/各policyoccupancy；轨迹比较与rewardscore损失扩展。
- 验证依据：实际读§3.1/3.2、§4.1/4.2和C2构造；理论论文非机器人常见失效发生率估计。
- 边界：不能写成所有低误差reward必失败；不是固定PBRS势错误改变任务最优性的反例。
- 关联（阅读者推断）：RF-Agent应关心被搜索选择/被RL优化后的truebehavior，不能只看静态fit；具体新方法需超过EPIC/DARD与ROBORM。
