---
name: codex-native-subagent-team
description: Use when the user explicitly asks for subagents, parallel agents, delegation, or a team-style split in native Codex; adapt oh-my-codex $team ideas to Codex native subagents without tmux, OMX state, or hooks.
---

# Codex Native Subagent Team

Coordinate native Codex subagents safely. This skill is a recipe for explicit parallel work, not an automatic team runtime.

## What This Migrates

This adapts the useful parts of oh-my-codex `$team` and `$ultrawork`:

- grounded context before delegation
- independent lanes with clear ownership
- leader-owned integration and verification
- evidence-first final reporting
- no blind leader: the main thread stays responsible for monitoring, integration, and final truth

It does not migrate OMX tmux panes, `.omx/state`, worker mailboxes, Stop-hook continuation, or automatic keyword routing.

## Use When

- The user explicitly asks for subagents, parallel agents, delegation, or a team-style split.
- Work can be split into independent lanes that materially help the main task.
- Each subtask has a clear output and, for edits, a disjoint write scope.
- The main thread can keep doing useful non-overlapping work while subagents run.

## Do Not Use When

- The user has not explicitly authorized subagents or parallel delegation.
- The next local action is blocked on the delegated result.
- The task is small, sequential, or tightly coupled.
- Multiple agents would edit the same files without a clean ownership boundary.
- The task is still ambiguous enough that `$codex-deep-interview` or `$codex-consensus-plan` should run first.

## Workflow

1. Decide the local critical path first.
   - State what the main thread will do itself.
   - Identify sidecar tasks that can run in parallel without blocking that next step.
2. Shape each subtask.
   - Give each subagent one concrete question or implementation slice.
   - Name allowed files, modules, or read-only scope.
   - Tell editing subagents they are not alone in the codebase and must not revert unrelated work.
3. Spawn only useful lanes.
   - Prefer `explorer` for bounded codebase questions.
   - Prefer `worker` for bounded edits with clear file ownership.
   - Omit explicit model overrides unless the user requested one or there is a clear task-specific reason.
4. Continue local work.
   - Do not wait immediately unless the next action truly depends on the result.
   - Avoid duplicating the delegated task locally.
5. Integrate results.
   - Review returned claims or patches.
   - Resolve conflicts in the main thread.
   - Run the smallest meaningful verification.
6. Report lane evidence.
   - For each subagent, capture the result, changed files if any, and confidence or remaining uncertainty.
   - If a subagent edits files, inspect the diff before claiming the lane is integrated.
7. Close or stop tracking agents when no longer needed.
   - Do not leave unused subagents open after their result has been integrated.

## Delegation Template

Use this shape when asking for subagents:

```text
Use native subagents for these independent lanes:

Main thread:
- I will own: <critical path work>
- I will not duplicate: <delegated lanes>

Subagent A (<explorer|worker>):
- Goal:
- Scope:
- Files/modules:
- Output needed:
- Non-goals:

Subagent B (<explorer|worker>):
- Goal:
- Scope:
- Files/modules:
- Output needed:
- Non-goals:

Integration:
- Main thread will compare results, apply or reconcile changes, and run <verification>.
```

## Output Shape

When planning subagent work, report:

- Local critical path
- Delegated lanes
- Ownership boundaries
- Verification plan
- Stop condition

When finishing, report:

- What the main thread changed
- What each subagent contributed
- What was verified
- Any unrun checks or residual risk

## Safety Rules

- Do not use subagents as a substitute for reading the relevant code yourself.
- Do not spawn multiple agents on the same unresolved write scope.
- Do not hand off destructive, credentialed, or external-production work unless the user explicitly authorized that exact action.
- Preserve unrelated dirty work.
- If a subagent result conflicts with current repo evidence, trust the repo and inspect before applying.
- Do not treat subagent completion as task completion; the leader must still verify the integrated outcome.

## References

Read `references/native-subagent-team.html` when you need concrete lane examples or prompt templates.
