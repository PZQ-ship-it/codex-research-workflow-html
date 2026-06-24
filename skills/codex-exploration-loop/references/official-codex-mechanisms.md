# Official Codex Mechanisms

Use official Codex surfaces before custom code.

## Use Skills For

- reusable exploration protocol,
- instructions and references,
- deterministic helper scripts,
- routing to other skills.

Skills are the authoring format. Plugins are the distribution unit when a skill needs broader team or marketplace-style installation.

## Use Subagents For

- independent branch scouts,
- parallel criticism of a lead,
- bounded search over clearly separated hypotheses.

The lead agent must integrate results, score branches, and log records.

## Use `codex exec` For

- scripted branch workers,
- CI-style or non-interactive probes,
- schema-backed final outputs,
- repeatable dry runs.

Prefer `--sandbox workspace-write`, `--profile`, `--output-schema`, `--output-last-message`, and `--json`.

## Use Automations For

- scheduled wake-ups,
- heartbeat continuation in the same thread,
- independent recurring checks across projects.

Thread automations preserve conversation context. Standalone/project automations start fresh recurring work.

## Use SDK/App-Server For

- custom UI,
- trusted external controller,
- streamed event handling,
- external approval or resume logic.

The external controller should orchestrate Codex. It should not directly rebuild Codex's model/tool loop.

## Use MCP/Connectors For

- issue trackers,
- docs systems,
- browser/data sources,
- tools that should be exposed as typed external actions.

Do not write custom crawlers or API wrappers when a reliable MCP/connector already fits.
