# zhang2025rewind — ReWiND: Language-Guided Rewards Teach Robot Policies without New Demonstrations

阅读日期：2026-10-06。书目年份/venue：2025；CoRL 2025 / PMLR 305（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2505.10911)；[书目正式版本](https://raw.githubusercontent.com/mlresearch/v305/main/assets/zhang25a/zhang25a.pdf)。版本：[Submitted on 16 May 2025 ( ), last revised 19 Sep 2025 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/zhang2025rewind.web.txt](_sources/zhang2025rewind.web.txt)。

- 原文问题：新任务无需新示范的语言reward和policy迁移。
- 原文方法/输入/监督：小demo集训练language reward与offline RL policy；新任务变体用该reward在线finetune。
- 原文摘要报告的验证：摘要报告reward generalization/对齐最高2.4倍，仿真适应2倍、真机bimanual pretrained policy5倍。
- 阅读者判断/待核细节：无新示范指每个新任务；已有初始demo与policy预训练仍是预算。
- 与基础工作的关系：把结构reward用于新任务迁移须对照既有reward+policy协同训练。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2505.10911v2](https://arxiv.org/html/2505.10911v2)。实际范围：§3–5、Tables1–3及真实预算；未全部附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/zhang2025rewind.full.reading.txt](_sources/zhang2025rewind.full.reading.txt)。

正文证据与阅读判断：356kOXE+target15–20task约5demos，DINOv2/MiniLM frozen+causalsequentialtransformer，timeprogress、mismatchzero、videorewind下降、firstframePE；offlineIQL/onlinesuccessbonus。Table1 rolloutrankingρ.82 vsLIVFT.47；Table2加fullPE improvedsuccessfuldemoρ.85vs.79但Table3policy相对.69，单successfuldemoordering不足。MetaWorld8unseen100k3seedIQM79%；真实Koch5tasks1h50kbase12→68%，human成功/targetenvdemos仍需要。Fig7抓空停滞再试reward上升已覆盖恢复；rewind可能非物理作者承认。
