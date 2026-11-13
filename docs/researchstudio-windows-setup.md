# ResearchStudio Windows 安装记录

核对日期：2026-11-13。完整本机指南：[D:/research-stdio/SETUP.zh-CN.md](D:/research-stdio/SETUP.zh-CN.md)。

- 主仓库：[microsoft/ResearchStudio](https://github.com/microsoft/ResearchStudio)，`063f10088af49909e1a4a7ea8d29efe19633f34e`，本机 `D:\research-stdio\ResearchStudio`。
- 视频依赖完整克隆在 `D:\research-stdio\components\ppt-master` 和 `pptx2video`；commit 与许可记录见 [第三方来源](../skills/THIRD_PARTY_SKILLS.md)。
- 全局安装：`C:\Users\Administrator\.codex\skills`。同步：本仓库 `skills/`。11 个顶层技能加嵌套 `html2pptx`，保留完整可运行脚本、模板、引用资源和许可。
- 用户/项目 `.agents/skills` 通过目录链接兼容当前 Codex 发现路径；不更改全局模型、鉴权或权限设置。
- 独立 Python 3.11.15：`D:\research-stdio\.venv`。启动时执行 `. D:\research-stdio\Start-ResearchStudio.ps1`，再运行 `codex`。
- venv 的基础解释器来自 `C:\ProgramData\Anaconda3\envs\devdefender-lab`；它隔离包安装，但迁移/删除基础 conda 环境时要重建 venv。
- 原生依赖：LibreOffice 26.8.3.1、FFmpeg/FFprobe 9.0.2，复用 TeX Live 的 Poppler/XeLaTeX。
- `pptx2video==0.5.0` 的 doctor 不识别 FFmpeg 9 的两位 filter flags；使用 `imageio-ffmpeg==0.6.0` 自带 FFmpeg 7.1，并显式配置 `PPTX2VIDEO_FFPROBE`。不改或绕过 QA。
- `scholarly==1.7.11` 导入旧 bibtexparser 模块，故固定 `bibtexparser<2`。
- CairoSVG 复用本机 `C:\ProgramData\Anaconda3\envs\yasi\Library\bin\cairo-2.dll`，启动脚本同时配置 `PATH` 与 `CAIROCFFI_DLL_DIRECTORIES`。其他机器须配置自己的 Cairo。
- 本机 requirements、freeze、安装/镜像脚本、原始失败检查和修复后的检查在 `D:\research-stdio\`。

基础使用不要求新的 API key。完整 Idea 的 OpenReview 连接器在当前代码中要求 `OPENREVIEW_USER`/`OPENREVIEW_PASS`，尽管 setup 文档写为可选；本机匿名请求也返回 403。Semantic Scholar 匿名请求出现 429，建议申请 `SEMANTICSCHOLAR_API_KEY`。OpenAlex 匿名查询可用；大规模与 cursor paging 配置 `OPENALEX_API_KEY`，以[当前官方文档](https://help.openalex.org/api/authentication/)为准。真实算力预算建议每次明确或填 `IDEASPARK_DEFAULT_COMPUTE`。

用户可选填写 `D:\research-stdio\.env`；模板为 `researchstudio.env.example`。不在同步 bundle 中存凭据。AI 配图、外部视觉审核、Pandoc 旧格式转换均按需配置。新技能下一轮可用，未发现时重启客户端。[Codex 官方技能文档](https://developers.openai.com/codex/skills/)

最小使用示例：

```text
$paper-search 检索 2024–2026 年长上下文 KV cache 压缩论文，报告缺失来源。
$idea-spark 为我的研究方向提出一个可证伪方案，严格遵守我提供的真实预算。
$paper2poster D:/papers/paper.pdf
$paper2blog D:/papers/paper.pdf
$paper2video D:/papers/paper.pdf
```

检查命令：`& D:\research-stdio\Start-ResearchStudio.ps1 -Mode Doctor`。`doctor`/安装烟雾检查不等于真实论文全流程和产物质量验收；科研结论需要另外的证据合同。运行细节及最终状态以本机指南和 `evidence/` 为准。

最终验证：8 项安装烟雾检查和 doctor 通过；检索后处理/运行时自检 15+16 项通过；OpenAlex 实际查询返回 RAG 原论文与综述。上游 1 页、3 动画的样例 PPTX 已完整渲染为约 11.67 秒视频，`--qa-mode strict` 返回 0 error / 0 warning（2 条 info），产物和原始 QA 位于 `D:\research-stdio\evidence\video-smoke`。匿名网络仍有明确限制：Semantic Scholar 429、OpenReview 403、arXiv 批量查询 429；没有伪装为全部数据源通过。
