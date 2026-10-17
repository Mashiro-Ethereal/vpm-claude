# liu2026timerewarder — TimeRewarder: Learning Dense Reward from Passive Videos via Frame-wise Temporal Distance

阅读日期：2026-10-06。书目年份/venue：2026；ICML 2026 / PMLR 306:79029–79049（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2509.26627)；[书目正式版本](https://raw.githubusercontent.com/mlresearch/v306/main/assets/liu26et/liu26et.pdf)。版本：[Submitted on 30 Sep 2025 ( ), last revised 20 May 2026 (this version, v3)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/liu2026timerewarder.web.txt](_sources/liu2026timerewarder.web.txt)。

- 原文问题：以被动视频帧间temporal distance提供进度奖励。
- 原文方法/输入/监督：robot demos/human videos，无动作输入；帧对时间距离建模后输出step-wise proxy rewards。
- 原文摘要报告的验证：摘要报告10个MetaWorld难任务，20万步中9/10近乎成功，并优于environment dense。
- 阅读者判断/待核细节：时间距离是否跨失败/恢复有效、额外sparse reward如何用，须正文验证。
- 与基础工作的关系：‘时间距离替代进度’不是新提法，应检验定义与闭环假设。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2509.26627v3](https://arxiv.org/html/2509.26627v3)。实际范围：§4.1–4.3、5.2，未全附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/liu2026timerewarder.full.reading.txt](_sources/liu2026timerewarder.full.reading.txt)。

正文证据与阅读判断：两orderedframes normalizedtimedifference∈[-1,1]、反序implicitnegative、1/Δsampling、20bintwohot；直接adjacentpredictedΔtime+externalsuccess。§5.2 DrQv2 10MetaWorldtasks8seeds，9/10best；20humanvideo+1insimdemo跨域只测simRL不是真机器人。理论§4.3 optimalexpert、deterministicfullyobservablestate，排除视觉cyclealias；作者明述需historycounter扩展。反向/停滞已讨论，timestamp距离不是无条件realcompletioncost。
