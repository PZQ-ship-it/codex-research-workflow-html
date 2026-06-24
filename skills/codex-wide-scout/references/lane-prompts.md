# Lane Prompts

Use these shapes for native subagents or `codex exec` workers.

## Native Subagent Lane

```text
Use $codex-wide-scout to scout one lane only.

Question:
<overall question>

Wave:
<wave number>

Lane:
<lane id>

Hypothesis:
<lane hypothesis>

Probe:
<concrete lane probe>

Scope:
<read-only / scratch-write worktree / web allowed / skills allowed>

Return:
- evidence paths or URLs;
- what changed your view;
- scores for novelty, promise, evidence, coverage, cost, and risk;
- one-paragraph lane brief;
- next suggestion: deepen, split, park, discard, or hand off.

Do not update the controller ledger, frontier, wave table, git branches, commits, or final synthesis.
Do not touch credentials, paid/authenticated services, production systems, commit, push, or merge.
```

## Multiple Subagents Inside One Lane

Use `subagents_per_lane > 1` only when a lane has internal dimensions that can be checked independently, for example:

- source discovery versus implementation feasibility;
- optimistic route versus adversarial route;
- baseline evidence versus contrary evidence;
- user-value analysis versus technical risk.

Give each internal scout a different angle. Do not ask several agents the same prompt unless the task is explicitly about robustness or consensus.

## Controller Duties

The lead agent must:

- read the relevant local context before dispatch;
- define lanes and budgets;
- create worktrees for write-capable lanes;
- collect every lane before wave synthesis;
- resolve contradictions;
- write the final scout map.

Lane scouts may propose splits, but only the controller decides the next wave or handoff.
