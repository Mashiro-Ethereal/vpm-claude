# Replacing Rewards with Examples: Example-Based Policy Search via Recursive Classification

Eysenbach, Levine, Salakhutdinov；NeurIPS 2021。补充检索，2026-10-06。

- 来源：[正式论文](https://proceedings.neurips.cc/paper/2021/file/5ffaa9f5182c2a36843f438bb1fdbdea-Paper.pdf)、[可读全文](https://arxiv.org/html/2103.12656)。保存了 PDF 和文本。
- 实际阅读：摘要、§3.1–3.2、§4.1–4.2、§5.1–5.3、结论；补充浏览 HTML 附录的任务实现说明，未逐行审查所有证明。
- 问题：只有成功状态示例和转移数据时，能否直接学习达到成功的策略，省去独立奖励估计。
- 方法：递归分类成功未来对应的状态动作与普通状态动作，分类 odds 对应折扣未来成功量，以 Bellman 形式更新并改进策略。
- 假设：成功示例自身不能唯一确定成功概率。§3.1 明确要求用户访问状态边际与转移数据边际的联系；另给未知边际下的稳健目标及与 Hellinger 散度的关系。理论分析为相应理想化设置，神经模型输出并非自动校准的概率。
- 实验证据：状态输入的 Sawyer 与 dexterous-hand 任务，成功示例而非完整示范；3 个图像任务覆盖位置/尺寸变化和清桌。相同示例监督下比较 VICE、ORIL、PURL、DAC、SQIL 等。图像尺寸泛化成功；作者也报告更复杂图像任务仍难学。
- 边界：结论明确承认分类预测校准不足。没有语言条件的多阶段视觉进度表示，但“直接预测未来成功而非设计奖励”已被提出并验证。
- 对本项目的判断：新方向若输出 reachability，需先回答为何不是 RCE/目标条件价值学习，以及新增状态表征或监督如何减少失败后的估计偏差。仅将输出命名为 progress 或 completion potential 不构成区别。
