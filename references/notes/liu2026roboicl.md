# liu2026roboicl

## 选择性精读：强策略与比较条件（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2609.34261v1)，原始来源核实题名/版本，实际读§3–4.3；保存 deep.web.txt/roboicl_exp.detail.web.txt。这是新预印本，非已获独立复现。

**方法。** 冻结GPT-6 Astra用示范和自身观测-动作-执行回执-观测记忆直接输出小段动作；固定初始anchor和分散时间记忆。50图片上限下共享示范/互动memory；主1shot J=B=12，0shot B25，3相机拼triptych。零样本不等于没历史或执行反馈。

**证据与条件。** 10任务面板5layout，1shot60.60、zero45.60、Direct38.50（Table1），不同外部controller动作/观测接口。30任务Table2 overall50.64是进度分数，非成功率；Open零样本其余一示范，seed0，每任务20或50评估，放弃任务计0；外部基线公开协议不同。真机3任务5trial各条件，进度14.45→63.33→78.89；3shotPeg2/5完整插入（§4.3）。少试验不能确定普遍真实精度。

**关联。** 未训练参数/奖励也可通过反馈记忆取得较强真实行为；必须成为新奖励学习方向的适用条件挑战。示范、接口和大量在线推理有成本，不能当作免费oracle或所有低层RL替代。

**标题**：RoboICL: Embodied In-Context Learning with GPT-6 Astra

**书目登记**：Fangcheng Liu; Yeqing Shen; Anda Cheng; Weishi Mi; Chao Tang; Chenyuan Liu; Yushun Xiang; Tingguang Li; Yong-Lu Li; Yehui Tang；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2609.34261)。版本记录：[Submitted on 28 Sep 2026]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：直接VLM控制的精度和长程能力弱。

**原文方法/输入监督**：示范+action/outcome交互grammar，boundedanchoredmemory保留早经验，无参数更新/VLA。

## 初筛记录：摘要证据

摘要：30RoboDojoOverall50.64 vs33.68；真机3任务progress14.45→63.33→78.89。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：one/3shot示范、memory机制；总体score非成功率，少真机任务。

**阅读者推断/关联**：记忆/错误修正强直接策略基线，不能用旧zero-shotplanner代表竞争。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/liu2026roboicl.abs.web.txt`（若首轮批量来源为 `liu2026roboicl.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
