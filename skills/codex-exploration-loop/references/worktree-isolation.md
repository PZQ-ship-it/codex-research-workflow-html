# Worktree Isolation

Exploration can be bold only when edits are isolated.

## Default

For a Git workspace that may be edited:

```powershell
python <skill-dir>\scripts\explore_ledger.py prepare-worktree `
  --run-dir <run-dir> `
  --branch-id b001 `
  --repo-root <git-repo>
```

The helper records `git status --short --branch`, creates a branch named like `explore/<run>-b001`, writes `worktrees.json`, and annotates the branch in `frontier.json`.

Default path:

- if the run dir is outside the target repo: `<run-dir>\worktrees\<branch-id>`;
- if the run dir is inside the target repo: `<repo-parent>\<repo-name>-codex-worktrees\<run-name>\<branch-id>`.

This avoids nesting a Git worktree inside the main repo checkout.

For read-only probes, a shared repo checkout is acceptable. For edit-heavy sibling probes, create one worktree per branch.

## Lifecycle

Create an isolated worktree:

```powershell
python <skill-dir>\scripts\explore_ledger.py prepare-worktree `
  --run-dir <run-dir> `
  --branch-id b002 `
  --repo-root <git-repo> `
  --base-ref HEAD
```

List recorded worktrees:

```powershell
python <skill-dir>\scripts\explore_ledger.py list-worktrees --run-dir <run-dir>
```

Prepare a worker without passing `--workspace`; it will use the branch worktree when one is active:

```powershell
python <skill-dir>\scripts\explore_ledger.py prepare-worker `
  --run-dir <run-dir> `
  --round 2 `
  --branch-id b002 `
  --portable
```

Mark a worktree as promoted when the branch contains a lead worth turning into a completion-loop or review task:

```powershell
python <skill-dir>\scripts\explore_ledger.py promote-worktree --run-dir <run-dir> --branch-id b002
```

Remove a run-local worktree after collection:

```powershell
python <skill-dir>\scripts\explore_ledger.py retire-worktree --run-dir <run-dir> --branch-id b002
```

`retire-worktree` refuses to remove paths outside the recorded default worktree root unless `--allow-outside-run-dir` is explicit. Use `--force` only for a disposable branch with known dirty files.

## Rules

- Run edit-heavy probes in the scratch worktree.
- Do not merge exploration output automatically.
- Promote a lead into a separate completion-loop task or clean branch.
- Do not copy private transcripts, credentials, cookies, `.env`, or paid content into public run dirs.
- If the main worktree is dirty, do not revert or clean unrelated changes.
- Do not let sibling branches share a writable worktree.
- Do not retire a worktree until its diff, logs, and useful artifacts have been reviewed or copied into the run ledger.

## Windows Path Safety

Before recursive delete or move:

1. Resolve the absolute target path.
2. Verify it is inside the intended scratch worktree or run directory.
3. Use one shell end-to-end.
4. Prefer PowerShell native commands such as `Remove-Item -LiteralPath`.

Never build a path in PowerShell and hand it to another shell for deletion.

## Failure

If worktree creation fails:

- stop before edits if edits are required;
- continue read-only if enough value remains;
- or ask whether a scratch copy is acceptable.
