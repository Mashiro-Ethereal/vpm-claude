# RoboRecover: Benchmarking Robot Policy Recovery under Execution Deviations

引用键：li2026roborecover。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2609.28952v1)。
- 版本、发表状态与实际范围：arXiv v1 preprint；实际读§4全部构造与§5主要实验含§5.5monitor/corrector。书目所列年份：2026；venue：arXiv（除明确写已核验者，书目状态不视为独立确认）。
- WHY：执行动作造成偏离中间态需恢复。。
- HOW：RoboTwin+LIBERO各1000failurestate；自然/扰动/人工轨迹replay，3annotator；referencepolicies4×5trial筛10–90%可恢复难度。
- WHAT：WrongTarget/Pose/StageRollback/SceneChange跨phase； nominal高分≠recovery；monitor+correction改善。
- 假设、监督与输入：每域800train200test，过滤irreversibledamage；simreplayobject/ee<2mm，SSIM>.99，实际历史前缀。
- 验证依据：LIBEROpi0.5 base64.4，Correction71.2，monitor+Correction75.5；bestperstateoracle91.8为回看非可部署。
- 边界：Reversion30步回退改变初态，非same-statefairleaderboard；恢复点过滤由referencepolicy能力影响。
- 关联（阅读者推断）：训练failuremonitor+corrector与stage rollback已经覆盖；需比较条件义务学习而不是另写检测恢复pipeline。
