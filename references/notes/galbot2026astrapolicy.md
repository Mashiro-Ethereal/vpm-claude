# galbot2026astrapolicy

## 选择性精读：强直接策略的条件与失败（第二轮）
来源：[arXiv v1](https://arxiv.org/html/2609.38537v1)，实际读操作控制/评价、RoboDojo/RoboLab、灵巧双手与RoboCasa实验（正文对应节）；保存 deep.web.txt。版本身份由arXiv原始来源确认，仍属近期预印本。
**证据。** RoboLab偏语义抓放10任务各5试验Direct49/50、Hybrid46/50；不能由此推任意低层控制。RoboDojo选10任务按π0.5表现分层、每5场景，Direct/Hybrid配对但published列重新加权，非统一训练对比。DexJoCo成功5/10，指导两试验间修改，63.60M记录token含缓存，73.6%物理动作来自冻结π0.5。直接灵巧任务已有负面：平移Astra1/5而任务RL4/5，误差59.05vs17.29mm；抓牢也不代表可精确控制。
**关联。** 语义规划很强与动态接触控制薄弱同时存在；新奖励学习需要后者的适用条件及训练后部署成本优势，不能把无权重更新直接等同低计算/低反馈。

**标题**：Systematically Exploring the Capabilities of GPT-6 Astra as Embodied Policies

**书目登记**：Galbot Team; Xuchuan Chen; Xiaoqian Cheng; Yu Deng; Lihe Ding; Shaocong Dong; Xiangjun Gao; Haozhe Jia; Zekai Li; Zhoujian Li; Yunrui Lian; Sikai Liang; Chenghuai Lin; Dairu Liu; Jiahang Liu; Qingtao Liu; Yuxuan Ma; Zekun Qi; Jiayi Su; He Wang; Ruochen Xu; Tianyu Xu; Xudong Xu; Zhe Xu; Mi Yan; Siming Yan; Li Yi; Ruixi Yu; Jinlu Zhang; Yintianrun Zhang; Zhikai Zhang; Zhizheng Zhang; Yixin Zheng; Weiyi Zhu；2026；arXiv。

**实际读取来源**：[原始来源](https://arxiv.org/abs/2609.38537)。版本记录：[Submitted on 29 Sep 2026]。

阅读日期：2026-10-06。当前范围：**见文件顶部精读记录**。初筛时范围为原始摘要。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：全面评估Astra直接/混合具身控制及反馈适应。

**原文方法/输入监督**：六domain；数值actions、π0.5混合、whole-bodycontroller等接口。

## 初筛记录：摘要证据

摘要：部分RoboDojo hybrid48%；导航92/82%；locomotion5次失败；大量tokens、物理暂停39.86s平均call。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：多任务不同protocol；较高success不等于实时动作可靠。

**阅读者推断/关联**：比较奖励训练与在线语言控制必须核推理延迟与预训练技能。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/galbot2026astrapolicy.abs.web.txt`（若首轮批量来源为 `galbot2026astrapolicy.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
