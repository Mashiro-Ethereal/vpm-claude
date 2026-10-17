# zhang2026dream2reward — Dream2Reward: Transition-Alignment Reward Models from Positive Demonstrations for Robotic Manipulation

阅读日期：2026-10-06。书目年份/venue：2026；arXiv（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2608.18787)；[书目正式版本](https://arxiv.org/pdf/2608.18787)。版本：[Submitted on 19 Aug 2026]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/zhang2026dream2reward.web.txt](_sources/zhang2026dream2reward.web.txt)。

- 原文问题：比较观察transition与成功transition预测，罚错误方向/overshoot/stagnation。
- 原文方法/输入/监督：positive demos学language-conditioned latent transition field；visual history预测displacement，再signed direction与symmetric magnitude匹配；无failure/progress/synthetic negatives。
- 原文摘要报告的验证：机制诊断、shared trajectories、online/offline policy及real robot。
- 阅读者判断/待核细节：successful field对多种可行解的覆盖和policy dependence需正文；不能直接说value=advantage。
- 与基础工作的关系：反例挑战‘绝对progress不足所以加transition’这个宽泛方向。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2608.18787v1](https://arxiv.org/html/2608.18787v1)。实际范围：§III–VI，含全部§IV命题与V-A–G。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/zhang2026dream2reward.full.reading.txt](_sources/zhang2026dream2reward.full.reading.txt)。

正文证据与阅读判断：4帧视觉历史/语言成功转移field与实际转移signed cosine×对称幅度匹配，直接reward，非PBRS。EgoDex/OXE正例训练，无失败label；非零norm下稳定性及相同scalarprogress方向分离不是完成可达性/最优策略定理。TableI 400真实轨迹AUC .95 vsRobometer .93/Dopamine .41；Fig5包含抓空后恢复。真实4任务离线RL每50demo+50mixedrollout，50eval/任务，69/200=34.5% vs28/22.5/17%。在线只LIBERO两任务5seed300kSAC；Dopamine直接nativeprogress归一reward、Robometer借原论文，非完整原生系统比较。历史、方向、正例训练和局部恢复已覆盖；多解成功field覆盖和最终policy可达性仍须另定义。
