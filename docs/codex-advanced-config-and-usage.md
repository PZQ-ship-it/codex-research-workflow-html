# Codex 高级配置与用法笔记

本文件用于沉淀本项目中反复会用到的 Codex 高级配置、功能解释、工作流技巧和实践建议。

## 当前重点

- 学习并整理 `~/.codex/config.toml` 的高级配置。
- 总结 Codex for VS Code 与 Codex App 的能力差异。
- 固化适合研究、论文阅读、HTML 产物生成、视觉验收的工作流。
- 逐步提炼 skills、MCP、subagents、goals、memories、hooks、permissions 的组合用法。

## 已讨论功能

### Goals

`goals = true` 开启 `/goal` 长目标模式。适合有明确停止条件和验证方式的任务。

示例：

```text
/goal 把这篇 PDF 转成结构化 HTML，直到完成：
1. 主要图表被保留或解释
2. HTML 可独立阅读
3. Playwright 截图无明显排版问题
4. 输出来源和不确定点清单
```

关键点：目标必须可验证。没有测试、截图、清单、指标或人工验收标准的 goal 容易变成模糊愿望。

写好 `/goal` 的四个要素：

1. 要做什么。
2. 做到什么程度。
3. 涉及哪些项目、目录、文件或功能。
4. 如何判断完成。

推荐模板：

```text
/goal 帮我完成【具体任务】，要求【范围、约束和非目标】，最后通过【验证方式】确认完成。
```

适合使用 `/goal`：

- 任务较长，可能需要多轮读文件、改文件、跑命令。
- 有明确完成标准，例如测试通过、构建成功、截图无明显问题、报告生成完毕。
- 需要 Codex 在长上下文中持续围绕同一个目标推进。

不适合使用 `/goal`：

- 只是问一个概念、解释一段代码、翻译一句话。
- 只是改一行配置。
- 目标很虚，例如“优化项目”“让系统更好”。
- 同一个 goal 塞进多个跨度很大的任务。

更适合本项目的 goal 写法：

```text
/goal 把指定 PDF 转成结构化 HTML，要求使用 paper-pdf-to-structured-html 工作流，保留主要图表和关键证据，输出到 docs/ 或 reports/，最后通过 Playwright 截图检查无明显排版问题，并列出不确定点。
```

```text
/goal 完成本项目 Codex 高级配置与用法笔记的一个专题更新，要求先阅读现有 docs/codex-advanced-config-and-usage.md，避免重复，补充可复制示例，最后总结新增内容和仍待验证的版本相关点。
```

可以在目标里写资源边界，例如“优先在 50000 token 内完成”。这类预算表达适合控制长任务成本，但属于版本相关能力：是否显示或严格执行预算，取决于当前 Codex 版本。

### Memories

`memories = true` 开启长期偏好记忆。适合存稳定偏好，例如：

- 研究产物优先输出 standalone HTML。
- 最终交付前尽量做视觉验收。
- 中文说明中保留关键英文术语。

团队规则、项目硬约束、目录约定仍应写进 `AGENTS.md` 或项目文档。

### 文件型知识库 / Vault

文件型知识库是把长期上下文放在一个纯文本目录里，让 Codex 可以跨会话读取项目状态、偏好、资料来源和待办。它和 memories 的区别：

- Memories：适合稳定个人偏好，入口较轻。
- Vault：适合项目化、可审计、可编辑、可 Git 管理的上下文。
- `AGENTS.md`：负责规定 Codex 在这个目录里什么时候更新、更新什么、不该乱写什么。

本项目已建立：

```text
vault/
  AGENTS.md
  README.md
  INDEX.md
  TODO.md
  agent/
  notes/
  people/
  projects/
  sources/
  templates/
```

各目录职责：

- `TODO.md`：待办、后续问题、需要验证的点。
- `agent/`：Codex 偏好、提示词模式、工具和工作流笔记。
- `projects/`：项目状态、里程碑、决策记录。
- `people/`：协作者/利益相关者笔记，避免敏感信息。
- `notes/`：通用可复用笔记。
- `sources/`：资料来源、阅读路径、引用清单。
- `templates/`：可复制模板。

使用规则：

- 不放 `.env`、token、账号、私密数据。
- 版本敏感内容要标注来源或待确认。
- 先写短条目和下一步，再逐步整理。
- 重要主题先在 `vault/INDEX.md` 建入口。
- 正式、完整的对外文档仍放在 `docs/`；vault 更像工作记忆和索引层。

### Unified Exec

`unified_exec = true` 启用新版统一命令执行器，适合：

- 长时间运行的命令。
- 本地 dev server。
- 交互式进程。
- 持续输出的测试或构建。

### MCP

MCP 用于把外部工具接入 Codex。当前配置中已有 Figma MCP 示例：

```toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
http_headers = { "X-Figma-Region" = "us-east-1" }
startup_timeout_sec = 20
tool_timeout_sec = 120
```

后续值得探索：

- 文档检索 MCP，例如 Context7。
- GitHub MCP，用于 issue、PR、repo 操作。
- Notion MCP，用于知识库归档。
- Playwright 或浏览器类 MCP，用于页面验收。

#### 常用 MCP 推荐清单

MCP 的选择原则：

- 先接“高频、低风险、可验证”的工具。
- 优先使用官方或维护活跃的一手 MCP server。
- 对会写入外部系统的 MCP，例如 GitHub、Notion、Linear，默认用最小权限 token。
- 对 browser/computer 类 MCP，明确任务范围，避免让 Codex 接触不相关登录态和私人页面。
- 配置进入 `config.toml` 前，先确认需要的环境变量已在 `.env` 或系统环境变量中配置，不要把 token 写死。

##### 1. OpenAI Docs MCP

用途：查 OpenAI API / Codex / Responses / SDK 官方文档。适合回答版本敏感问题。

适合本项目：

- 核对 Codex 配置字段。
- 查 OpenAI API / SDK 用法。
- 避免第三方文章里的过时说法。

参考：`https://platform.openai.com/docs/docs-mcp`

##### 2. Context7

用途：查常见开源库和框架文档。适合前端、Python、Node、LaTeX/PDF 工具链等技术问题。

示例配置：

```toml
[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
startup_timeout_sec = 20
tool_timeout_sec = 120
```

适合本项目：

- 查 Playwright、pdfplumber、pypdf、reportlab、Vite、React 等库的当前文档。
- 为 skills 或脚本补官方用法。

参考：`https://github.com/upstash/context7`

##### 3. GitHub MCP

用途：操作 GitHub repo、issue、PR、review、actions 等。

适合本项目：

- 生成 issue / PR 描述。
- 根据 review comment 修复问题。
- 检查 CI 失败和 workflow 日志。
- 把长期工作流沉淀到 GitHub 仓库。

注意：

- token 权限要最小化。
- 写入型操作前让 Codex 明确列出将创建/修改什么。
- 对私有仓库避免把敏感 issue 内容写入普通文档。

参考：`https://github.com/github/github-mcp-server`

##### 4. Figma MCP

用途：读取 Figma 设计稿、组件、设计 token 和页面结构。

当前已有配置：

```toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
http_headers = { "X-Figma-Region" = "us-east-1" }
startup_timeout_sec = 20
tool_timeout_sec = 120
```

适合本项目：

- 如果后续把 HTML digest 做成固定视觉系统，可以从 Figma 读取设计规范。
- 对照设计稿做页面还原和视觉审查。

##### 5. Chrome DevTools MCP

用途：连接 Chrome，做页面检查、性能分析、网络请求、DOM/CSS 调试。

适合本项目：

- 检查生成的 HTML artifact。
- 追踪 CSS 布局问题、资源加载失败、控制台错误。
- 结合 Playwright 做视觉验收前后的排障。

参考：`https://github.com/ChromeDevTools/chrome-devtools-mcp`

##### 6. Playwright MCP / Browser MCP

用途：浏览器自动化、截图、点击、表单、E2E 检查。

适合本项目：

- HTML/PDF 视觉验收。
- 检查移动端和桌面端布局。
- 生成截图作为报告证据。

注意：

- 对登录态页面要谨慎，避免把私人页面暴露给任务。
- 不提交不可逆表单，除非用户明确确认。

##### 7. Notion MCP

用途：读写 Notion 知识库、项目文档、会议记录。

适合本项目：

- 把 `vault/` 或 `docs/` 中的结论同步到 Notion。
- 从 Notion 汇总项目状态、资料来源和长期计划。

注意：

- Notion 权限边界要按 workspace/page 限制。
- 同步时要避免重复创建页面。

##### 8. Sentry MCP

用途：读取 Sentry issue、错误事件、release、trace 等。

适合代码项目：

- 排查线上错误。
- 从错误事件生成复现路径和修复计划。
- 验证修复是否影响同类异常。

参考：`https://docs.sentry.io/product/sentry-mcp/`

##### 9. Filesystem / Search 类 MCP

用途：把外部资料库或特定目录作为可检索上下文暴露给 Codex。

适合本项目：

- 连接论文库、资料库、历史报告目录。
- 对大量 Markdown/HTML/JSON 研究资料做检索和综合。

注意：

- 不要把整个用户主目录暴露给 MCP。
- 明确 allowlist 目录，排除 `.env`、账号文件、下载目录中的敏感文件。

##### 10. Database MCP

用途：查询数据库 schema、样例数据、只读分析。

适合代码项目：

- 理解业务表结构。
- 生成迁移计划。
- 排查数据相关 bug。

注意：

- 默认只读账号。
- 禁止直连生产写库。
- 查询结果可能含个人信息，进入文档前要脱敏。

#### 本项目建议优先级

```text
第一批：OpenAI Docs MCP + Context7 + GitHub MCP
第二批：Chrome DevTools / Playwright MCP + Notion MCP
第三批：Figma MCP + Sentry MCP + Filesystem/Search MCP
```

对当前研究工作流，最实用的组合是：

```text
OpenAI Docs MCP：核对 Codex 功能和配置
Context7：查库文档
Playwright/Chrome DevTools：验收 HTML artifact
GitHub：沉淀 issue/PR/版本记录
Notion 或 vault：归档长期知识
```

#### 维护规则

- 每新增一个 MCP，都在 `vault/sources/codex-links.md` 或本文件记录用途、权限、token 环境变量名和风险。
- 对外部写入型 MCP，先写只读用法，再逐步开放写权限。
- 把 MCP 的“安装命令”和“使用场景”分开写，避免为了装而装。
- 如果某个 MCP 三个月没用，可以考虑移出默认配置，保留在文档里作为候选。

### Subagents

Subagents 适合并行分工。典型角色：

- `explorer`：读代码、查路径、回答具体代码库问题。
- `worker`：执行独立实现任务，适合明确文件所有权。
- 自定义 agent：例如论文审查、视觉验收、事实一致性检查。

Subagent 不一定要提前定义。可以在一次任务里直接描述临时职责，让 Codex 根据任务临时派生内置 agent：

```text
请临时开 3 个 subagent：
1. explorer：检查这个仓库里 PDF 转 HTML 的流程入口。
2. explorer：检查现有 Playwright 视觉验收方式。
3. reviewer：只审查 docs/codex-advanced-config-and-usage.md 是否有重复、过时或不准确内容。

主线程继续整理文档，等它们返回后再合并结论。
```

提前定义 custom agent 的价值主要是复用、稳定约束和权限控制。适合反复出现的角色，例如论文事实审查、视觉验收、配置安全审查。一次性任务通常只需要自然语言描述职责。

适合使用的场景：

- 多个独立问题可以并行调查。
- 大任务可以拆成互不重叠的文件范围。
- 一个主流程继续推进，同时旁路 agent 做验证或审查。

不适合使用的场景：

- 下一个动作马上依赖该结果。
- 任务范围模糊，子任务无法自洽。
- 多个 agent 会编辑同一批文件，容易冲突。

#### 自定义 subagent TOML 示例

自定义 agent 可以放在用户级或项目级目录：

```text
~/.codex/agents/paper-reviewer.toml        # 全局可用
<repo>/.codex/agents/paper-reviewer.toml   # 当前项目可用
```

每个 TOML 文件定义一个 agent。必填字段：

- `name`
- `description`
- `developer_instructions`

常用可选字段：

- `model`
- `model_reasoning_effort`
- `sandbox_mode`
- `approval_policy`
- `tools`
- `mcp_servers`
- `skills.config`

示例 1：论文事实与论证审查 agent

```toml
name = "paper-reviewer"
description = "Reviews academic paper digests for unsupported claims, missing evidence, terminology drift, and weak experiment interpretation."
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
你是严格的学术论文审查 subagent。

只做审查和建议，不直接改文件，除非主线程明确要求。
重点检查：
- 论文摘要或 HTML digest 是否遗漏核心贡献、实验设置、数据集、指标和限制。
- 结论是否被证据支持，是否有过度外推。
- 术语、指标、数据集名称是否前后一致。
- 哪些点需要回看原 PDF 或官方来源确认。

输出格式：
1. High-risk findings
2. Medium-risk findings
3. Missing evidence
4. Suggested fixes
"""
```

示例 2：视觉验收 agent

```toml
name = "visual-acceptance-reviewer"
description = "Checks generated HTML/PDF artifacts for layout, readability, clipping, overlap, and mobile/desktop visual issues."
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"

[skills.config]
allowed = ["codex-visual-acceptance", "playwright", "screenshot"]

developer_instructions = """
你负责视觉验收。

优先使用 Playwright 或截图工具检查 HTML/PDF 产物。
重点关注：
- 文本是否溢出、重叠、被遮挡。
- 移动端和桌面端布局是否都可读。
- 主要图表、表格、代码块是否清晰。
- 页面是否出现空白、加载失败或资源丢失。

如果发现问题，返回具体文件、视口尺寸、截图路径和修复建议。
不要做无关 UI 重构。
"""
```

示例 3：Codex 配置安全审查 agent

```toml
name = "codex-config-auditor"
description = "Audits Codex configuration, AGENTS.md, skills, MCP, hooks, and vault notes for safety and maintainability."
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
你负责审查 Codex 配置和工作流文档。

重点检查：
- 是否把 secrets、token、API key 或私密路径写进文档。
- config.toml、AGENTS.md、skills、hooks 示例是否有危险默认值。
- 第三方文章中的说法是否被当成官方事实。
- 是否存在版本敏感但未标注待验证的内容。

输出必须区分：
- confirmed issue
- possible issue
- recommendation
"""
```

示例 4：带 MCP 限制的资料检索 agent

```toml
name = "docs-researcher"
description = "Finds current official documentation and source-backed references for Codex features."
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
mcp_servers = ["context7", "github"]

developer_instructions = """
你负责资料检索，只回答有来源支撑的内容。

优先级：
1. 官方 OpenAI / Codex 文档。
2. 官方 GitHub 仓库。
3. 明确标注为第三方参考的社区文章。

输出时必须列出来源链接，并标明哪些结论是版本敏感的。
不要把第三方 cheat sheet 当成官方事实。
"""
```

调用方式示例：

```text
请用 paper-reviewer subagent 审查 reports/latest-paper-digest.html，只返回高风险问题和证据缺口。
```

```text
请并行启动 visual-acceptance-reviewer 和 codex-config-auditor：
1. 前者检查新生成 HTML 的排版问题。
2. 后者检查 docs/codex-advanced-config-and-usage.md 是否有不安全配置建议。
主线程继续整理修改计划。
```

建议：

- 全局 agent 放通用角色，例如 `docs-researcher`、`codex-config-auditor`。
- 项目级 agent 放强绑定当前仓库的角色，例如研究 HTML 验收、论文 digest 审查。
- 写 `description` 时要说明何时使用，方便 Codex 自动选择。
- 写 `developer_instructions` 时要规定输出格式和非目标，减少 subagent 跑偏。
- 给 worker 类 agent 明确文件所有权，避免多个 agent 同时编辑同一批文件。

#### OMX `$team` 到 native subagents 的迁移

当前建议把 OMX `$team` 的工作纪律迁移到 `$codex-native-subagent-team`，而不是复制 tmux panes、worker mailbox 或 `.omx/state`：

```text
$codex-native-subagent-team "这个任务适合并行。请先拆出主线程 critical path 和 2 个只读 explorer lane，再继续主线程工作。"
```

迁移原则：

- 必须由用户明确要求 subagents、parallel agents、delegation 或 team-style split，才启动 native subagents。
- 主线程先保留 critical path；只把不阻塞下一步的旁路调查、验证或 disjoint edit 交给 subagent。
- 每个 subagent 都要有明确 scope、文件所有权、输出格式和非目标。
- 不把 `$team` 迁移成自动 fanout；当前 native Codex subagent 是显式协作工具，不是 OMX runtime。
- 不迁移 OMX 的 tmux、Stop-hook continuation、`.omx/state/team`、worker mailbox；这些保留给 WSL2 OMX runtime。

参考：

- Official Codex Subagents: https://developers.openai.com/codex/subagents

### AGENTS.md

`AGENTS.md` 用于给 Codex 提供项目级规则。本项目当前规则：

- 维护本文件作为 Codex 高级配置与用法笔记。
- 默认用中文写文档。
- 优先沉淀可复用的配置片段、命令和工作流。
- 不把 `.env`、token、私密配置写进文档。

官方和社区共同认可的参考：

- OpenAI Codex AGENTS.md guide: https://developers.openai.com/codex/guides/agents-md
- AGENTS.md open format: https://agents.md/

全局 AGENTS.md 建议放在 `~/.codex/AGENTS.md`。它应该只写跨所有项目都成立的个人偏好和安全规则；项目规则放项目根目录 `AGENTS.md`；目录局部规则再放子目录里的 `AGENTS.md` 或 override 文件。

全局文件适合包含：

- 交流语言、回答风格、文档偏好。
- 安全底线：不泄露 secrets，不主动改 `.env`，不做破坏性 git 操作。
- 默认工程习惯：先读代码、优先现有模式、修改后验证。
- 工具偏好：搜索用 `rg`，视觉检查用 Playwright，PDF 任务使用相关 skill。
- 记忆/vault 规则：哪些结论应写入长期知识库。

全局文件不适合包含：

- 某个项目的技术栈、目录、测试命令。
- 过长的 prompt 大全。
- 会和项目 `AGENTS.md` 冲突的强约束。
- token、账号、私密路径、公司敏感规则。

推荐全局模板：

```md
# Global AGENTS.md

## Language

- 默认用中文沟通；代码、命令、API 名称保留英文。
- 回答保持简洁，优先给可执行结论和必要背景。

## Working Style

- 先快速阅读相关文件和现有约定，再修改。
- 优先沿用项目已有框架、目录结构、命名和测试方式。
- 不做无关重构；若发现旁路问题，先记录或说明。
- 修改后尽量运行最小验证；无法验证时明确说明原因。

## Safety

- 不读取、输出、复制或记录 secrets、API key、token、密码。
- 不主动修改 `.env`、凭据文件或私密配置，除非用户明确要求。
- 不使用破坏性 git 命令，例如 `git reset --hard`、强制覆盖、删除未确认文件。
- 写入长期笔记时避免敏感个人信息。

## Tools

- 搜索文件优先使用 `rg` / `rg --files`。
- Web/文档信息若可能过期，优先查官方来源。
- UI/HTML/PDF 视觉问题优先使用截图或 Playwright 验证。
- PDF 论文处理优先考虑相关 PDF/HTML skill。

## Long-Term Notes

- 可复用的 Codex 配置、工作流、prompt 模板和待验证点，可以写入项目 vault。
- 版本敏感结论必须标注来源或待验证。
```

### Codex for VS Code 与 Codex App

Codex for VS Code 更适合：

- 侧边栏聊天。
- 读写代码。
- 查看 diff。
- 运行命令。
- 配合本地浏览器或 Playwright 预览页面。

Codex App 的 sidebar/artifacts 体验更完整，适合：

- 预览产物。
- 对页面或文档做更直接的视觉反馈。
- 使用 App 内置 browser、voice dictation、artifacts 等体验。

VS Code 中语音输入目前更现实的方案是系统听写，例如 Windows 的 `Win + H`。

### Automations

Automations 是 Codex App 里的定时后台任务能力。官方文档当前把 Automations 放在 Codex App 使用文档下，而不是 IDE Extension 或 CLI 的原生命令中。

要点：

- 在 Codex App sidebar 的 automations pane 里管理 automation 和运行结果。
- 可以在普通 Codex thread 中描述任务、频率、是否绑定当前 thread，让 Codex 帮你创建或更新 automation。
- project-scoped automation 需要 Codex App 正在运行，并且所选项目在本机磁盘上可用。
- Git 仓库里可以选择在当前 local project 里运行，或在单独 worktree 中运行；worktree 更适合隔离后台修改。
- Automations 可以使用同一套 plugins 和 skills，也可以在 prompt 里用 `$skill-name` 显式触发 skill。
- Automations 默认使用你的 sandbox 设置；后台无人值守时不要轻易用 full access。

类型区分：

- Standalone / project automation：每次按计划从新的 prompt 开始，结果进入 Triage，适合日报、周期检查、跨项目检查。
- Thread automation：绑定当前 thread，像心跳一样定期唤醒同一会话，适合长任务跟进、轮询 GitHub/Slack、持续 review loop。

当前判断：

```text
Codex App：有原生 Automations。
Codex for VS Code：没有看到同等原生创建/管理入口。
Codex CLI：没有 App Automations，但可以用 codex exec + cron / Windows Task Scheduler / GitHub Actions 自己搭定时自动化。
```

替代方案示例：

```powershell
codex exec "检查 docs/codex-advanced-config-and-usage.md 是否有待补充项，并输出今日建议"
```

可以把上面的命令交给 Windows Task Scheduler 定时执行，但它不会自动拥有 Codex App 的 Triage、thread automation、worktree 管理等产品级体验。

### Permissions Profiles

Permissions profiles 是 Codex 的 beta 权限配置方式，用来把本地命令执行的文件系统权限和网络权限打包成一个可复用 profile。它适合替代旧的 `sandbox_mode` + `sandbox_workspace_write` 组合。

关键规则：

- 内置 profile 有 `:read-only`、`:workspace`、`:danger-full-access`。
- 自定义 profile 写在 `[permissions.<name>]` 下。
- 顶层 `default_permissions = "<profile-name>"` 选择默认 profile。
- 不要把新 permissions profile 和旧 `sandbox_mode` / `sandbox_workspace_write` 混用；如果旧 sandbox 设置处于 active config layer，Codex 会优先使用旧 sandbox。
- Permission profiles 只约束本地 sandboxed command execution；MCP、browser、computer use、Codex cloud、人工批准后的提权路径还有各自的控制面。
- 网络规则允许的是“能连接哪里”，不代表目标本身可信。
- 在 native Windows 上，官方建议 elevated sandboxing 最强；如果需要 Linux sandbox 模型，用 WSL。

#### 内置 profile 快速用法

只读：

```toml
default_permissions = ":read-only"
```

允许写当前 workspace：

```toml
default_permissions = ":workspace"
```

取消本地 sandbox 限制：

```toml
default_permissions = ":danger-full-access"
```

`:danger-full-access` 只适合非常明确且可信的任务，不适合作为默认。

#### 示例 1：只读 + 官方文档网络 allowlist

适合查文档、审查配置、读项目但不改文件。

```toml
default_permissions = "readonly-docs"

[permissions.readonly-docs.filesystem]
":minimal" = "read"

[permissions.readonly-docs.filesystem.":workspace_roots"]
"." = "read"
"**/*.env" = "deny"

[permissions.readonly-docs.network]
enabled = true

[permissions.readonly-docs.network.domains]
"developers.openai.com" = "allow"
"github.com" = "allow"
"raw.githubusercontent.com" = "allow"
"api.github.com" = "allow"
```

#### 示例 2：工作区可写 + 禁止联网

适合纯本地代码修改、文档整理、格式化。

```toml
default_permissions = "project-edit"

[permissions.project-edit.filesystem]
":minimal" = "read"

[permissions.project-edit.filesystem.":workspace_roots"]
"." = "write"
"**/*.env" = "deny"
"tmp" = "write"
"output" = "write"

[permissions.project-edit.network]
enabled = false
```

#### 示例 3：工作区可写 + 公共网络访问

适合需要联网查资料、下载公开依赖、跑浏览器验收的任务。`"*"` 很宽，只有确认需要公共网络时再用。

```toml
default_permissions = "workspace-net"

[permissions.workspace-net.filesystem]
":minimal" = "read"

[permissions.workspace-net.filesystem.":workspace_roots"]
"." = "write"
"**/*.env" = "deny"

[permissions.workspace-net.network]
enabled = true

[permissions.workspace-net.network.domains]
"*" = "allow"
```

#### 示例 4：本地 dev server / Playwright 验收

适合前端页面、HTML artifact、本地服务截图检查。Codex 默认会防止访问本地/私有网络，访问 `localhost` 需要显式 allowlist。

```toml
default_permissions = "local-preview"

[permissions.local-preview.filesystem]
":minimal" = "read"

[permissions.local-preview.filesystem.":workspace_roots"]
"." = "write"
"**/*.env" = "deny"

[permissions.local-preview.network]
enabled = true

[permissions.local-preview.network.domains]
"localhost" = "allow"
"127.0.0.1" = "allow"
"developers.openai.com" = "allow"
"github.com" = "allow"
"raw.githubusercontent.com" = "allow"
```

如果必须访问解析到本地或私网地址的主机名，再考虑：

```toml
[permissions.local-preview.network]
enabled = true
allow_local_binding = true
```

不要为普通任务开启 `dangerously_*` 网络选项。

#### 示例 5：当前研究工作流建议 profile

适合本项目这类 PDF/HTML/文档工作流：允许写当前 workspace，拒绝 `.env`，允许访问官方文档、GitHub、AnySearch 和 OpenAI API。

```toml
default_permissions = "research-workflow"

[permissions.research-workflow.filesystem]
":minimal" = "read"
glob_scan_max_depth = 3

[permissions.research-workflow.filesystem.":workspace_roots"]
"." = "write"
"**/*.env" = "deny"
"tmp" = "write"
"output" = "write"
"reports" = "write"
"docs" = "write"
"vault" = "write"

[permissions.research-workflow.network]
enabled = true

[permissions.research-workflow.network.domains]
"developers.openai.com" = "allow"
"github.com" = "allow"
"raw.githubusercontent.com" = "allow"
"api.github.com" = "allow"
"api.anysearch.com" = "allow"
"api.openai.com" = "allow"
"localhost" = "allow"
"127.0.0.1" = "allow"
```

临时切换 profile：

```powershell
codex -c 'default_permissions="readonly-docs"'
codex -c 'default_permissions="workspace-net"'
```

如果要长期使用，把 `default_permissions` 和对应 `[permissions.<name>]` 写进 `~/.codex/config.toml`；如果只对当前仓库生效，写进项目级 `.codex/config.toml`。

参考：

- Official Codex Permissions: https://developers.openai.com/codex/permissions

### oh-my-codex / OMX in WSL2

`oh-my-codex` 是 OpenAI Codex CLI 的 workflow layer。官方 README 当前把 macOS/Linux + Codex CLI 作为推荐默认路径；原生 Windows 不是默认体验，Windows 上更适合放到 WSL2 里单独跑完整 OMX runtime。

本机配置要点：

- Windows 功能需要启用 `Microsoft-Windows-Subsystem-Linux` 和 `VirtualMachinePlatform`。
- BIOS/固件虚拟化要开启；可用 `systeminfo` 查看 Hyper-V requirements。
- 如果刚启用功能后 `LxssManager` 服务不存在，或 Ubuntu 注册报 `0x8007019e`，先重启 Windows，再继续安装。
- Ubuntu/Debian 内建议安装 `tmux`，OMX 的 durable team runtime 会用到它。

官方安装目标：

```bash
npm install -g @openai/codex
npm install -g oh-my-codex
omx setup
```

当前 npm 包要求 Node.js `>=20`。安装后至少做：

```bash
omx doctor
codex login status
omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"
```

本仓库提供了重启后续装脚本：

```powershell
.\tools\setup-oh-my-codex-wsl2.ps1
```

脚本会检查/启用 WSL2 前置项，安装 Ubuntu 24.04、Node.js 20、`tmux`、`@openai/codex` 和 `oh-my-codex`，然后运行 `omx setup` 与 `omx doctor`。如果 Codex 登录态不存在，最后的真实执行 smoke test 需要先在 WSL 中手动 `codex login`。

自动化结束后需要人工完成：

```bash
codex login
codex login status
omx doctor
omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"
```

如果使用自定义 provider、代理、MCP token 或额外环境变量，不要从 Windows 复制凭据文件；在 WSL 内手动写入 `~/.codex/config.toml`、`~/.bashrc` 或其他 WSL-local 配置，并避免把 token 写进仓库脚本或文档。

#### OMX 日常使用速查

OMX 不替代 Codex CLI；它是在 Codex 之上增加 prompts、skills、hooks、HUD、team runtime 和 `.omx/` 状态层。日常使用时不要把它当成一堆 shell 子命令来手动操作一整天，而是先启动一个 OMX 管理的 Codex 会话，然后在会话里用 `$...` workflow keywords。

每次开始本项目工作，先进入项目目录，避免在 `/mnt/c/Windows/system32` 这类宿主系统目录下生成 `.omx/` 状态：

```bash
cd /mnt/d/工作流优化/codex-research-workflow-html
```

健康检查与真实调用 smoke test：

```bash
omx doctor
codex login status
omx exec --skip-git-repo-check -C . "Reply with exactly OMX-EXEC-OK"
```

`omx doctor` 只能证明 OMX 文件、hooks、skills 和本地 runtime wiring 看起来正常；`omx exec` 才能证明当前 shell/profile 下的 Codex auth、provider、base URL 和模型请求真的可用。

启动交互式会话：

```bash
omx --high
```

官方 README 的强启动示例是：

```bash
omx --madmax --high
```

但 `--madmax` 会绕过 Codex approvals 和 sandbox，只适合你明确信任的本地仓库与命令环境。第一次排障或处理陌生仓库时，优先用不带 `--madmax` 的启动方式。

进入 OMX/Codex 会话后，常用 workflow keywords 是直接发给 Codex 的消息，不是在 shell 里执行：

```text
$deep-interview "澄清这个需求的范围、边界和非目标"
$ralplan "基于澄清结果形成可执行计划并审查取舍"
$ultragoal "把已批准计划转成可持续执行和检查点"
```

推荐顺序：

1. 需求不清楚：先用 `$deep-interview`。
2. 需要方案、风险、取舍：用 `$ralplan`。
3. 已经批准计划，要长期推进到完成：用 `$ultragoal`。
4. 某个 Ultragoal story 真的适合并行拆分时，再用 `$team`。
5. 只需要一个持续推进的单负责人闭环时，用 `$ralph`。

常用运维命令：

```bash
omx status
omx cancel
omx update
omx doctor --team
omx team status <team-name>
omx team shutdown <team-name>
```

如果 `omx exec` 出现 `401 Unauthorized`，优先检查当前 shell 中 Codex 实际使用的 `~/.codex/config.toml`、`CODEX_HOME`、provider/base URL 和 API key 是否匹配。使用 OpenAI-compatible proxy 时，必须确保自定义 base URL 在当前 WSL 配置中真的生效；否则 proxy key 会被发到默认 OpenAI endpoint 并报 invalid key。

#### 同步 Windows 全局 Codex 配置到 WSL

不要把 `C:\Users\Administrator\.codex` 整个覆盖到 WSL。Windows 全局目录里通常包含 `auth.json`、`.sandbox-secrets`、session/log/sqlite 数据库、运行时状态和 Windows-only 路径；这些不应复制到 Linux `~/.codex`，也可能覆盖 `omx setup` 刚写入的 WSL hooks、skills、agents 和 config。

本仓库提供安全同步脚本：

```powershell
.\tools\sync-codex-global-to-wsl.ps1
```

同步策略：

- 先备份 WSL `~/.codex` 到 `~/.codex/backups/windows-global-sync-<timestamp>`。
- 排除 `auth.json`、`.env`、`.sandbox-secrets`、sqlite、logs、sessions、runtime 等凭据和运行态。
- `config.toml` 不覆盖 WSL 生效配置，只在安全检查通过时复制为 `config.windows-global.reference.toml` 供人工参考。
- `skills`、`rules`、`memories` 采用不覆盖已有文件的合并式复制。
- `plugins` 默认不复制；如只想保留 Windows 插件作参考，可加 `-IncludePluginReference`，目标目录是 `plugins-windows-reference`。
- `AGENTS.md` 不是机械覆盖，而是在 WSL `AGENTS.md` 前插入 `WINDOWS-GLOBAL-AGENTS-SYNC` 区块，并声明环境适用性。

AGENTS 合并原则：

- 语言、工作风格、安全边界、文档习惯等通用偏好可以继承。
- Windows 路径、PowerShell 命令、VS Code UI、桌面/browser automation 等只作为宿主侧参考，不能自动当成 WSL 命令。
- WSL 内优先使用 Linux 路径和工具，例如 `~/.codex`、`/mnt/d/...`、`bash`、`apt`、`tmux`。
- 与 OMX 生成的 WSL config/hooks/skills/AGENTS 区块冲突时，OMX-managed 内容优先。

同步结束后需要人工复核：

```bash
sed -n '1,120p' ~/.codex/AGENTS.md
less ~/.codex/config.windows-global.reference.toml
vi ~/.codex/config.toml
omx doctor
```

只把 `config.windows-global.reference.toml` 中确实适合 Linux/WSL 的设置手动迁移进生效的 `~/.codex/config.toml`。Windows-only path、PowerShell 命令和桌面环境配置不要直接照搬。

### Hooks

Hooks 用于在 Codex 生命周期中运行确定性脚本，例如检查用户 prompt 是否误贴了密钥、拦截危险 shell 命令、在任务结束前提醒补充验证。官方文档当前说明：hooks 默认启用；如果要关闭，可在 `config.toml` 中设置：

```toml
[features]
hooks = false
```

常见位置：

```text
~/.codex/hooks.json          # 用户级 hooks
~/.codex/config.toml         # 用户级 inline [hooks]
<repo>/.codex/hooks.json     # 项目级 hooks
<repo>/.codex/config.toml    # 项目级 inline [hooks]
```

注意：

- 项目级 hooks 只有在项目 `.codex/` 配置层被信任时才会加载。
- 新增或修改过的非托管 command hook 需要在 Codex CLI 里用 `/hooks` 审查并信任。
- 多个来源的 hooks 会一起运行，不是高优先级覆盖低优先级。
- 同一事件下多个匹配 command hook 会并发启动。
- `PreToolUse` / `PostToolUse` 是 guardrail，不是完整安全边界；当前对新式 `unified_exec`、WebSearch 等路径的拦截并不完整。
- 本机旧版 CLI 若没有 `/hooks` 或 `features list` 中看不到 `hooks`，先升级 Codex CLI / App。

#### 项目级 hooks.json 示例

不要直接复制后立刻启用；先创建脚本、确认路径，再用 `/hooks` 信任。

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/check_prompt_secrets.py\"",
            "commandWindows": "py -3 .codex/hooks/check_prompt_secrets.py",
            "timeout": 5,
            "status_message": "Checking prompt for secrets"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/block_dangerous_shell.py\"",
            "commandWindows": "py -3 .codex/hooks/block_dangerous_shell.py",
            "timeout": 5,
            "status_message": "Checking shell command"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/stop_validation_reminder.py\"",
            "commandWindows": "py -3 .codex/hooks/stop_validation_reminder.py",
            "timeout": 10,
            "status_message": "Checking final validation note"
          }
        ]
      }
    ]
  }
}
```

Windows 简化示例里的 `commandWindows` 假设 Codex 从仓库根目录启动。若经常从子目录启动，建议把脚本路径改成绝对路径，或用 PowerShell 先解析 git root。

#### 示例 1：阻止 prompt 里误贴密钥

文件：`.codex/hooks/check_prompt_secrets.py`

```python
import json
import re
import sys

data = json.load(sys.stdin)
prompt = data.get("prompt", "")

patterns = [
    r"sk-[A-Za-z0-9_-]{20,}",
    r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?[^\\s'\"]{12,}",
]

if any(re.search(pattern, prompt) for pattern in patterns):
    print(json.dumps({
        "decision": "block",
        "reason": "疑似包含 API key、token、password 或 secret。请先移除敏感信息后再发送。"
    }, ensure_ascii=False))
```

`UserPromptSubmit` 可以通过 `decision: "block"` 阻止本次 prompt 继续提交。

#### 示例 2：拦截危险 shell 命令

文件：`.codex/hooks/block_dangerous_shell.py`

```python
import json
import re
import sys

data = json.load(sys.stdin)
tool_input = data.get("tool_input") or {}
command = tool_input.get("command", "")

dangerous_patterns = [
    r"\brm\s+-rf\s+/",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-fdx\b",
    r"Remove-Item\b.*\s-Recurse\b.*\s-Force\b",
]

if any(re.search(pattern, command, re.IGNORECASE) for pattern in dangerous_patterns):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "危险命令已被 hook 拦截。需要执行时请让用户明确确认。"
        }
    }, ensure_ascii=False))
```

`PreToolUse` 阻止的是已支持的工具路径。不要把它当成唯一安全机制；仍然要依赖 sandbox、permissions、人工审批和项目规则。

#### 示例 3：结束前提醒补充验证说明

文件：`.codex/hooks/stop_validation_reminder.py`

```python
import json
import sys

data = json.load(sys.stdin)
message = data.get("last_assistant_message") or ""

keywords = ["验证", "测试", "截图", "未能运行", "无法运行"]

if message and not any(keyword in message for keyword in keywords):
    print(json.dumps({
        "systemMessage": "结束前请确认是否需要补充验证结果，例如测试、构建、截图或无法验证的原因。"
    }, ensure_ascii=False))
```

如果想让 Codex 自动继续一轮，可以让 `Stop` 返回：

```json
{
  "decision": "block",
  "reason": "请补充本次改动的验证结果；如果无法验证，请说明原因。"
}
```

`Stop` 中的 `decision: "block"` 不是否决当前任务，而是让 Codex 用 `reason` 自动继续下一轮。

#### Inline TOML 示例

也可以不写 `hooks.json`，直接放在 `config.toml`：

```toml
[[hooks.PreToolUse]]
matcher = "^Bash$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = 'python3 "$(git rev-parse --show-toplevel)/.codex/hooks/block_dangerous_shell.py"'
command_windows = "py -3 .codex/hooks/block_dangerous_shell.py"
timeout = 5
status_message = "Checking shell command"
```

建议：同一配置层里优先二选一，使用 `hooks.json` 或 inline `[hooks]`，不要两个都写，避免启动时合并警告。

参考：

- Official Codex Hooks: https://developers.openai.com/codex/hooks

### 外部参考：codex-cheat-sheet

参考仓库：`BA-CalderonMorales/codex-cheat-sheet`。该仓库采用从 Level 1 到 Level 5 的学习路径组织 Codex CLI 用法，适合作为查漏补缺清单。

值得学习的结构：

- 用分层方式学习：入门命令、基础 slash commands、中级配置、高级功能、专家工作流。
- 把命令速查和实践场景分开：先知道有什么，再知道什么时候用。
- 用 `<details>` 折叠长内容，适合做“可扫读”的 cheat sheet。
- 每个高级能力都给最小可复制示例，例如 MCP、sandbox、`codex exec`、skills。
- 仓库内的 `AGENTS.md` 很简洁，明确 purpose、style、include/avoid 和贡献规则，可借鉴到自己的文档型仓库。

值得迁移到本项目笔记的主题：

- Slash commands 速查：`/model`、`/permissions`、`/review`、`/init`、`/compact`、`/diff`、`/status`、`/mcp`、`/goal` 等。
- CLI 会话管理：`codex resume`、`codex resume --last`、`codex exec resume --last`。
- 多目录上下文：`codex --add-dir ../backend --add-dir ../shared`，适合跨仓库分析。
- 非交互自动化：`codex exec`、`codex exec --json`、`codex exec --output-schema schema.json`、`-o output.txt`。
- 管道工作流：`git diff | codex exec "create a commit message"`、`cat logs.txt | codex exec "find the error"`。
- MCP 管理命令：`codex mcp list/add/get/remove/login/logout`。
- 权限和沙箱：`sandbox_mode`、`approval_policy`、`sandbox_workspace_write`。
- Skills 的最小结构：YAML frontmatter + `SKILL.md` 正文，示例 skill 可以非常短，但 description 要清楚触发条件。
- 项目管理用法：把 Codex 用于任务拆解、PR 描述、release notes、风险识别、onboarding 文档。

对本项目特别有用的模式：

```text
git diff | codex exec "请生成中文变更摘要，包含变更动机、主要文件、验证情况和风险"
```

```text
codex exec --json "扫描 docs/ 和 skills/，列出 Codex 工作流文档中重复、过时或缺少示例的条目"
```

```text
codex --add-dir ../other-research-repo "对比两个研究工作流仓库的 skills 和 docs 结构，给出可合并项"
```

该仓库也有一些需要谨慎的地方：

- 模型名、slash command 清单、experimental features 会快速变化，应以官方文档和本机 `/status`、`/help`、`/mcp` 输出为准。
- 示例里的 `danger-full-access`、`--full-auto` 只适合可信工作区和明确任务，不应作为默认推荐。
- `js_repl` 示例只是演示思路，不等价于一个安全、完整的 MCP server。
- 第三方 cheat sheet 可以做学习索引，但配置片段进本项目文档前要二次核对。

### Skills 清单与选用

本机当前有两类 skills：

- 全局 skills：`C:\Users\Administrator\.codex\skills\`
- 项目内 skills：`skills/`

项目内 skills 是当前研究工作流的可移植子集；全局 skills 更完整，包含系统创建/安装工具、OpenAI 文档、Notion、截图、Playwright 等。调用时通常用 `$skill-name`，或让 Codex 根据 `description` 自动触发。

选用原则：

- 先按任务类型选 skill，不要为了“用 skill”而用 skill。
- PDF/论文/HTML 产物优先走研究类 skills。
- 视觉、浏览器、截图类任务优先走 Playwright/visual acceptance。
- 大任务先用 interview/plan/goal 类 skill 收束目标，再进入 implementation。
- 需要联网查资料时优先用 `openai-docs` 或 `anysearch`，并标注来源。

#### 研究、论文、PDF、LaTeX

| Skill | 选用场景 |
|---|---|
| `paper-pdf-to-structured-html` | 把论文 PDF、arXiv、会议论文、survey 转成可独立阅读的结构化 HTML digest。 |
| `academic-paper-reviewer` | 严格审查论文、毕业论文、proposal、manuscript，输出优先级问题、证据缺口和答辩风险。 |
| `pdf` | PDF 读取、生成、渲染、布局检查，尤其是需要 Poppler、pdfplumber、pypdf、reportlab 时。 |
| `latex-pdf-final-review` | LaTeX 论文/毕业论文提交前最终检查：编译、引用、术语、图表、PDF 页面和 layout warnings。 |
| `research-fact-source-sync` | 根据代码、数据、benchmark、manifest 更新论文事实，避免实验结果和论文文字脱节。 |
| `thesis-figure-pipeline` | 从实验表生成论文/毕业论文图，处理 CJK 字体、标签映射、PNG/PDF 输出和 LaTeX 同步。 |

#### 资料检索与证据综合

| Skill | 选用场景 |
|---|---|
| `openai-docs` | 查 OpenAI / Codex / API 官方文档，特别是模型、Responses、SDK、配置字段等版本敏感问题。 |
| `anysearch` | 实时搜索、网页内容提取、批量搜索、垂直领域搜索；适合读取 URL、查资料和交叉验证。 |
| `evidence-synthesis-docs` | 把大量 JSON、CSV、Markdown、评论、网页抓取、OCR、访谈材料综合成报告、矩阵、taxonomy、证据表。 |
| `notion-research-documentation` | 从 Notion 多页面研究并综合成结构化文档。 |
| `notion-knowledge-capture` | 把对话、决策、FAQ、how-to 归档成 Notion 页面。 |
| `notion-meeting-intelligence` | 基于 Notion 背景准备会议 agenda、pre-read、参会人相关材料。 |
| `xhs-explore` | 小红书搜索、笔记详情、首页浏览、用户主页分析。 |

#### Codex 工作流、规划、审查

| Skill | 选用场景 |
|---|---|
| `define-goal` | 把模糊意图转成可验证 goal，适合创建 `/goal` 前定义成功标准。 |
| `codex-deep-interview` | 需求模糊、实现路径分叉、约束不清时，先澄清意图、非目标和验收标准。 |
| `codex-consensus-plan` | 需要先拿到决策完备计划，再开始改代码/论文/实验/文档。 |
| `codex-completion-loop` | 用户明确希望一路做到实现、验证、交付证据，不停在半成品。 |
| `codex-adversarial-qa` | 对方案、论文 claim、实验 pipeline、prompt、UI 做敌意场景测试。 |
| `codex-native-subagent-team` | 用户明确要求 subagents/parallel agents/team-style split 时，安全拆分 native Codex 并行任务。 |
| `project-briefing-room` | 面向 stakeholder 做项目状态 briefing，再引出澄清和下一步计划。 |
| `codex-design-brief` | 产品、UI、文档或流程需要轻量设计 brief/决策源。 |

#### 视觉、浏览器、截图、前端验收

| Skill | 选用场景 |
|---|---|
| `codex-visual-acceptance` | UI、HTML note、figure、PDF 页面需要截图/浏览器级视觉验收。 |
| `playwright` | 用真实浏览器导航、点击、截图、抓取 DOM、调试 UI flow。 |
| `screenshot` | 用户明确要求系统/桌面截图，或 Playwright 等工具无法覆盖时。 |
| `html-research-notes` | 生成 standalone HTML 研究/工程/论文工作流笔记，带元数据、内部链接、打印友好样式。 |

#### LLM Benchmark 与实验

| Skill | 选用场景 |
|---|---|
| `resilient-llm-benchmark` | 设计和运行可恢复的大规模 LLM benchmark：checkpoint、append-only、retry、sharding、成本边界。 |

#### Skill / Plugin 管理

| Skill | 选用场景 |
|---|---|
| `skill-creator` | 创建或更新新的 Codex skill，设计 `SKILL.md`、references、assets、scripts。 |
| `skill-installer` | 从 curated list 或 GitHub repo 安装 skills 到 `$CODEX_HOME/skills`。 |
| `plugin-creator` | 创建 Codex plugin 骨架，包含 `.codex-plugin/plugin.json`、skills、hooks、scripts、assets、MCP、marketplace。 |

#### 当前项目优先组合

论文/PDF 到 HTML：

```text
$paper-pdf-to-structured-html
+ $academic-paper-reviewer
+ $codex-visual-acceptance
+ $playwright
```

Codex 高级配置研究：

```text
$openai-docs
+ $anysearch
+ $codex-consensus-plan
+ $codex-adversarial-qa
```

毕业论文/LaTeX 最终检查：

```text
$latex-pdf-final-review
+ $research-fact-source-sync
+ $thesis-figure-pipeline
```

大型实验：

```text
$resilient-llm-benchmark
+ $research-fact-source-sync
+ $evidence-synthesis-docs
```

#### 维护建议

- 全局独有且常用的 skills，可以考虑同步一份到项目 `skills/`，便于迁移。
- 项目 `skills/` 中已存在的研究类 skill，是本仓库工作流的核心，不要随意改名。
- 每次新增 skill 后，在本节补一行“何时选用”，而不是只保存路径。
- 如果 skill 的描述过长，可以在这里写短解释；完整触发条件仍以 `SKILL.md` frontmatter 为准。

### Plugins

Plugin 可以理解为把一套 Codex 工作流打包成可安装/可展示的组合包。它通常把以下内容放在同一个目录里：

- `skills/`：可复用能力说明和操作流程。
- `.mcp.json`：该工作流需要的 MCP server 配置。
- `hooks/` 或 hooks 配置：任务前后自动检查、守门、提醒。
- `scripts/`：工作流脚本。
- `assets/`：图标、截图、模板资源。
- `.codex-plugin/plugin.json`：插件 manifest，描述名称、版本、能力、入口路径和展示信息。

Plugin 和 skill 的调用范式不完全相同：

- Skill 是直接调用的能力单位。常见方式是在对话中写 `$skill-name`，或让 Codex 根据 skill 的 `description` 自动触发。
- Plugin 是能力包/安装包。通常先通过 marketplace 或本地路径安装/启用，然后它里面暴露的 skills、MCP、apps 等组件再被使用。
- 如果 plugin 只包含 skills，最终实际被触发的仍然是其中的某个 skill，而不是“整个 plugin 像 `$skill` 一样执行”。
- Plugin 的 `interface.defaultPrompt` 可以提供起手 prompt，帮助用户从 UI 里启动典型流程，但它不是 skill 的等价替代品。

简单判断：

```text
$paper-pdf-to-structured-html        # 调一个具体 skill
安装 research-html-workflow plugin   # 获得一组 skills/MCP/scripts/assets
```

所以 plugin 更像“装一个工具箱”，skill 更像“拿起工具箱里的某个工具”。

本机可用的 `plugin-creator` skill 可以生成脚手架。默认创建个人插件：

```powershell
python C:/Users/Administrator/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py research-html-workflow --with-skills --with-scripts --with-assets --with-mcp --with-marketplace
```

如果要创建在当前仓库里的团队/项目插件，需要显式指定路径和 marketplace：

```powershell
python C:/Users/Administrator/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py research-html-workflow `
  --path plugins `
  --marketplace-path .agents/plugins/marketplace.json `
  --with-skills --with-scripts --with-assets --with-mcp --with-marketplace
```

典型结构：

```text
plugins/research-html-workflow/
  .codex-plugin/
    plugin.json
  skills/
    paper-digest/
      SKILL.md
  scripts/
  assets/
  .mcp.json
```

`plugin.json` 的核心职责是告诉 Codex 这个插件叫什么、展示成什么、包含哪些组件：

```json
{
  "name": "research-html-workflow",
  "version": "0.1.0",
  "description": "Research PDF to structured HTML workflow for Codex.",
  "author": {
    "name": "Personal"
  },
  "keywords": ["codex", "research", "html", "pdf"],
  "skills": "./skills/",
  "mcpServers": "./.mcp.json",
  "interface": {
    "displayName": "Research HTML Workflow",
    "shortDescription": "Turn research PDFs into reviewed HTML notes.",
    "longDescription": "Reusable Codex workflow for PDF reading, structured HTML generation, source tracking, and visual acceptance.",
    "developerName": "Personal",
    "category": "Productivity",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": [
      "Convert this paper PDF into structured HTML.",
      "Review this HTML digest for missing evidence.",
      "Run a visual acceptance pass on the generated note."
    ]
  }
}
```

注意：实际可接受字段以当前 Codex 插件摄取端为准。脚手架生成后应运行校验：

```powershell
python C:/Users/Administrator/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/research-html-workflow
```

Marketplace 用于让插件出现在 Codex UI 的插件列表中。repo/team marketplace 示例：

```json
{
  "name": "project",
  "interface": {
    "displayName": "Project Plugins"
  },
  "plugins": [
    {
      "name": "research-html-workflow",
      "source": {
        "source": "local",
        "path": "./plugins/research-html-workflow"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

什么时候该做 plugin：

- 一套工作流包含多个 skills、MCP、脚本、模板或资产。
- 想在 Codex UI 中作为一个能力包安装/展示。
- 想把个人 workflow 分享给团队或跨机器复用。
- 单个 skill 已经开始膨胀，依赖外部工具和配置。

什么时候只做 skill：

- 只是一个可复用提示词或操作流程。
- 不需要 MCP、hooks、脚本、资产。
- 只在本机或本项目内部使用。

对本项目的插件化方向：

```text
research-html-workflow plugin
  skills: paper-pdf-to-structured-html, academic-paper-reviewer, codex-visual-acceptance
  scripts: PDF 提取、HTML 校验、截图验收脚本
  mcp: Playwright / docs search / Notion 或 GitHub
  assets: HTML 模板、报告模板、图标
```

## 推荐学习顺序

1. `AGENTS.md`
2. Subagents / custom agents
3. Permissions profiles
4. Hooks
5. MCP 扩展
6. Skills / plugins
7. Fast mode / 模型分层
8. Goals + memories 的规范写法

## 待补充

- VS Code 中的视觉验收工作流。
