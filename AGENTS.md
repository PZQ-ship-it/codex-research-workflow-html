# AGENTS.md

## Project Role

This repository maintains research-workflow materials for Codex, with a current focus on collecting, refining, and reusing advanced Codex configuration, usage patterns, and workflow tips.

## Primary Maintained Document

- Maintain the project-local knowledge note at `docs/codex-advanced-config-and-usage.md`.
- Use this document to summarize advanced Codex features, configuration snippets, usage patterns, examples, caveats, and recommended learning order.
- Keep it practical: prefer copyable configuration, concrete workflows, and short explanations over broad marketing-style descriptions.

## Scope For Now

For this project, prioritize documenting Codex-related knowledge only:

- `config.toml` feature flags and profiles.
- `AGENTS.md` conventions.
- Skills and plugins.
- MCP servers and tool integrations.
- Goals, memories, automations, hooks, permissions, and subagents.
- VS Code usage patterns and limitations.
- Verification workflows such as Playwright screenshots, artifact checks, and review loops.

Avoid expanding this file into general project management rules until the user asks for that.

## Documentation Style

- Write notes in Chinese by default, preserving English feature names where useful.
- Prefer concise sections with examples.
- Include file paths, commands, and TOML snippets when they make the note easier to reuse.
- Mark uncertain or version-sensitive behavior clearly, and verify current official docs when freshness matters.
- Keep recommendations separated from confirmed behavior.

## Working Rules

- Before editing the maintained document, skim existing content and append or reorganize without duplicating sections.
- If a new Codex feature is discussed in the chat, add a compact entry to the maintained document when it seems reusable.
- When changing configuration examples, avoid exposing secrets from `.env` or local private tokens.
- Do not rewrite unrelated HTML reports, templates, skills, or papers unless explicitly requested.

## Verification

- For documentation-only edits, a read-through is usually enough.
- For workflow instructions involving commands, tools, hooks, MCP, or browser verification, include a minimal smoke-test or sanity-check command when practical.
