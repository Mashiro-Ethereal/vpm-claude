# li2024decisionnce — DecisionNCE: Embodied Multimodal Representations via Implicit Preference Learning

阅读日期：2026-10-06。书目年份/venue：2024；ICML 2024（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2402.18137)；[书目正式版本](https://raw.githubusercontent.com/mlresearch/v235/main/assets/li24cr/li24cr.pdf)。版本：[Submitted on 28 Feb 2024 ( ), last revised 24 May 2024 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/li2024decisionnce.web.txt](_sources/li2024decisionnce.web.txt)。

- 原文问题：统一local/global progress、temporal consistency与language grounding。
- 原文方法/输入/监督：视觉轨迹与对应语言的implicit preference，Bradley-Terry重参数化得到embodied InfoNCE目标。
- 原文摘要报告的验证：仿真和真机多类policy learning。
- 阅读者判断/待核细节：implicit preference无需人标不等于所有失败有可靠标签；细节需正文。
- 与基础工作的关系：reward形式与表征目标共同设计已覆盖简单joint representation方向。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2402.18137v2](https://arxiv.org/html/2402.18137v2)。实际范围：§3.1–3.4、5.2–5.3；未完整证明/附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/li2024decisionnce.full.reading.txt](_sources/li2024decisionnce.full.reading.txt)。

正文证据与阅读判断：instructionmatchedsegment preferredovermismatched，randomspan，DecisionNCEP距离shift、T latenttransitiondirection对languagecosinealign。P差分不是pureγPBRS而是rawsimilarity+shaping。Table3 FrankaKitchenMPPIzero-shot平均successP.101/T.122vsLIV.054，非realrobotonline；representationLCBC另评。transitiondirection已有2024直接近邻，不能把signedvectorvsstaticstate当空白。
