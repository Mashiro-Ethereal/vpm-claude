# fang2026densereward — DenseReward: Dense Reward Learning via Failure Synthesis for Robotic Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2607.13033)；[书目正式版本](https://arxiv.org/pdf/2607.13033)。版本：[Submitted on 14 Jul 2026]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/fang2026densereward.web.txt](_sources/fang2026densereward.web.txt)。

- 原文问题：真实物理失败和恢复数据合成dense reward。
- 原文方法/输入/监督：simulation自动生成碰撞/抓空/掉落/恢复，visual+language frame分数，无人工failure labeling。
- 原文摘要报告的验证：sim/real reward prediction，downstream MPC及RL。
- 阅读者判断/待核细节：模拟任务生成可能利用特权状态；跨real数据和closed-loop细节需全文。
- 与基础工作的关系：‘成功示范之外补失败’已经覆盖，监督预算才可能形成实质差别。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2607.13033v1](https://arxiv.org/html/2607.13033v1)。实际范围：§3–5、Appendix A/B/C。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/fang2026densereward.full.reading.txt](_sources/fang2026densereward.full.reading.txt)。

正文证据与阅读判断：五阶段reach/grasp/lift/move/place、RGBD/GraspNet/CuRobo+仿真state边界；碰撞/抓空/掉落/噪声/恢复（collision后replan）的预设奖励curve。Qwen3VL4B current+2history+language，26579episodes7560942frames。MAE .081，无failure .1312；history0/1/2/3 .096/.088/.081/.086。MPC28actions15steps只最小EE-objectdistance，不是completion。仿真PPO π0+sim真success；真实DSRL两task20/10约trainingtrajectories，10eval，40→80%/30→70%，成功终止外部信号保留。历史+真实失败恢复合成+真在线RL覆盖；标签是否等policyreachability未证明。
