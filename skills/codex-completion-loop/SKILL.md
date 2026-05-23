---
name: codex-completion-loop
description: Use when the user wants Codex to carry a task through implementation, verification, and final evidence instead of stopping at a partial fix. Inspired by oh-my-codex Ralph completion loops, adapted for native Codex tools without OMX state, tmux, or hooks.
---

# Codex Completion Loop

Drive the task to a real stopping point: implemented, verified, and explained with evidence.

This is the native Codex adaptation of OMX `$ralph` plus the practical parts of `$ultrawork` and `$ultragoal`: keep persistence, evidence, retry discipline, and goal awareness; omit OMX mode state, tmux panes, `.omx/ultragoal` ledgers, and Stop-hook continuation.

## Workflow

1. Define done.
   - Restate the requested outcome in one sentence.
   - Identify the minimum evidence required to prove it works.
2. Work in tight loops.
   - Inspect context.
   - Make focused edits.
   - Run the smallest meaningful verification.
   - Fix failures or explain blockers.
3. Preserve user work.
   - Do not revert unrelated changes.
   - If the worktree is dirty, touch only the intended scope.
4. Escalate only when useful.
   - Use subagents only if the user explicitly asks for them or the current environment permits that workflow and parallel work is genuinely helpful.
   - Prefer `$codex-native-subagent-team` for explicit native subagent coordination.
   - Use browser/PDF/screenshot tools when output quality cannot be proven by text checks alone.
5. Keep goal state honest when goal tools are active.
   - Use current goal status as focus and accounting, not as proof of completion.
   - Mark a goal complete only after the requested outcome and evidence are actually satisfied.
   - If a durable ledger is needed, write a normal repo/vault note instead of pretending to mutate OMX `.omx/ultragoal` state.
6. Finalize with evidence.
   - Summarize what changed.
   - List commands, screenshots, generated files, or checks that prove completion.
   - Mention any unrun checks or remaining risks.

## Failure Handling

- If a command fails, inspect the error and try a bounded fix.
- If external credentials, missing data, or unavailable services block completion, report the blocker and preserve all useful intermediate work.
- Do not invent successful verification.
- If the same blocker repeats after bounded attempts, stop with diagnosis, evidence, and the next owner/action.

## References

Read `references/completion-evidence.html` when deciding what evidence is enough for code, paper, figure, or workflow tasks.
