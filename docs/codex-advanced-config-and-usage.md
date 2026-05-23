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

- Permissions profile 示例。
- Hooks 配置示例。
- 自定义 subagent TOML 示例。
- 常用 MCP 推荐清单。
- VS Code 中的视觉验收工作流。
