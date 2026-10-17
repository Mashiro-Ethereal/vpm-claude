# he2026spars

**标题**：SPARS: Structure-informed progress-aware reward shaping for fabric manipulation learning from demonstration

**书目登记**：Ruhan He; Yifei Wei; Lianqing Yu; Xianyi Zeng；2026；Robotics and Autonomous Systems 203, 105499 (September 2026)。

**实际读取来源**：[原始来源](https://www.sciencedirect.com/science/article/abs/pii/S0921889026001727)。版本记录：原始来源见保存片段；正式版本状态按来源确认，不从书目标题推断。

阅读日期：2026-10-06。范围：**官方出版商索引摘要与节摘录；全文访问受限**。此为第一轮阅读笔记，后续精读在本文件追加。

## 问题与方法

**原文问题**：布料多阶段credit难，示范只用action丢失expert FSM结构。

**原文方法/输入监督**：从FSM归纳对齐/轨迹/目标三相，随学习progress改权重，配PER与网络改进。

## 已读证据

ScienceDirect原始索引摘要：cloth69% vs41%，variance降63%；UR5 RGBD sim2real。

## 边界与基础关联

**边界**：首次直接open失败；已读官方索引摘要/intro/section snippets，完整方法表受限。

**阅读者推断/关联**：阶段奖励随训练动态调配已做；进度是学习进度而非必为单轨迹进度。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/he2026spars.abs.web.txt`（若首轮批量来源为 `he2026spars.web.txt`，见该文件）；ScienceDirect获取补充见 `_sources/search_policy_sciencedirect_original.web.txt`。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。

