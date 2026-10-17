# PRM-as-a-Judge: A Dense Evaluation Paradigm for Fine-Grained Robotic Auditing

引用键：ji2026prmjudge。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2603.21669v1)。
- 版本、发表状态与实际范围：arXiv v1 preprint；实际读§3.1公式/OPD、§4benchmark、§5.1及Table2、附录D Remark与审计片段。书目所列年份：2026；venue：arXiv（除明确写已核验者，书目状态不视为独立确认）。
- WHY：二元成功遮蔽进度效率稳定。。
- HOW：固定Φ统一相对增量并给OPD completion/PPL/CRA/STR过程指标。
- WHAT：RoboPulse1800pairs/816tasks；RoboDopaminepairaccuracy.83，对VLAC/GVL.71；RoboTwin5policies×7tasks×50rollout审计。
- 假设、监督与输入：taskconditionedprogressjudge，可选start/endanchors；nativeinputformats不严格同输入。
- 验证依据：benchmark筛单调清晰区间、排掉negligible/ambiguous oscillation，无neutral；OPDpolicydata同训练budget。
- 边界：任意scalar自然诱导additiveincrements，附录D作者明确不等于物理正确；微进度分辨需验证。
- 关联（阅读者推断）：进度评价与过程非单调问题均已有；不能把路径可加性等同新的行为有效性保证。
