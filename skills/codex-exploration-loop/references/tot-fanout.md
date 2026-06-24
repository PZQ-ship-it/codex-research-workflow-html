# Tree-of-Thoughts Fanout

Use fanout when breadth is the point: several plausible hypotheses exist, early commitment is risky, or the user explicitly asks for parallel exploration.

## Default Shape

- `scout`: avoid fanout unless explicitly requested.
- `standard`: fanout width 3, beam width 2, max one worker unless the user authorized subagents.
- `bull`: fanout width 3-5, beam width 2, diversity branch 1, bounded subagents when useful.

## Layer Protocol

1. Expand candidate thoughts.
   - Use `fanout` for human/lead-authored candidates.
   - Or return `decision = branch` with `proposed_branches` in a round result.
2. Dispatch sibling branches.
   - Use native subagents for independent read/search/design lanes when authorized.
   - Use `prepare-worker` / `finish-worker` for schema-backed `codex exec` branch workers.
   - Give every worker one branch, one probe, one budget, and the same safety gates.
3. Collect all sibling results before selection.
   - Do not beam-select early just because one branch finished first.
   - Import every worker result as a normal round record.
4. Select the next beam.
   - Run `beam-select`.
   - Keep top total-score branches.
   - Keep an extra diversity branch when novelty is high and cost is acceptable.
   - Park unselected branches instead of deleting them.
5. Continue, pivot, promote, or run another fanout layer.

## Subagent Prompt Shape

Use this shape for each native subagent branch:

```text
Use $codex-exploration-loop to explore one branch only.

Question:
<question>

Branch:
<branch-id>

Hypothesis:
<hypothesis>

Probe:
<probe>

Scope:
<read-only or scratch-write scope>

Return:
- evidence paths or URLs;
- scores for novelty, promise, evidence, risk, and cost;
- a delta-oriented reflection;
- decision: continue, pivot, branch, prune, promote, or stop;
- optional proposed_branches if this branch should split further.

Do not modify frontier.json, ledger.jsonl, or selection artifacts.
Do not commit, push, merge, touch credentials, or use paid/authenticated services.
```

## Beam Policy

Score remains:

```text
total = 0.30 * promise + 0.25 * novelty + 0.25 * evidence - 0.10 * risk - 0.10 * cost + exploration_bonus
```

Selection rule:

- primary beam: highest `total`;
- diversity slot: highest `novelty - 0.5 * cost` outside the primary beam;
- ties: prefer higher evidence, then lower risk, then lower cost;
- low-evidence branches should not be promoted even when novelty is high.

## Safety

- Use separate scratch worktrees for edit-heavy sibling branches.
- Prefer read-only sibling probes for first fanout.
- Do not let sibling workers write the same files.
- Keep paid, credentialed, destructive, commit/push, merge, and production actions gated by explicit user confirmation.
- Keep portable artifacts free of `.env`, cookies, tokens, private transcripts, and unnecessary absolute paths.

## Recovery

- If a worker fails, record an abort round for that branch and continue collecting other siblings.
- If only one sibling succeeds, do not pretend beam selection was comparative; state that the layer collapsed.
- Parked branches can be manually reactivated by editing `frontier.json` if the lead later needs them.
