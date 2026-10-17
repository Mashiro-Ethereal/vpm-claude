# LIBERO-RECOVER: Beyond Task Success Towards Failure Recovery in Robotic Manipulation Models

引用键：liu2026liberorecover。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2609.05178v3)。
- 版本、发表状态与实际范围：arXiv v3 preprint；实际读§2.1–2.5构造/§3数据、§4主要实验与§4.2.3干预。书目所列年份：2026；venue：arXiv（除明确写已核验者，书目状态不视为独立确认）。
- WHY：近完美标准LIBERO成功隐藏恢复弱。。
- HOW：真实policy失败取状态并保证存在恢复，L1retry/L2adapt/L3restoreobject/L4restoreenvironment；专门recovery训练和评测。
- WHAT：2178scenarios130subtasks；复杂restore差，正常LIBERO高分不能代替恢复；initialframe可改善恢复。
- 假设、监督与输入：6sourceVLArollouts/Qwen定位+simstate，4teleop3184recoverytraces413failurestates，exclude trainfailurestates。
- 验证依据：OpenVLA-OFT恢复20.8→26.8加历史；混合data恢复20.8→25.4但正常97.1→96.6（不同干预）。
- 边界：localization自动标注抽查不等完整oracle；自然自失误转移收益有限；分层恢复定义已包含关系/依赖/历史。
- 关联（阅读者推断）：状态恢复/历史语义是真问题但不是新问题；评估需自然policy失败而非仅被动扰动。
