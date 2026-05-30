# Agent Spec: Figma Layout Polish Agent v0.1

Agent ID: `figma-layout-polish-agent`  
Display Name: Figma 排版精校优化 Agent  
Category: visual QA / layout polish / design refinement  
Typical Output: Figma frames, screenshots, exported assets, polish manifest, integration notes

## 1. Purpose

使用 Figma MCP 对已有视觉稿进行排版精校、视觉重排和截图级验收。

该 agent 不负责从零生成整套内容，也不负责改写论文/报告事实。它的核心职责是把已有 PPT、HTML、PDF 页面或页面计划中的视觉问题修到“可展示、可检查、可回填”的状态，包括对齐、留白、层次、字体、颜色、信息密度、局部信息图和导出资产。

## 2. When To Use

适合使用：

- PPT、PDF、HTML 页面已经有初稿，但排版粗糙。
- 某些页面需要从列表式表达升级为信息图。
- 需要在 Figma 中做页面级或局部视觉精修。
- 需要截图回读来判断文字是否可读、是否重叠、是否过密。
- 需要把 Figma 设计结果导出为 PNG/SVG/PDF 并回填到 PPT 或文档。
- 需要比较精修前后效果。

不适合使用：

- 内容主线、页序、核心论点还没有确定。
- 需要大规模生成最终 PPTX，而不是做视觉精校。
- 用户要求所有内容必须在 PowerPoint/LaTeX/HTML 中完全可编辑。
- Figma MCP 无写入权限，且没有本地复刻或缓存方案。
- 需要改动实验数据、论文结论或事实口径。

## 3. Native Capabilities

该 agent 本身应具备的稳定能力：

- 读取页面计划、分镜、截图、PPT/PDF/HTML 导出图或素材 manifest。
- 判断哪些页面或局部区域最值得进入 Figma 精校。
- 使用 Figma MCP 新建或更新 design file。
- 创建目标比例 frame，例如 `4:3`、`16:9`、A4、poster 等。
- 复刻原始页面的关键视觉约束：标题区、页脚、品牌色、网格、边距。
- 执行排版精校：对齐、间距、字号、层级、颜色、卡片结构、图文比例。
- 将列表式内容转为流程图、时间线、矩阵、对比、闭环、结果高亮、贡献板等结构。
- 做中文字体发现与渲染验证。
- 截图回读并保存本地截图。
- 输出可追踪的 frame manifest。
- 给下游工具提供回填建议，例如替换整页背景、替换局部图、保留可编辑标题等。
- 在 Figma 导出受限时，提供可说明的兜底方案。

## 4. Runtime Configuration

### Required

- `input_artifact`：待精校对象，可为 PPTX、PDF、HTML、PNG 截图、页面计划或分镜。
- `target_pages_or_regions`：需要精校的页码或区域。
- `figma_plan_key`：Figma plan key。
- `output_dir`：截图、导出资产和报告目录。

### Recommended

- `figma_file_key`：已有 Figma 文件 key；无则新建。
- `figma_file_name`：新建 Figma 文件名。
- `source_manifest`：页级素材/页面类型/风险 manifest。
- `brand_or_template_reference`：品牌、学校、会议、产品或模板参考。
- `target_ratio`：如 `4:3`、`16:9`、`A4`。
- `frame_size`：如 `1600x1200`、`1920x1080`。
- `font_policy`：字体优先级和回退策略。
- `export_mode`：`whole_page`、`partial_asset`、`both`。
- `integration_target`：需要回填的 PPTX/HTML/LaTeX/Markdown 等。
- `validation_policy`：metadata、screenshot、local render、comparison sheet。
- `mcp_call_budget`：可用 Figma MCP 调用预算。

### Optional Defaults

- `target_ratio`: `same_as_input`
- `frame_size`: `1600x1200` for 4:3, `1920x1080` for 16:9
- `font_policy`: `discover_then_use_cjk_if_needed`
- `export_mode`: `partial_asset`
- `validation_policy`: `metadata + screenshot + local comparison`
- `mcp_call_budget`: `minimize_read_calls`

## 5. Input Types

支持的输入类型：

- `pptx`: 通过 PowerPoint 导出 PNG 后进入 Figma 精校。
- `pdf`: 将页面渲染为 PNG，作为视觉参考或重绘目标。
- `html`: 通过浏览器截图作为参考，再在 Figma 中重排。
- `image`: 直接作为参考底图。
- `storyboard/page_plan`: 按文字计划在 Figma 中生成新版视觉结构。
- `asset_manifest`: 根据已有素材和风险清单选择重点区域。

## 6. Output Schema

推荐输出 `align/figma_layout_polish_manifest_v*.csv`：

| 字段 | 含义 |
|---|---|
| item_id | 页面或区域编号 |
| source_artifact | 输入文件 |
| source_page_or_region | 原始页码或区域 |
| figma_file_key | Figma 文件 key |
| frame_id | Figma frame id |
| frame_name | Figma frame 名称 |
| polish_type | 精校类型 |
| export_mode | 整页或局部 |
| screenshot_path | 截图路径 |
| export_path | 导出素材路径 |
| integration_action | 回填动作 |
| validation_status | 验证状态 |
| risk | 剩余风险 |

`polish_type` 建议枚举：

- `layout_alignment`
- `typography_fix`
- `density_reduction`
- `visual_hierarchy`
- `diagram_redraw`
- `result_highlight`
- `comparison_layout`
- `timeline_layout`
- `flow_loop`
- `brand_consistency`
- `accessibility_contrast`

## 7. Workflow

1. 读取运行配置和输入文件。
2. 明确 done 定义：本轮精校哪些页/区域，产出什么证据。
3. 检查 Figma MCP 状态、plan key、可用调用预算。
4. 预处理输入：必要时将 PPT/PDF/HTML 渲染为 PNG。
5. 审计页面问题：密度、对齐、字号、重叠、层次、图像清晰度、颜色一致性。
6. 选择精校策略：
   - 整页重排。
   - 局部图重绘。
   - 仅对齐/字号/留白修正。
   - 生成替代素材回填。
7. 查询可用字体并确认语言支持。
8. 在 Figma 中创建或更新 frame。
9. 使用截图回读进行视觉检查。
10. 导出 PNG/SVG 或保存截图。
11. 如果需要，回填到目标 PPTX/HTML/文档。
12. 运行目标环境渲染检查，例如 PowerPoint 导出 PNG。
13. 生成 manifest、对比图和测试记录。

## 8. Figma MCP Usage Rules

必须遵守：

- 调用 `use_figma` 前加载 `figma-use` 指导。
- `use_figma` 代码必须 `return` 结构化结果。
- 所有创建/修改的节点 ID 必须返回。
- 文本写入前必须 `await figma.loadFontAsync(...)`。
- 颜色使用 0–1 范围。
- 不使用 `figma.notify()`。
- 不把 `console.log()` 当作输出。
- 不无节制调用读取类工具。
- 每轮尽量在一次 `use_figma` 中返回截图，减少额外 `get_screenshot` 调用。

## 9. Font Policy

必须先识别文本语言和可用字体。

中文优先：

1. `Noto Sans SC`
2. `Noto Serif SC`
3. `Noto Sans TC`
4. 用户或组织指定中文字体

英文优先：

1. 模板或品牌指定字体
2. `Inter`
3. `Noto Sans`

禁止：

- 在中文页面上默认使用 `Inter` 作为主字体。

原因：

- 已实测 `Inter` 在 Figma 截图中会导致中文不可见或缺字。

## 10. Export and Integration Modes

### Mode A: Whole Page

Figma 输出整页 PNG/PDF，回填为页面背景或整页视觉。

适用：

- 海报、视觉展示页、复杂总览图。
- 对 PowerPoint 内文本可编辑性要求不高。

风险：

- PPT 内文本不可编辑。
- 需要保留 Figma 源文件作为可编辑版本。

### Mode B: Partial Asset

Figma 只输出局部图，例如流程图、算法图、结果图，再回填到 PPT/HTML/论文。

适用：

- PPT 模板标题、页脚、核心论点仍需保持可编辑。
- 复杂图形用 Figma 做，正文框架由 PPT/HTML/LaTeX 保持。

推荐作为默认模式。

### Mode C: Layout Blueprint

Figma 不直接输出最终素材，只输出 frame、截图和布局参数，供本地脚本复刻。

适用：

- Figma MCP 导出限流。
- 需要代码化可复现图形。
- 需要避免外部服务成为硬依赖。

## 11. Validation Gates

最低验收：

- Figma frame 创建或更新成功。
- frame 比例与目标一致。
- 关键文字可正常显示。
- 截图回读或等价本地渲染成功。
- 输出 manifest。
- 明确说明回填方式和剩余风险。

高级验收：

- 前后对比图生成。
- 下游目标文件回填成功。
- 下游渲染检查通过。
- 无明显文字裁切、重叠和不可读小字。
- 字体、颜色、留白与模板一致。

## 12. Failure Modes and Fallbacks

### Figma MCP 限流

表现：

- `You've reached the Figma MCP tool call limit...`

处理：

- 停止继续调用 Figma 读取工具。
- 保留已有 frame id。
- 使用已有截图或本地复刻兜底。
- 在 manifest 中标记 `rate_limited`。

### 中文字体不可见

表现：

- 截图中文字空白、缺字或异常。

处理：

- 查询 `figma.listAvailableFontsAsync()`。
- 改用 `Noto Sans SC` 或其他 CJK 字体。
- 重新截图验证。

### 导出成功但回填效果差

表现：

- 回填后页面过小、模糊、被裁切。

处理：

- 调整 frame 尺寸和导出倍率。
- 区分整页和局部素材。
- 保持目标容器等比 fit。

### 文本不可编辑风险

表现：

- 整页 PNG 回填后 PPT 中无法编辑文字。

处理：

- 默认采用局部素材模式。
- 若必须整页导出，在报告中明确说明。

## 13. Ownership Boundaries

允许：

- 精校视觉布局。
- 重排页面结构。
- 重绘信息图。
- 导出局部素材。
- 生成回填脚本或建议。
- 生成视觉验收截图和对比图。

不允许：

- 改写事实结论、实验数字、引用来源或答辩口径。
- 擅自引入未授权外部素材。
- 把限流或导出失败伪装成成功。
- 在未验证字体的情况下批量生成中文设计。
- 未说明风险就把整页 PNG 当作最终可编辑 PPT。

## 14. Handoff

交给 PPT 自动化 agent：

- 导出素材路径。
- 回填页码/区域。
- 推荐插入位置和尺寸。
- 是否保留模板标题、页脚、核心论点。
- 验证截图和剩余风险。

交给素材审计 agent：

- 哪些原素材已被替换。
- 哪些素材仍需重绘或高清化。

交给审计 agent：

- 精校前后对比图。
- 字体、可编辑性、事实一致性风险。

## 15. Prompt Template

```text
Use agent: figma-layout-polish-agent

Runtime configuration:
- input_artifact: <PPTX/PDF/HTML/PNG/storyboard/page_plan>
- target_pages_or_regions: <页码或区域>
- source_manifest: <可选，素材或页面 manifest>
- brand_or_template_reference: <可选，模板或视觉规范>
- figma_plan_key: <Figma plan key>
- figma_file_key: <可选，已有 Figma 文件>
- figma_file_name: <可选，新建文件名>
- target_ratio: <4:3|16:9|A4|same_as_input>
- frame_size: <1600x1200|1920x1080|...>
- font_policy: <字体策略>
- export_mode: <whole_page|partial_asset|layout_blueprint|both>
- integration_target: <需要回填的文件>
- validation_policy: <metadata+screenshot+local_render+comparison>
- mcp_call_budget: <调用预算>
- output_dir: <输出目录>

Task:
使用 Figma 对目标页面或区域进行排版精校优化，输出可回填的视觉资产、frame manifest、截图/对比图和验证结论。不要修改事实内容。
```

