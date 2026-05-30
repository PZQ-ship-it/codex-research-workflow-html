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

## Native Agent Installation

This repository may contain two different agent forms:

- Native Codex custom agents: `.codex/agents/*.toml`
- Legacy or extended prompt specs: `agent/*.md`

Only the TOML files are directly spawnable as Codex native custom agents. Markdown specs can be used as source material or fallback guidance, but reading a Markdown spec does not install a spawnable agent.

To install project agents globally, copy TOML files from this repository into the user-level native agent directory:

```powershell
New-Item -ItemType Directory -Force $HOME\.codex\agents | Out-Null
Copy-Item -Force .codex\agents\*.toml $HOME\.codex\agents\
```

Then validate the installed agents when `agent-creator` is available:

```powershell
python $HOME\.codex\skills\agent-creator\scripts\create_agent.py validate $HOME\.codex\agents
```

If `agent-creator` is not installed, at minimum parse the files with Python/TOML or inspect that each file has `name`, `description`, and `developer_instructions`.

## Subagent Config Check

When a task depends on native subagents, Codex should check the local feature flags before assuming custom agents can be spawned:

```powershell
codex features list
```

For the Codex CLI version currently used with this repository, the expected effective flags are:

```text
child_agents_md  true
collab           true
```

`~/.codex/config.toml` should include:

```toml
[features]
child_agents_md = true
collab = true

[agents]
max_threads = 6
max_depth = 1
```

If these flags are missing or false, do not silently continue as if native custom agents are enabled. Tell the user to add the snippet above to `~/.codex/config.toml` and restart Codex. Some newer Codex documentation mentions `features.multi_agent`; verify with `codex features list` before using it, because older local CLIs may reject that flag.

After installing or changing `.toml` agents, remind the user that an already-running Codex session may not hot-load new custom agent types. Restart Codex before doing an availability test.

## Verification

- For documentation-only edits, a read-through is usually enough.
- For workflow instructions involving commands, tools, hooks, MCP, or browser verification, include a minimal smoke-test or sanity-check command when practical.
