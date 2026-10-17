# huang2026rynnvalue — RynnValue: Scaling Robotic Value Foundation Models with Temporal Distance

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2608.09853)；[书目正式版本](https://arxiv.org/pdf/2608.09853)。版本：[Submitted on 10 Aug 2026 ( ), last revised 29 Sep 2026 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/huang2026rynnvalue.web.txt](_sources/huang2026rynnvalue.web.txt)。

- 原文问题：temporal distance规模化value foundation model。
- 原文方法/输入/监督：7000h/3Mclips timestamp labels，shuffle/random sampling/value-isolation attention；PBRS密集reward。
- 原文摘要报告的验证：OOD τa=.704 vs .655/.292；真机online52.5→72.5、offline63.8→82.5%。
- 阅读者判断/待核细节：temporal distance标签与政策可达性不相等；大量数据预算须保持。
- 与基础工作的关系：价值/进度区别及PBRS通用模型已有当前直接对照。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2608.09853v2](https://arxiv.org/html/2608.09853v2)。实际范围：§3.1.2、3.2、3.3–3.4、3.6、5.1–5.2、AppendixE.5。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/huang2026rynnvalue.full.reading.txt](_sources/huang2026rynnvalue.full.reading.txt)。

正文证据与阅读判断：7000h、1.67Moriginalepisodes→3Msegments，subtaskcutoff有nativeannotation/比例trim，timestamptime-to-go、8random/shuffledframe、valueisolatedattention、mismatchaugment。potential=−predictedtime，不等真实robotBellmanV；causal部署。真人success/termination保留，reward−1/0+PBRS；AppendixE.5 terminalnextΦ设0、chunkγc=γs^q，明确规范边界。真实4tasksDSRL60onlineepisodes/task20eval：72.5vsRobometer52.5/sparse48.8%；offline82.5vs63.8。timevalue+history+correctPBRS+realonline已覆盖；policy/recovery不同导致duration标签语义变化仍可检验，不能泛称用timecost新。
