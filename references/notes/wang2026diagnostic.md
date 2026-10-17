# wang2026diagnostic

## 选择性精读：选择反证、预算控制与诊断局限（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2605.28918v1)，读§3、§5–9.7及论文给出的限制；保存 deep*.web.txt 与 diagnostic_selection.detail.web.txt。

**方法与验证。** 根据稀疏任务失败taxonomy、probe统计和API语义反馈修改奖励；MiniGrid最多3×500probe+3000最终=4500episode，比单次多50%。§8.2静态词汇控制显著追回metrics-only差距，故收益不能仅归动态检测标签。§8.5 probe300/500/800的总体成功0.62/0.78/0.96（各3seed）显示诊断本身需要样本，不可假设越短越够。

**最重要反证。** §9.7相同4500预算Best-of-3短训选后重训：DoorKey8 92.3 vs迭代97.6；KeyCorr60.1vs86.7；UnlockPickup24.3vs24.3。10seed差异Welch p=0.51/0.106/1，bootstrap CI全含0。诊断修订优于强选择的证据尚未确认。§9.5同预算no-shaping在Hopper882，高于原诊断525；return-aware改造472也无增益。原success检测面对无二元成功指标运动任务持续误报reward hacking。§9.6单anchor固定LLM/RL种子方差估计不能作严格方差分解。

**关联。** 新研究必须分清奖励设计缺陷、训练不足、评价接口失配。论文已研究跨候选短probe选择；还未评估跨family/task/optimizer的可泛化预测器。

**标题**：When LLM Reward Design Fails: Diagnostic-Driven Refinement for Sparse Structured RL

**书目登记**：Youting Wang; Yuan Tang; Bowen Liu; Xuan Liu; Dingyan Shang；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2605.28918)。版本记录：[Submitted on 27 May 2026]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：稀疏结构任务中one-shot奖励误解API/语义或reward flooding。

**原文方法/输入监督**：训练诊断与失败taxonomy定向修订，metrics-only、static-vocab与best-of3预算对照。

## 初筛记录：摘要证据

摘要：DoorKey2.3→97.6%，KeyCorridor31.2→86.7%，seed方差高；taxonomy静态控制已恢复多收益。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：MiniGrid/PPO核心；MuJoCo边界没有稳健收益。

**阅读者推断/关联**：诊断性修订不是新颖性本身，关键是新的可测故障与证据条件。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/wang2026diagnostic.abs.web.txt`（若首轮批量来源为 `wang2026diagnostic.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
