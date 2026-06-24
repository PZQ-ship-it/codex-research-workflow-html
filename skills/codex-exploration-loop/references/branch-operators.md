# Branch Operators

Use branch operators as tools for exploration. Operator output must become a round record; do not let a sub-skill or subagent become an unlogged side quest.

## Core Operators

- `search`: inspect files, docs, web, issues, or papers.
- `patch`: make a scratch edit to test a hypothesis.
- `experiment`: run a focused command, test, benchmark, or probe.
- `compare`: pit two branches or designs against each other.
- `critic`: attack a promising lead before promotion.
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
- Prune branches with two stale rounds and no new evidence.
- Pivot when the top branch is blocked or low-evidence after repeated probes.

## Promotion

Promote only when:

- the lead has concrete evidence;
- the next action is no longer exploratory;
- implementation, review, or write-up criteria are clear.

Promoted leads should move to `codex-completion-loop`, `codex-adversarial-qa`, or a human decision.
