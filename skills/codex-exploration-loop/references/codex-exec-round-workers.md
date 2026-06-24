# Codex Exec Round Workers

Use `codex exec` when a branch round should run as a scripted worker and return a schema-valid result.

## v1.5 Adapter

Prefer the helper script over hand-writing worker commands:

```powershell
python <skill-dir>\scripts\explore_ledger.py prepare-worker `
  --run-dir <run-dir> `
  --round 2 `
  --branch-id b001 `
  --workspace <scratch-worktree-or-repo> `
  --probe "Run the next smallest useful probe." `
  --portable

& <run-dir>\artifacts\b001-round-002.codex-exec.ps1

python <skill-dir>\scripts\explore_ledger.py finish-worker `
  --run-dir <run-dir> `
  --worker-output <run-dir>\artifacts\b001-round-002.result.json
```

`prepare-worker` writes:

- `<branch>-round-<n>.prompt.md`
- `<branch>-round-<n>.codex-exec.ps1`
- `<branch>-round-<n>.worker.json`
- `<branch>-round-<n>.events.jsonl` path for Codex JSON events
- `<branch>-round-<n>.result.json` path for the schema result

It also starts `pending_round.json` unless `--no-start` is passed.

Use `--portable` when the artifact directory may be committed, shared, or moved. It writes relative manifest fields and copies the schema beside the generated worker script.

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
- If a worker writes prose around JSON, `finish-worker` will try to extract the first JSON object, but the preferred contract remains JSON-only output.

## Avoid

- `--dangerously-bypass-approvals-and-sandbox` except in a disposable isolated runner.
- workers that can commit, push, merge, or touch credentials.
- workers that modify the main worktree.
