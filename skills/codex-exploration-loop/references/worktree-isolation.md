# Worktree Isolation

Exploration can be bold only when edits are isolated.

## Default

For a Git workspace that may be edited:

```powershell
git status --short --branch
git worktree add -b explore/<slug>-<timestamp> <scratch-worktree-path> HEAD
```

Record the pre-run status in `brief.md` or `scratch-worktree.md`.

## Rules

- Run edit-heavy probes in the scratch worktree.
- Do not merge exploration output automatically.
- Promote a lead into a separate completion-loop task or clean branch.
- Do not copy private transcripts, credentials, cookies, `.env`, or paid content into public run dirs.
- If the main worktree is dirty, do not revert or clean unrelated changes.

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
