# hung2025victor — VICtoR: Learning Hierarchical Vision-Instruction Correlation Rewards for Long-horizon Manipulation

阅读日期：2026-10-06。书目年份/venue：2025；ICLR 2025（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://arxiv.org/abs/2405.16545)；[书目正式版本](https://proceedings.iclr.cc/paper_files/paper/2025/file/2c74f005aabbf90a8f1747d99f387321-Paper-Conference.pdf)。版本：[Submitted on 26 May 2024 ( ), last revised 20 Feb 2025 (this version, v2)]。实际范围：**已读摘要及下列正文节，具体见精读记录**；未列明的正文与附录保持开放。来源记录：[_sources/hung2025victor.web.txt](_sources/hung2025victor.web.txt)。

- 原文问题：长程hierarchical visual-instruction correlation reward。
- 原文方法/输入/监督：action-free视频+language，stage detector和motion-progress evaluator，关注object state。
- 原文摘要报告的验证：仿真/真机，摘要称long-horizon成功率提升43%。
- 阅读者判断/待核细节：43%是作者摘要口径，未判绝对/相对；stage标签和输入需全文。
- 与基础工作的关系：显式阶段+局部motion进度已经是近邻。

阅读局限：本次为选择性正文精读；尚未核对的表格、图像与附录以末尾实际阅读范围为准，不将已读结论外推到这些部分。


## 选择性正文精读更新

版本：[2405.16545v2](https://arxiv.org/html/2405.16545v2)。实际范围：§3–5.2及主表1/2，未全部附录。定位使用 HTML 节/表/公式，不冒称 PDF 页码检查通过。源文：[_sources/hung2025victor.full.reading.txt](_sources/hung2025victor.full.reading.txt)。

正文证据与阅读判断：GPT4生成stage/objectconditions/motions，objectcropclassifier+CLIPmotionprogress；Φ累计前序motion+currentfineprogress，rewardΦ'−Φ（并非γΦ'−Φ）。sim10tasksPPO+success、groundtruthobjectdetector加速，3seed；3stage5motion57.7% vsLOReL28.9%。XSkill realvideo诊断非realclosedloop。PRMstagehierarchy近邻但视觉网络/监督不同；objectstate充分阶段判断假设并未覆盖任意history计数。
