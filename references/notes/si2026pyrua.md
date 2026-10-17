# si2026pyrua

## 选择性精读：计算预算与无需新奖励的改进（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2610.01939v1)，实际读§3–5及表1–3；保存 deep.web.txt。原始来源核实，不从题名补充结论。

**方法。** 同GPT-6 Astra、同RPent经典/VLA primitives；代码cell内条件、局部重试、几何计算，按需返回图；对照逐工具调用。700仿真实例，一次运行/实例，LLM调用限40（复合RoboCasa100）及2h。调用限制不等于相同primitive执行数。

**核对结果。** Table2成功63.1→71.7，8.6百分点≈14%相对，而非14百分点。共同成功子集调用17.0→8.7、input788k→276k，49%/65%节约；未涵盖全失败尝试成本。移除VLA/guide仍有收益（Table3），但不能完全分离接口各成分因果贡献。§4.5/5只仿真、单次、固定planner/primitive，真机未知。

**关联。** 确认强具身策略不一定先新增奖励模型；新奖励方向应比较总训练与部署推理预算，并选择primitive组合失败而学习策略有独立价值的任务。

**标题**：Fewer Tokens, Better Action: GPT-6 Astra Robot Agents with 14% Higher Success Rate but 65% Fewer Tokens

**书目登记**：Ruiyang Si; Jianxin Bi; Shunyu Yang; Rui Ni; Wenbo Huang; Qiang Wang; Shulong Jiang; Duomin Wang; Xiuyu Li; Haiwen Feng; Zhen Dong; Daquan Zhou；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2610.01939)。版本记录：[Submitted on 1 Oct 2026]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：VLM逐call和冗余image成本高。

**原文方法/输入监督**：Pythoncell组合classical/VLAprimitives，本地condition/retry，选择观测后replan。

## 初筛记录：摘要证据

原始摘要：700siminstance，sameplanner/primitive/equalcallbudgets，success63.1→71.7%；共同成功子集inputtokens−65%。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：14%是相对提升，8.6百分点；token减幅条件是两者都成功实例。

**阅读者推断/关联**：无需reward的agent工具效率已有；推理与RL总成本应分开。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/si2026pyrua.abs.web.txt`（若首轮批量来源为 `si2026pyrua.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
