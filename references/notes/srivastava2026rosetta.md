# srivastava2026rosetta

**全文获取补充（2026-10-06）**：已按验证可用的显式联网升级方式尝试OpenReview公开PDF一次，服务器返回HTTP403，记录见 `_sources/srivastava2026rosetta.download_log.txt`。没有重复此端点；当前阅读范围仍为下述完整作者项目页，而非正式PDF正文。

## 选择性阅读：作者完整项目页的方法与评价
来源与范围：[项目页](https://sanjanasrivastava.github.io/rosetta-project/)全部文字方法、数据、设置、评价；正式PDF受OpenReview验证页阻挡，未称全文精读。原始片段 abs.web.txt。
**原文证据。** 116偏好+30困难偏好，同一个用户最多4轮改变要求；grounding→staging→code后训练一些变体，由原用户挑选。2连续短程/3primitive长程ManiSkill，PPO/SAC-MAPLE。结果87%优化目标成功、86%用户满意，任务成功不能判断当前偏好；专家另看语言和代码语义。80%偏好修改要求，25%包含纠正，这些属性可重叠。Eureka/Text2Reward在纠正子集可同样好或更好；no-grounding保留旧容易奖励的优化性不错但语义不符。真机primitive transfer依FoundationPose提供正确状态。
**推断。** 原用户选择与反馈不是零成本；优化性、程序语义、最终行为满意已经被明确区分。奖励新研究仅提高bench成功而不检查偏好，会遗漏这里的实证失败。

**标题**：ROSETTA: Constructing Code-Based Reward from Unconstrained Language Preference

**书目登记**：Sanjana Srivastava; Kangrui Wang; Yung-Chieh Chan; Tianyuan Dai; Manling Li; Ruohan Zhang; Mengdi Xu; Jiajun Wu; Li Fei-Fei；2026；ICLR 2026。

**实际读取来源**：[原始来源](https://sanjanasrivastava.github.io/rosetta-project/)。版本记录：原始来源见保存片段；正式版本状态按来源确认，不从书目标题推断。

阅读日期：2026-10-06。当前范围：**作者完整项目页详细阅读；正式PDF仍受限，见顶部获取记录**。当前实际阅读范围以文件顶部的精读记录为准。以下小节保留第一轮初筛记录；后续已核实内容以顶部为准。

## 初筛记录：问题与方法

**原文问题**：人类偏好多样、含糊、动态，固定成功指标不足。

**原文方法/输入监督**：作者页：gpt-4o做偏好场景落地和staging，o1-mini代码，训练候选后原偏好作者选择。

## 初筛记录：摘要证据

作者页：116偏好，87%成功、86%满意；短程PPO、长程MAPLE原语SAC，真实平台用FoundationPose状态。

## 初筛记录：边界与基础关联

**初筛时待核边界（当前以顶部为准）**：OpenReview被浏览器验证页阻挡；已读作者页摘要/方法/评价，暂非正式PDF全文。

**阅读者推断/关联**：直接覆盖动态偏好、分阶段奖励代码、成功与语义/人类满意度分开评价。

来源身份与版本以原始来源记录为准；原文摘要中的改进值仅作作者报告，未将其冒充已核对表格。原始读取片段见 `_sources/srivastava2026rosetta.abs.web.txt`（若首轮批量来源为 `srivastava2026rosetta.web.txt`，见该文件）。基础两篇分别链接 [RF-Agent笔记](base_rf_agent.md) 和 [PRM4RL笔记](base_progress_reward.md)。
