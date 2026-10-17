# donahue2024gtcc — Learning to Predict Activity Progress by Self-Supervised Video Alignment

阅读日期：2026-10-06。书目年份/venue：2024；CVPR 2024（未将书目venue自动视作本次核验）。来源：[原始摘要/作者页面](https://openaccess.thecvf.com/content/CVPR2024/html/Donahue_Learning_to_Predict_Activity_Progress_by_Self-Supervised_Video_Alignment_CVPR_2024_paper.html)；[书目正式版本](https://openaccess.thecvf.com/content/CVPR2024/papers/Donahue_Learning_to_Predict_Activity_Progress_by_Self-Supervised_Video_Alignment_CVPR_2024_paper.pdf)。版本：正式出版/作者页面；见来源记录。实际范围：**摘要初筛**，已读取完整可得摘要，不声称已读实验正文。来源记录：[_sources/donahue2024gtcc.web.txt](_sources/donahue2024gtcc.web.txt)。

- 原文问题：in-the-wild视频对齐与进度预测，处理重复/冗余/背景。
- 原文方法/输入/监督：TCC推广为GMM多邻居cycle、多cycle-back回归；context-dependent drop与multihead跨task网络。
- 原文摘要报告的验证：多数据集alignment/progress预测优于既有，正式CVPR摘要。
- 阅读者判断/待核细节：摘要未给闭环RL，且已处理action ordering/重复，不能称视觉进度都假设固定单调帧序。
- 与基础工作的关系：与阶段/历史结构有关，但奖励闭环需单独检验。CVF直接403，搜索返回原CVF摘要。

局限：上述实验数字是摘要中的作者报告，未核对表格、误差及完整比较条件；正文没有在此阶段读取的内容保持开放。

