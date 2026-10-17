# mao2026arm — ARM: Advantage Reward Modeling for Long-Horizon Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；CVPR 2026 Workshops / GigaBrainChallenge（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2604.03037)；[书目正式版本](https://arxiv.org/pdf/2604.03037)。版本：[Submitted on 3 Apr 2026 ( ), last revised 21 Apr 2026 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/mao2026arm.web.txt](_sources/mao2026arm.web.txt)。

- 原文问题：相对advantage替代绝对progress，含回退/恢复。
- 原文方法/输入/监督：人工tri-state Progressive/Regressive/Stagnant，支持完整demo与DAgger片段；offline RL重权筛次优。
- 原文摘要报告的验证：长时程towel folding99.4%，human标注一致性。
- 阅读者判断/待核细节：所称advantage是否为Q−V须正文；tri-state人工标签不是Bellman估计。
- 与基础工作的关系：不能以‘考虑回退的相对进度’泛称新颖；须区分符号变化与策略优势。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2604.03037v2](https://arxiv.org/html/2604.03037v2)。实际范围：§3.2–4.5/主消融，未完整附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/mao2026arm.full.reading.txt](_sources/mao2026arm.full.reading.txt)。

正文证据与阅读判断：CLIPvisual/proprio/language causalMIMO，+/0/−localprogress人工初标再pseudo，completionanchor累计重建、AWBC lengthadaptivegainnormalizedweights。所谓advantage的监督是progressgain类别，不是Qπ−Vπ。§4.5 realGR00Tpolicy baseline62.1/SARMRA-BC78.5/ARMAWBC99.4，Table5ARM+RABC92.3；本次尚未核实总evaluation次数，数字只原文报告不推不确定性。已覆盖方向/停滞、terminalanchors、加权BC；真正counterfactualactionadvantage需定义差异。
