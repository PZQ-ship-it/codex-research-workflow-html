---
name: codex-exploration-loop
description: Use when Codex should explore a fuzzy, underspecified, or stubborn problem through bounded rounds rather than finish a known implementation. Triggers include time-boxed or round-count exploration, "try several directions", "keep attacking this unclear issue", surprising-design search, sandboxed brute-force investigation, branch exploration with subagents, or evidence-seeking loops inspired by Tree of Thoughts, Reflexion, or Voyager. Do not use for straightforward implementation, final cleanup, review-only tasks, credential setup, or high-risk external actions.
---

# Codex Exploration Loop

Run a bounded exploration loop for fuzzy work. The goal is leads, evidence, and a next decision, not pretending the problem is complete.

## Quick Start

1. Restate the fuzzy target as `question`.
2. Choose defaults when the user did not specify them:
   - `mode`: `standard`
   - `max_rounds`: `6`
   - `round_timebox_minutes`: `10`
   - `workspace`: current repo
3. Gate risky actions:
   - Allowed by default: read/search, scratch edits, public network, local tests, local skills.
   - Ask first: destructive edits, paid/authenticated calls, credentials, commit/push, merge, production systems.
4. Initialize a run directory with `scripts/explore_ledger.py init`.
5. For each round:
   - select a branch from `frontier.json`;
   - write `start-round`;
   - run one concrete probe;
   - write `finish-round` with evidence, score, reflection, and decision.
6. Stop when the round budget is used, a lead is promoted, all branches are blocked/pruned, or the user redirects.
7. End with best leads, dead ends, artifacts, and the recommended next lane.

## Modes

Scout:

- 3 rounds, 5 minutes each.
- Prefer read-only probes.
- No subagents unless the user explicitly asks.

Standard:

- 6 rounds, 10 minutes each.
- Use a scratch worktree for edit-heavy probes.
- Public network, local commands, local skills, and one independent branch worker are allowed when useful.

Bull:

- 10 rounds, 15 minutes each.
- Scratch worktree required for edits.
- Bounded subagents and branch fanout are allowed.
- Keep explicit gates for paid, authenticated, destructive, commit/push, and merge actions.

## Round Discipline

Every round must produce a decision:

- `continue`: same branch deserves one more probe.
- `pivot`: same problem, different hypothesis.
- `branch`: split a promising alternative.
- `prune`: stop spending budget on this branch.
- `promote`: convert the lead into a completion/review task.
- `stop`: budget done or no useful next probe.

Reflection must be delta-oriented: say what changed, what failed, and what to try next.

## Official Codex First

Use Codex mechanisms before custom harness code:

- AGENTS.md for repo policy.
- Codex skills for reusable workflows.
- Permission profiles, sandbox modes, and approval policy for boundaries.
- Codex app worktrees or Git worktrees for isolation.
- Native subagents for bounded independent branch scouts.
- MCP/connectors/web search for external tools.
- `codex exec` plus `schemas/round-result.schema.json` for scripted round workers.
- Codex automations or SDK/app-server only for long-running unattended v2 workflows.

Do not rebuild Codex's model/tool loop, subagent pool, approval system, sandbox, or scheduler inside this skill.

## Resource Routing

Read only what is needed:

- `references/ledger-schema.md`: ledger files, JSON shapes, scoring, and recovery.
- `references/worktree-isolation.md`: scratch worktree and path-safety rules.
- `references/branch-operators.md`: branch decisions, scoring, and local-skill operators.
- `references/official-codex-mechanisms.md`: when to use Codex skills, subagents, `codex exec`, automations, SDK, and MCP.
- `references/codex-exec-round-workers.md`: how to run schema-backed non-interactive branch workers.
- `references/automation-and-sdk-runner.md`: v2 guidance for recurring or programmatic runs.
- `prompts/lead-controller.prompt.md`: reusable lead-agent prompt skeleton.
- `prompts/round-worker.prompt.md`: reusable branch-worker prompt skeleton.
- `schemas/round-result.schema.json`: output schema for round records.
- `scripts/explore_ledger.py`: deterministic run-dir, ledger, frontier, and digest helper.

## Minimal Commands

Initialize:

```powershell
python <skill-dir>\scripts\explore_ledger.py init `
  --root <workspace> `
  --slug <slug> `
  --question "<question>" `
  --max-rounds 6 `
  --round-timebox-minutes 10 `
  --mode standard
```

Start and finish a round:

```powershell
python <skill-dir>\scripts\explore_ledger.py start-round --run-dir <run-dir> --round 1 --branch-id b001 --timebox-minutes 10
python <skill-dir>\scripts\explore_ledger.py finish-round --run-dir <run-dir> --record-json <round-result.json>
```

Summarize:

```powershell
python <skill-dir>\scripts\explore_ledger.py frontier --run-dir <run-dir>
python <skill-dir>\scripts\explore_ledger.py digest --run-dir <run-dir>
```

## Output

Final response:

```text
Exploration complete
- Budget used:
- Run dir:
- Scratch worktree:

Best leads
1. ...

Dead ends
- ...

Artifacts
- ...

Recommended next lane
- completion-loop / adversarial-qa / continue-exploration / human decision

Not done
- ...
```
