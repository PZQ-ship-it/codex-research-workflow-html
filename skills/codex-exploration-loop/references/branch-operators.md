# Branch Operators

Use branch operators as tools for exploration. Operator output must become a round record; do not let a sub-skill or subagent become an unlogged side quest.

## Core Operators

- `search`: inspect files, docs, web, issues, or papers.
- `patch`: make a scratch edit to test a hypothesis.
- `experiment`: run a focused command, test, benchmark, or probe.
- `compare`: pit two branches or designs against each other.
- `critic`: attack a promising lead before promotion or when frontier selection is converging without enough evidence.
- `distill`: summarize evidence and compress branch memory.

## Skill Operators

Use these when available and relevant:

- `anysearch`: public web or source search.
- `deep-think-reasoning`: generate or critique lanes.
- `codex-native-subagent-team`: independent branch scouts.
- `codex-adversarial-qa`: attack a promising lead.
- `reporting-trace-maintainer`: record project-relevant discoveries.
- `codex-completion-loop`: implement a promoted lead.
- `skill-eval-optimizer`: test this skill itself.

## Selection

Default frontier policy:

- Keep top 2 active branches by total score.
- Keep 1 diversity branch when it has high novelty and low cost.
- Keep parked branches in the global frontier; they are deferred options, not deleted failures.
- When a new fanout layer is low-yield, compare it against all parked branches and resume the best earlier branch if it is stronger.
- Before a high-promise/low-evidence branch dominates the frontier, run a critic checkpoint and consider a challenger branch.
- Prune branches with two stale rounds and no new evidence.
- Pivot when the top branch is blocked or low-evidence after repeated probes.

Tree-of-Thoughts fanout policy:

- Expand 3-5 sibling branches only when breadth is useful.
- Run sibling probes independently, preferably through native subagents or schema-backed workers.
- Collect all sibling results before selection.
- Use `beam-select` to keep top total-score branches plus optional diversity.
- Park unselected branches so they can be resumed later.
- Use `next-frontier --include-parked` after weak fanout results to recommend the next global frontier branch.
- Use `next-frontier --include-parked --activate` to mark a parked branch active again.
- Use `critic-checkpoint --after-beam --record` when beam selection would collapse to one weakly verified lead.
- Let workers propose `proposed_branches`, but only the lead/controller updates `frontier.json`.

Branch metadata:

- `visits`: number of completed probes on the branch.
- `last_probe_round`: latest round number that touched the branch.
- `rung`: rough probe depth such as `seed` or `fanout`; use it as a human-readable hint, not a strict algorithm.
- `parked_reason` / `resume_reason`: why the branch left or re-entered the active frontier.

## Promotion

Promote only when:

- the lead has concrete evidence;
- a critic checkpoint, adversarial QA pass, or equivalent verification probe did not find a blocking counterexample;
- the next action is no longer exploratory;
- implementation, review, or write-up criteria are clear.

Promoted leads should move to `codex-completion-loop`, `codex-adversarial-qa`, or a human decision.

## Critic Output

A `critic` probe should be concise and actionable:

- strongest counterexample or missing evidence;
- hidden assumption and how to falsify it;
- score correction for `promise`, `evidence`, and `risk`;
- best challenger branch, if any;
- one next verification probe.

If the critique cannot name evidence or a falsification probe, treat it as low-value reflection and do not let it block the controller.
