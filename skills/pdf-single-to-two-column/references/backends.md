# 后端与证据边界

## 已核对的接口

- Codex 官方 MCP 文档说明本地客户端可用 stdio，远程服务可用 Streamable HTTP；配置入口是 `~/.codex/config.toml` 与 `codex mcp add/list`：<https://developers.openai.com/codex/mcp>。
- Word VBA 的 `TextColumns.SetCount` 是正文分栏接口：<https://learn.microsoft.com/en-us/office/vba/api/word.textcolumns.setcount>。
- Word 的 `Document.ExportAsFixedFormat` 可导出 PDF/XPS：<https://learn.microsoft.com/en-us/office/vba/api/word.document.exportasfixedformat>。

## Office MCP 结论（2026-07-23）

| 方案 | 传输/边界 | 实测或静态审计 | 适合本 skill 吗 |
|---|---|---|---|
| `word-mcp-live` | 本机 Python stdio/SSE/HTTP，pywin32 + python-docx | v1.6.20 启动成功；MCP `initialize`、`list_tools`（120 工具）和 `word_live_list_open` 只读调用成功；没有正文 `TextColumns/SetCount`，只有表格列工具 | 可作为未来 Office 连接器，当前不能直接完成双栏 |
| `mcp-msoffice-interop-word` | Node stdio/SSE，winax COM | 有文档打开/保存和页面设置，未发现正文 TextColumns 工具 | 不作为当前后端 |
| OfficeMCP | Windows Python COM；提供任意 `RunPython` | 可理论上调用 Word COM，但任意代码执行面过大，且没有专用双栏契约 | 不作为默认依赖 |
| Microsoft Work IQ Word MCP | OneDrive/SharePoint 云端预览 | 官方文档为 preview，需要 M365 Copilot/租户/管理员治理；不操作本机 PDF | 不适合本地批处理 |

`word-mcp-live` 的“column”命名可能指表格列，不能把它误报为页面双栏。若未来要通过 MCP 做双栏，应新增一个最小、可审计的 `word_live_set_text_columns(count=2)` 工具，内部只调用 `Section.PageSetup.TextColumns.SetCount`，不要暴露任意 Python 执行。

## 样例 PDF 验证边界

用户可见样例 `01-react-synergizing-reasoning-and-acting.no_watermark.zh.mono.pdf` 是 33 页 Letter 的 BabelDOC 翻译输出，含嵌入字体和公式/学术排版。它适合验证 Word/PDF 导入边界，但不能再次作为 BabelDOC IL 后端的输入；BabelDOC 会用元数据守卫抛出 `InputFileGeneratedByBabelDOCError`。

- Word COM 的 DOCX→PDF 路线在本机 Word 16.0.20131 上通过：1 个 section 的 `TextColumns` 从 1 变为 2，导出 PDF 成功，输出页数发生变化，页面尺寸保持 Letter。
- Word COM 直接打开这个 PDF 在无界面自动化中卡在 `Documents.Open` 的 PDF 导入阶段，不能当作成功路径；不同 Office 安装可能不同，因此脚本将 PDF 导入设为显式 `--allow-pdf-import`。
- 有损基线 `pdftotext -layout → Pandoc DOCX → Word COM` 确实生成了双栏 PDF，但首屏出现作者/摘要/正文顺序和断行损坏；这证明纯文本重排只能用于诊断，不适合论文默认批处理。

## BabelDOC IL 后端（实验）

- 本机可用解释器：`D:\hkust-gz-ra-paper-reading\.venvs\pdf2zh-reflexion\Scripts\python.exe`；`pdf2zh-next 2.9.0` 搭配 `babeldoc 0.6.2`。
- BabelDOC 后端的输入必须是未经过 BabelDOC 的 born-digital 原 PDF。ReAct 试跑使用 `_translation-sources\01-react-synergizing-reasoning-and-acting.pdf`，不是同目录的 `*.no_watermark.zh.mono.pdf`；不要删除元数据或绕过守卫来重复处理 BabelDOC 产物。
- 可迁移的架构：native parser 建立 Page/Paragraph/Character/Formula/Figure/Form/Curve IL，LayoutParser 识别版面，Typesetting 做行布局，PDFCreater 复用页面尺寸和原 PDF 的资源/非文本对象。
- 本 skill 的适配器只启用 `skip_translation=True`，不会调用翻译器或写入密钥；使用 page-level column flow，默认跳过首屏，含图表/公式/图注的页默认 passthrough。
- 代表性 1--3 页试跑已产出独立 PDF、manifest 和 PNG render；页 2 的图形对象保留，页 2--3 的安全正文进入两栏，源文件 SHA-256 保持可核对。该结果仍需人工检查词间空格、阅读顺序和字符映射，不能作为论文出版级保证。
- 内部 API 不稳定。manifest 必须记录 BabelDOC 版本和 `font_scale`；版本漂移、`page-flow-failed`、重叠或文字不可选时停止全量。

## 验收建议

先对代表性 3--5 页做截图和文本顺序抽查，再做全量。需要保留公式、表格、图片和脚注时，优先回到 DOCX/LaTeX 或安装并锁定布局感知解析器；不要以文件能打开或页数变化作为唯一成功标准。
