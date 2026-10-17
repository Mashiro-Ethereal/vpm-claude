# Reward Machines for Deep RL in Noisy and Uncertain Environments

引用键：li2024noisyrm。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2406.00120v4)。
- 版本、发表状态与实际范围：arXiv v4/NeurIPS2024书目状态；实际读摘要、§5.1–5.4一致性/相关事件反例、§6.1–6.6实验及相应失败例。书目所列年份：2024；venue：NeurIPS 2024（除明确写已核验者，书目状态不视为独立确认）。
- WHY：真值事件词汇在现实难得。。
- HOW：比较Naive标签、逐步独立belief更新IBU、直接history→RMstate posterior的TDM。
- WHAT：只有TDM对一般POMDP一致；IBU可重复不确定事件虚增进度。Traffic/Kitchen/ColourMatching实证history推断有效。
- 假设、监督与输入：抽象监督来自groundtruth propositions/RMstate，2Kepisodes+100val/test；部分在线oraclefinetune用于隔离历史效应。
- 验证依据：8runs PPO；VLM仅单独label预测精度对比，不是其无oracle闭环RL验证。
- 边界：错误不是仅每帧分类精度，而是时间相关性；高量oracle监督和已给RM未消除。
- 关联（阅读者推断）：RMbelief/视觉记忆解决同观测历史歧义已经非常直接；弱监督替代需同输入同label预算强比较。
