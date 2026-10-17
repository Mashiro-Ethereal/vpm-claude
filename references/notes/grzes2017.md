# Reward Shaping in Episodic Reinforcement Learning

引用键：grzes2017。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://www.ifaamas.org/Proceedings/aamas2017/pdfs/p565.pdf)。
- 版本、发表状态与实际范围：正式AAMAS2017；实际读摘要、§4.1 Eq3与终端反例/修正、§4.2–4.3 UCT与R-max边界讨论；未逐项复核全部证明。书目所列年份：2017；venue：AAMAS 2017（除明确写已核验者，书目状态不视为独立确认）。
- WHY：episodic塑形的统一分析。。
- HOW：有限回报残留γ^NΦ(s_N)，在每次轨迹终止处令势为零去掉策略依赖。
- WHAT：episodic/截断与模型未知状态的边界会影响最优性论证。
- 假设、监督与输入：实际终止和非终止状态须区分，同一环境状态不必处处设零。
- 验证依据：读Eq3和终端讨论，非实证型效果保证。
- 边界：将最后一步shaping reward直接置零并不等价于正确终端势修正。
- 关联（阅读者推断）：训练timeout、真正成功/失败terminal和bootstrap边界需保持一致；这属于实现正确性，非视觉独有难题。
