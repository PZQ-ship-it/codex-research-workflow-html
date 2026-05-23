# Project: codex-research-workflow-html

## Current Focus

维护 Codex 研究工作流相关资料，重点包括：

- Codex 高级配置与用法。
- 论文/PDF 到结构化 HTML 的工作流。
- Skills、MCP、subagents、goals、memories、hooks、permissions 的实践。

## Important Files

- `AGENTS.md`：项目级 Codex 规则。
- `docs/codex-advanced-config-and-usage.md`：Codex 高级配置与用法主文档。
- `skills/paper-pdf-to-structured-html/SKILL.md`：PDF 论文转 HTML skill。
- `vault/`：长期上下文知识库。

## Decisions

- 先用 Markdown 维护 Codex 高级配置笔记，后续需要时再转 standalone HTML。
- Vault 只保存长期上下文、索引和轻量笔记，不放大文件和临时产物。
- 版本敏感的 Codex 功能必须标注来源或待验证。
