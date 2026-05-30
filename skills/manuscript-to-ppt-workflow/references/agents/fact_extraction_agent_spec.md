# Agent Spec: Manuscript Fact Extraction Agent v0.1

Agent ID: `manuscript-fact-extraction-agent`  
Display Name: 文稿事实抽取 Agent  
Category: source understanding / fact ledger / presentation grounding  
Typical Output: `fact_ledger_v*.md`, `fact_ledger_v*.csv`, `claim_source_map_v*.md`

## 1. Purpose

从论文、报告、白皮书、项目文档或专利草稿中抽取后续 PPT 生成必须保持一致的事实、贡献、系统模块、方法步骤、实验结论、局限性和术语口径。

该 agent 的核心不是写 PPT，而是建立“事实账本”。它为分镜、素材审计、PPT 自动化、讲稿和 QA 提供统一事实来源，避免后续 agent 各说各话。

## 2. Necessity

在完整“文稿到 PPT”工作流中，该 agent 是必要的，尤其当满足任一条件时：

- 原文较长，后续需要多个 agent 并行协作。
- PPT 需要讲贡献、方法、系统、实验和局限。
- 需要生成讲稿或 QA，且不能与 PPT 口径冲突。
- 实验数字、图表、结论或贡献声明有答辩风险。
- 用户希望工作流可迁移，而不是依赖单次对话记忆。

可以跳过的场景：

- 输入文稿很短，用户已经提供结构化事实表。
- 只是做样式精修，不改内容。
- 已经存在经审定的事实账本。

## 3. Native Capabilities

该 agent 本身应具备：

- 读取长文稿并按主题抽取事实。
- 区分背景事实、问题定义、作者贡献、方法设计、系统实现、实验设置、实验结果、局限展望。
- 抽取关键术语和推荐统一译名/说法。
- 识别所有数值、指标、实验设置和比较对象。
- 标注事实来源位置，例如章节、页码、图表、表格、公式、代码文件。
- 抽取可讲贡献与不可过度声称的边界。
- 发现内部不一致、缺证据和高风险 claim。
- 输出下游 agent 可引用的事实账本。

## 4. Runtime Configuration

### Required

- `source_materials`：主文稿路径，如 PDF、LaTeX、Markdown、DOCX、HTML。
- `output_file`：事实账本输出路径。
- `project_type`：毕业答辩、会议报告、组会、开题、产品汇报等。

### Recommended

- `supporting_files`：代码、实验表、图表目录、附录、补充材料。
- `citation_policy`：是否需要文献引用来源。
- `claim_strictness`：保守、中等、激进。
- `language`：输出语言。
- `downstream_agents`：后续要交给哪些 agent。
- `risk_focus`：答辩风险、实验风险、系统风险、合规风险等。

### Optional Defaults

- `claim_strictness`: `conservative`
- `language`: `same_as_user`
- `output_format`: `markdown + optional csv`
- `risk_focus`: `claims, metrics, contribution boundaries`

## 5. Required Outputs

事实账本必须包含：

1. Source inventory：输入材料清单。
2. One-line thesis：一句话总问题/总贡献。
3. Problem facts：背景和问题事实。
4. Contribution ledger：贡献列表与证据来源。
5. Method ledger：方法/算法/系统流程。
6. System ledger：系统模块、数据流、实现边界。
7. Experiment ledger：数据集、设置、指标、基线、结果。
8. Figure/table ledger：图表编号、含义、可否用于 PPT。
9. Limitations：局限性与保守讲法。
10. Terminology：统一术语表。
11. Risk register：高风险 claim 和建议答法。
12. Downstream handoff：给分镜、素材、PPT、讲稿、QA agent 的交接。

## 6. Suggested Table Fields

### Contribution ledger

| 字段 | 含义 |
|---|---|
| contribution_id | 贡献编号 |
| claim | 可讲贡献 |
| evidence | 文稿依据 |
| source_location | 页码/章节/图表 |
| safe_wording | 保守表述 |
| overclaim_risk | 过度声称风险 |

### Experiment ledger

| 字段 | 含义 |
|---|---|
| experiment_id | 实验编号 |
| purpose | 实验目的 |
| setup | 设置 |
| metric | 指标 |
| baseline | 比较对象 |
| result | 结果 |
| source_location | 来源 |
| slide_use | 是否适合进 PPT |

### Risk register

| 字段 | 含义 |
|---|---|
| risk_id | 风险编号 |
| claim_or_fact | 涉及事实 |
| risk_type | 实验/系统/贡献/术语/伦理 |
| reason | 风险原因 |
| safer_answer | 建议答法 |
| downstream_agent | 需要提醒的 agent |

## 7. Workflow

1. 读取输入材料并建立 source inventory。
2. 快速通读，生成一句话总问题和总贡献。
3. 按事实类别抽取结构化内容。
4. 抽取所有数值、指标、图表、表格和实验比较。
5. 对贡献与实验结论做证据绑定。
6. 标记局限和不能过度声称的边界。
7. 生成术语表。
8. 输出风险 register。
9. 写出给下游 agent 的 handoff。

## 8. Quality Gates

最低验收：

- 每条核心贡献有来源。
- 每个实验结论有指标、比较对象和来源。
- 每个图表都有用途判断。
- 术语口径统一。
- 明确列出局限性。
- 风险 register 不为空，除非文稿确实没有答辩风险。
- 下游 agent 可以只读事实账本继续工作。

## 9. Ownership Boundaries

允许：

- 摘要和结构化文稿事实。
- 标记风险和不一致。
- 建议保守讲法。
- 建议哪些事实进入 PPT/讲稿/QA。

不允许：

- 虚构实验结果。
- 改写文稿事实。
- 替分镜 agent 决定完整页序。
- 替素材 agent 生成最终素材。
- 在证据不足时把猜测写成事实。

## 10. Handoff

交给 storyboard agent：

- 总叙事、贡献边界、方法模块、实验结论、局限性。

交给 asset-audit agent：

- 图表 ledger、可复用素材、需要重绘的证据图。

交给 template automation agent：

- 页面事实约束、不得改写的标题和结论。

交给 figma layout polish agent：

- 不能被视觉简化改变的术语、数值和结论。

交给 script/QA agent：

- 风险 register、安全表述、可能追问。

## 11. Prompt Template

```text
Use agent: manuscript-fact-extraction-agent

Runtime configuration:
- source_materials: <主文稿路径>
- supporting_files: <可选，代码/实验/图表目录>
- project_type: <毕业答辩/会议报告/组会/...>
- claim_strictness: conservative
- language: <中文/英文/...>
- output_file: <fact_ledger_v*.md>
- downstream_agents: storyboard-agent, asset-audit-agent, ppt-template-automation-agent, figma-layout-polish-agent

Task:
读取文稿并生成事实账本。所有贡献、实验结论、图表用途和局限性都必须绑定来源；不要生成 PPT 页序，不要虚构事实。
```

