# Codex Exec Round Workers

Use `codex exec` when a branch round should run as a scripted worker and return a schema-valid result.

## Template

```powershell
codex exec `
  --cd <scratch-worktree> `
  --sandbox workspace-write `
  --profile codex-exploration-standard `
  --output-schema <skill-dir>\schemas\round-result.schema.json `
  --output-last-message <run-dir>\artifacts\b001-round-001.json `
  --json `
  "<round-worker prompt>"
```

## Rules

- Give the worker one branch, one probe, and one budget.
- Pass only compact branch memory and required paths.
- Do not pass hidden expected answers.
- Require the worker to output only the round result object.
- Log invalid worker output as an artifact and have the lead agent review it.
- Use `codex exec resume` only when continuing the same non-interactive worker session is intentional.

## Avoid

- `--dangerously-bypass-approvals-and-sandbox` except in a disposable isolated runner.
- workers that can commit, push, merge, or touch credentials.
- workers that modify the main worktree.
