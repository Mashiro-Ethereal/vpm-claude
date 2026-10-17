# yang2024rank2reward — Rank2Reward: Learning Shaped Reward Functions from Passive Video

阅读日期：2026-10-06。书目年份/venue：2024；ICRA 2024（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2404.14735)；[书目正式版本](https://rank2reward.github.io/static/pdf/ICRA_2024_Reward_learning_from_video.pdf)。版本：[Submitted on 23 Apr 2024]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/yang2024rank2reward.web.txt](_sources/yang2024rank2reward.web.txt)。

- 原文问题：raw passive video时间排序得到shaped reward，防reward exploit。
- 原文方法/输入/监督：无low-level state/actions；temporal rank表示incremental progress，与adversarial imitation结合。
- 原文摘要报告的验证：sim/real桌面arm操作；扩到web视频。
- 阅读者判断/待核细节：已有在线adversarial约束，不能笼统说旧视觉reward不处理rollout偏移。
- 与基础工作的关系：进度转reward+online修正是直接基础近邻。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2404.14735v1](https://arxiv.org/html/2404.14735v1)。实际范围：§IV–VI及TableI。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/yang2024rank2reward.full.reading.txt](_sources/yang2024rank2reward.full.reading.txt)。

正文证据与阅读判断：时间偏好BradleyTerry ranking+online expert-vspolicy classifier估densityratio，reward logpRF+αlogitD，非PBRS。MetaWorld8tasksDrQv21.5M3seed，ROT在push/dooropen更好；real6tasksdrawer6079/obstaclepush4391steps/sweep0%incompletion，GAIL复杂taskfail。Ego4D20kclips仅curve分析非human→robotRL。已覆盖OOD进度高估、在线分布惩罚；closeexpert可能罚替代成功策略，single-task/background/adversarialstability作者limits。
