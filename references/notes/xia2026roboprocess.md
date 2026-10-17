# RoboProcessBench: Benchmarking Process-Aware Understanding in Vision-Language Robotic Manipulation

引用键：xia2026roboprocess。阅读日期：2026-10-06。

- 来源：[实际读取原始来源](https://arxiv.org/html/2606.13040v3)。
- 版本、发表状态与实际范围：arXiv v3 preprint；实际读完整摘要、引言和§3方法开头，非实验精读。书目所列年份：2026；venue：arXiv（除明确写已核验者，书目状态不视为独立确认）。
- WHY：VLM评测需物理/时间过程理解。。
- HOW：static monitoring与dynamic reasoning，12问题族。。
- WHAT：~58KQA260tasks/12问题族staticmonitor+dynamicreasoning；posttrainQwen2.5VL7B/InternVL3-8B改善局部过程判断。
- 假设、监督与输入：操作视频和问答标注。。
- 验证依据：本次读取摘要声明与数据框架，未逐表审实验。
- 边界：VLM过程QA不等于闭环policy改善；含实际tracemetadata监督。
- 关联（阅读者推断）：过程评价近邻与可用测试。。
