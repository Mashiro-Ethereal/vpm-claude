# xu2026flora

## 选择性精读：离线代理搜索和实机泛化（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2605.22123v1)，实际读§III–VI及定理1证明概要；保存 deep*.web.txt。补充材料的完整证明/硬件细节未取得。

**原文方法。** 运动流关系→符号势φ，历史milestone状态m组成Φ(s,m)=φ(s)+Ψ(m)，用γΦ′−Φ塑形。LLM搜结构、BO搜参数，5示范60/40分训练验证；代理含阶段标签准确、与时间Spearman、非负势差比例。结构搜索不用每候选在线RL。定理保证在增广MDP的PBRS及原奖励不依赖m等条件下最优行为保持；并不保证有限样本加速。

**核对证据。** 8MetaWorld，Table I过程对齐0.97/轨迹排序0.80，排序真值来自专家dense奖励；策略RLPD3seed，简单100k困难200k（§VI-B）。§VI-B将方法间指标趋势对应称可靠效用预测，未见大量候选持出预测/校准曲线。真实Franka3任务：奖励各5示范，策略初始化前两任务5、Bulb20示范；Table II/§VI-C前两20min接近100%、Bulb1h45%。真实OOD位置/视角/对象测试并非全部下游在线训练泛化，也不覆盖不可见/大遮挡。仿真OOD保持物体可见，30°视角/40cm位置变化。

**对研究问题的挑战。** “视觉不变符号奖励+PBRS+结构参数分开+离线局部指标+实机OOD”已经组合实现。仍可研究learner/budget条件效用，但须直接对照该代理而不是声称首次无需RL候选筛选。

**标题**：Beyond Pixels: Learning Invariant Rewards for Real-World Robotics From a Few Demonstrations

**书目登记**：Tengye Xu; Yangting Sun; Ziju Shen; Guanqi Chen; Zhen Fu; Yizhou Chen; Hua Chen; Jia Pan；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2605.22123)。版本记录：[Submitted on 21 May 2026]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：像素分布拟合的奖励不能泛化物体/位置/相机。

**原文方法/输入监督**：5示范起步的符号不变量奖励，结构化task策略/物理约束+符号数值提取，无在线交互。

## 初筛记录：摘要证据

摘要：MetaWorld8+Franka3，3组真实OOD，奖励零样本位置/视角/物体泛化。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：示范和符号/视觉接口重要；policy invariance必须读理论条件。

**阅读者推断/关联**：极近视觉可迁移结构奖励，首次不变量/少示范真实泛化不能直接主张。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/xu2026flora.abs.web.txt`（若首轮批量来源为 `xu2026flora.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
