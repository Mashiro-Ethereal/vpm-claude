# zhang2026progresscompass — ProgressCompass: Embodied Progress Reward Models Are Lost Without the Right Context

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2609.36684)；[书目正式版本](https://arxiv.org/pdf/2609.36684)。版本：[Submitted on 29 Sep 2026]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/zhang2026progresscompass.web.txt](_sources/zhang2026progresscompass.web.txt)。

- 原文问题：context-dependent progress ambiguity的明确基准与agentic修正。
- 原文方法/输入/监督：24任务120episodes，state recall/sequence tracking/recurrence；同input格式paired context intervention；agentic context loop冻结PRM。
- 原文摘要报告的验证：正确上下文进度误差降77–82%；wrapper降63%、rank agreement升76%。
- 阅读者判断/待核细节：数字属摘要；benchmark模型估分不等于closed-loop RL收益。
- 与基础工作的关系：‘加入历史解决歧义’已覆盖且full-history模型仍错；须找具体尚未支持结论。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2609.36684v1](https://arxiv.org/html/2609.36684v1)。实际范围：§2–5及Appendix B；未精读Appendix A全部证明。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/zhang2026progresscompass.full.reading.txt](_sources/zhang2026progresscompass.full.reading.txt)。

正文证据与阅读判断：24tasks120videos71708frames，state recall/sequence/recurrence；Orienter27B、Verifier/Navigator9B、frozenRobometer4B，verifiedmemory/expectedtransition/计数loop。MAE25.4→9.3、ρ.53→.93；去expectedtransition MAE17.5/18.3；15early-stop/extra/mismatch负例。currentframe理论floor不适用于所有historymodel，优势是有条件不保证。实际视频进度annotation，无闭环RL实验；历史memory/任务分解/验证已直接覆盖。Appendix B orienter只current+文本memory、verifier3frames，至多8次验证。
