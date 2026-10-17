# ma2024eureka

## 选择性精读：训练反馈搜索的基础（第二轮）
来源：[arXiv v2](https://arxiv.org/html/2310.12931v2)，实际读§3–4；保存 deep.web.txt。

**原文方法。** 可用环境观测/变量代码作为上下文，LLM多样候选、编译/训练后择优，给总任务分数及各子奖励随训练变化的统计反思并下一代修改；人类反馈另可加入。并非只凭文本判断候选。
**验证。** §4沿原bench PPO超参，Isaac与BiDex共29环境；§4.3固定候选预算下进化优于只扩大首轮样本，主结果83%任务超过人类、平均人类归一化52%改善。Fig6奖励和专家奖励相关性低但仍有好策略，说明reward-value similarity不是策略效用的充分标准；这是已训练结果的相关分析，不是前瞻低预算预测。
**与RF。** RF改外层搜索组织及thought/action；继承独立任务评价、内层PPO和重复训练。新工作不能声称首次训练统计反思或奖励程序evolution。

**标题**：Eureka: Human-Level Reward Design via Coding Large Language Models

**书目登记**：Yecheng Jason Ma; William Liang; Guanzhi Wang; De-An Huang; Osbert Bastani; Dinesh Jayaraman; Yuke Zhu; Linxi Fan; Anima Anandkumar；2024；ICLR 2024。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2310.12931)。版本记录：[Submitted on 19 Oct 2023 (v1 ), last revised 30 Apr 2024 (this version, v2)]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：让LLM知识真正影响复杂低层控制，避免任务特定奖励模板。

**原文方法/输入监督**：GPT-4生成代码，基于训练反馈批量进化优化；可纳入人类反馈、课程。

## 初筛记录：摘要证据

摘要：29环境/10机器人形态，83%任务胜专家；平均归一化改进52%；模拟ShadowHand转笔。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：这些原文数字不是RF-Agent同预算重实现结果；消耗完整策略训练、依赖状态代码和任务指标。

**阅读者推断/关联**：奖励搜索反馈基线，后续必须区分新搜索机制与更大预算。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/ma2024eureka.abs.web.txt`（若首轮批量来源为 `ma2024eureka.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
