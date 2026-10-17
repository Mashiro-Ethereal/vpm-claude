# Ground-Compose-Reinforce: Grounding Language in Agentic Behaviours using Limited Data

引用键：li2025gcr。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2507.10741v2)。
- 版本、发表状态与实际范围：arXiv v2 2025-10-26，作者recordNeurIPS2025；实际读§3–7、附录A shaping算法、B1/B2/B3关键设置与C开头。书目所列年份：2025；venue：NeurIPS 2025（除明确写已核验者，书目状态不视为独立确认）。
- WHY：语言grounding不应依巨大数据或手工oracle。。
- HOW：labelledtrajectories学谓词；离线PVF对每literal学习reachability-value，max/min逻辑组合+RMsuccessor bootstrap近似V*(s,u)，辅助RL。
- WHAT：350DrawerWorldtraces仅单box动作，组合三box/重复持物任务能实现新行为；已是物理剩余任务价值势的直接近邻。
- 假设、监督与输入：GeoGrid结构图像5000randomtraces；DrawerWorld78维位置向量、350teleop并刻意含掉落/失败；groundtruthhandlabels。
- 验证依据：5runs+100/20eval；DrawerPVF实际MonteCarlo regression优于MCQ；B2实验用λ(v′−v)省γ，作者承认损理论性质。
- 边界：正文PBRS算法与实际无折扣势差需分开；非像素机器人；指定RM/词汇、组合近似非精确V*。
- 关联（阅读者推断）：不能声称首次从剩余可达性/组合价值做势或未见组合任务；可撤销当前谓词+RMhistory接口已能表达义务。
