# Exploration Loop Handoff

`codex-wide-scout` is a breadth-first front end. `codex-exploration-loop` is the deepening engine.

## Reuse Existing Helpers

Prefer the installed `codex-exploration-loop` helper for:

- `init`: run directory and compatible ledger;
- `fanout`: lane branch creation;
- `prepare-worktree`: per-lane isolation;
- `prepare-worker` and `finish-worker`: schema-backed non-interactive workers;
- `finish-round`: importing lane records;
- `digest`: final artifact when the run becomes a deeper exploration.

Do not copy `explore_ledger.py` into this skill.

## Wide Scout To Deep Exploration

When a lane becomes a lead:

1. Keep the lane's branch id, evidence, and artifacts.
2. Run `beam-select` only if you need to reduce active branches before deepening.
3. Hand off the selected branch to `codex-exploration-loop`.
4. Start deepening from the lane's `next_probe`, not from the original broad question.

## Wide Scout To Completion

When a lane is already implementation-shaped:

1. Summarize the chosen approach and why alternatives were rejected.
2. Preserve useful artifacts.
3. Retire unneeded worktrees.
4. Hand off to `codex-completion-loop`.

## Isolation Rules

- Read-only lanes may share a workspace.
- Write-capable lanes need separate Git worktrees.
- Internal subagents inside one lane may share the lane worktree only if they write disjoint files.
- Never let a lane scout write the controller's synthesis files.

## Handoff Note

Use this compact note:

```text
Handoff from codex-wide-scout
- Run dir:
- Selected lane:
- Hypothesis:
- Evidence:
- Rejected alternatives:
- Remaining uncertainty:
- Recommended next skill:
- First next probe/action:
```
