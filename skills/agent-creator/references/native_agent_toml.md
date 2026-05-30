# Native Agent TOML Reference

Use this reference when creating or debugging Codex native custom agents.

## Native Directories

- Global personal agents: `~/.codex/agents/*.toml`
- Project agents: `.codex/agents/*.toml`
- Legacy Markdown specs: `agent/*.md` or `~/.codex/agent/*.md`

Markdown specs are useful source material but are not native spawnable agents by themselves.

## Required Fields

```toml
name = "agent_name"
description = "Short routing guidance."
developer_instructions = """
Role, workflow, boundaries, and evidence contract.
"""
```

`name` should be snake_case. The file should usually be the same concept in kebab-case, for example:

- `name = "ppt_storyboard"`
- file: `ppt-storyboard.toml`

## Optional Fields

```toml
nickname_candidates = ["Short Name", "Another Name"]
model = "gpt-5.4"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
```

You can include normal Codex config-layer keys in a custom agent file when needed, such as `mcp_servers` or `skills.config`.

## Instruction Checklist

Good `developer_instructions` include:

- Role: what the agent owns.
- Non-role: what the agent must not do.
- Inputs: files, runtime config, or context it should read.
- Outputs: exact artifacts or final report fields.
- Ownership: allowed write scope and forbidden files.
- Workflow: short ordered procedure.
- Quality gates: minimum checks before returning.
- Handoff: what evidence the parent needs for integration.
- Fallbacks: what to do when inputs, tools, or permissions are missing.

## Example

```toml
name = "docs_researcher"
description = "Documentation specialist that verifies current API behavior before implementation."
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
nickname_candidates = ["Docs Scout", "API Verifier"]
developer_instructions = """
You verify APIs and version-specific behavior from primary documentation.
Do not edit code. Return concise findings with exact references and residual uncertainty.
"""

[mcp_servers.openaiDeveloperDocs]
url = "https://developers.openai.com/mcp"
```

## Version Compatibility

For the tested local CLI generation, multi-agent support is enabled by:

```toml
[features]
collab = true
child_agents_md = true

[agents]
max_threads = 6
max_depth = 1
```

Some newer documentation names the stable feature `features.multi_agent`. Always verify accepted flags with `codex features list`.

## Validation

Run:

```powershell
python <skill>/scripts/create_agent.py validate <agent-file-or-dir>
```

Then restart Codex if the current session was already running before the file was created.
