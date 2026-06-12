# Codex Workflows

## Purpose

这里保存偏工作笔记性质的 Codex 用法；正式整理后的内容再同步到 `../../docs/codex-advanced-config-and-usage.md`。

## Reusable Patterns

### Goal Template

```text
/goal 帮我完成【具体任务】，要求【范围、约束和非目标】，最后通过【验证方式】确认完成。
```

### Research HTML Workflow

```text
请使用 paper-pdf-to-structured-html 工作流处理指定 PDF，输出 standalone HTML，保留主要图表和证据，并用 Playwright 截图检查排版。
```

### Documentation Update Rule

```text
先阅读现有文档，避免重复；新增内容要包含可复制示例、版本相关提醒和待验证点。
```

### Scenario Agent Run Optimization

```text
请使用 scenario-agent-run-optimizer 分析【trace/log/eval 路径】，对照【system prompt/tool schema/成功标准】，输出运行健康、root cause、优化计划和验证方案。
```

全局 advisory hook：`C:\Users\Administrator\.codex\skills\scenario-agent-run-optimizer\scripts\scenario_agent_run_optimizer_hook.ps1`。它只在用户提示明显涉及 Agent 运行日志、traces、eval、失败诊断或优化时追加上下文提醒，不自动改文件。

### Codex Council

```text
Use Codex Council to review this architecture decision.
Focus on blockers, rollback, and verification.
```

本仓库已同步 `plugins/codex-council/`，来源和验证命令见 `../../plugins/THIRD_PARTY_PLUGINS.md` 与 `../../docs/codex-advanced-config-and-usage.md`。

## Open Questions

- 哪些 Codex App 功能可以在 VS Code 中近似复刻？
- 哪些 MCP 对研究工作流最有收益？
- 是否需要为本项目创建 custom subagents？
