# Tree-of-Thoughts Fanout

Use fanout when breadth is the point: several plausible hypotheses exist, early commitment is risky, or the user explicitly asks for parallel exploration.

## Concepts

- `round`: one branch probe and one ledger record.
- `layer`: one fanout/collection/beam-selection event.
- `generation`: sibling branches created by the same fanout layer.
- `beam`: retained branches after selection.

Do not equate `max_rounds` with fanout layers. `max_rounds = 8` means eight total probes. A first layer with four sibling probes already uses four rounds.

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
   - Use `prepare-worktree` first for any sibling branch that may edit files; omit `--workspace` in `prepare-worker` so the worker inherits that branch worktree.
   - Give every worker one branch, one probe, one budget, and the same safety gates.
3. Collect all sibling results before selection.
   - Do not beam-select early just because one branch finished first.
   - Import every worker result as a normal round record.
4. Select the next beam.
   - Run `critic-checkpoint --after-beam` first when one high-promise/low-evidence branch would dominate or when two branches are close but imply different next actions.
   - Run `beam-select`.
   - Keep top total-score branches.
   - Keep an extra diversity branch when novelty is high and cost is acceptable.
   - Park unselected branches instead of deleting them.
5. Continue, pivot, promote, or run another fanout layer.
   - Continue means deepen one retained branch.
   - Run another fanout only from a retained branch that needs sub-hypotheses.
   - If all retained or newly created children are weak, resume the best earlier parked branch from the global frontier.
   - Do not fan out every round by default.

Example with `max_rounds = 8`:

1. Layer 1: create four sibling branches and run four probes. Rounds used: 1-4.
2. Beam-select: keep two branches plus one diversity branch.
3. Deepen the best retained branch for two probes. Rounds used: 5-6.
4. If still fuzzy, fan out from that retained branch into two children. Rounds used: 7-8.
5. Stop, summarize, or promote. Do not create eight separate top-level sibling layers.

## Controller Decision Rule

- Fan out when the current branch question is still broad and has independent plausible hypotheses.
- Deepen when one branch has concrete evidence but needs another probe.
- Compare when two retained branches are close in score or imply different next actions.
- Criticize when a branch looks promising but is under-verified, has repeated `continue` decisions, or is about to be promoted.
- Resume a parked branch when the latest fanout layer is low-yield and an earlier branch has higher score, stronger evidence, or lower cost.
- Promote when the next step has become implementation, review, write-up, or human decision.
- Stop when the remaining budget cannot improve the decision.

## Low-Yield Fanout Fallback

Treat a fanout layer as low-yield when every probed child is below the useful score threshold or all children remain low-evidence. The default helper threshold is `total < 2.5` or `evidence < 2`, but controller judgment wins when the score is obviously miscalibrated.

When a layer is low-yield:

- Do not keep probing its children merely because they are recent.
- Run `next-frontier --include-parked` to inspect the global frontier.
- Prefer the best parked branch outside the latest layer when it has better score, evidence, risk, or cost.
- Activate the branch with `next-frontier --include-parked --activate` when the run ledger should reflect the fallback.
- Record the reason in the next round reflection: latest fanout was low-yield, so the controller resumed an earlier parked branch.

This is a best-first / beam-search control move, not a new round decision enum. The next round still records `continue`, `pivot`, `branch`, `prune`, `promote`, or `stop`.

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
- after a low-yield layer, compare selected children against parked branches from earlier layers before spending another round.
- when a critique finds a plausible counterexample, treat the lead's score as provisional and spend the next probe on verification, comparison, or branch split rather than promotion.

## Safety

- Use separate scratch worktrees for edit-heavy sibling branches.
- Prefer read-only sibling probes for first fanout.
- Do not let sibling workers write the same files.
- Keep paid, credentialed, destructive, commit/push, merge, and production actions gated by explicit user confirmation.
- Keep portable artifacts free of `.env`, cookies, tokens, private transcripts, and unnecessary absolute paths.

## Recovery

- If a worker fails, record an abort round for that branch and continue collecting other siblings.
- If only one sibling succeeds, do not pretend beam selection was comparative; state that the layer collapsed.
- Parked branches can be reactivated with `next-frontier --include-parked --activate`, or manually by editing `frontier.json` if needed.
