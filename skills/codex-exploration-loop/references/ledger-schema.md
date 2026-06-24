# Ledger Schema

Use the ledger as the source of truth for an exploration run. Chat context can be compacted or interrupted; ledger files must be recoverable.

## Run Directory

Default:

```text
explorations/<YYYY-MM-DD>-<slug>/
  brief.md
  ledger.jsonl
  frontier.json
  branches/
    b001.md
  artifacts/
  pending_round.json
  scratch-worktree.md
  final-digest.md
```

When the target repo is public-sensitive, prefer a public-safe lab repo or an ignored/private artifact directory.

## Branch Record

`frontier.json` shape:

```json
{
  "active": ["b001"],
  "branches": {
    "b001": {
      "status": "active",
      "hypothesis": "Initial broad exploration branch.",
      "last_score": 0,
      "rounds": [],
      "recent_reflections": [],
      "next_probe": "Inspect the workspace and form first probes."
    }
  }
}
```

Statuses:

- `active`: eligible for next round.
- `paused`: useful but blocked by cost, auth, dependency, or data.
- `pruned`: likely dead end.
- `promoted`: yielded a lead for completion/review.
- `merged`: folded into another branch.

## Round Record

Use `schemas/round-result.schema.json` as the authoritative schema. Required fields:

- `round`
- `branch_id`
- `hypothesis`
- `probe`
- `actions`
- `evidence`
- `scores`
- `reflection`
- `decision`

All records are appended to `ledger.jsonl` as one compact JSON object per line.

## Scoring

Default total:

```text
total = 0.30 * promise
      + 0.25 * novelty
      + 0.25 * evidence
      - 0.10 * risk
      - 0.10 * cost
      + exploration_bonus
```

Scores should use 0-5 integers except `total`, which may be a number.

Interpretation:

- `promise`: likelihood the branch leads to a useful answer.
- `novelty`: how much new surface area or surprising insight it opens.
- `evidence`: how grounded the branch is in observed facts.
- `risk`: chance of wasting budget, damaging state, or overclaiming.
- `cost`: expected time, money, complexity, or dependency cost.

## Recovery

Use `start-round` before a probe. It writes `pending_round.json`.

Use `finish-round` after a probe. It validates and appends the final record, updates frontier state, and removes the pending file.

Use `abort-round` when a probe is interrupted, times out, or is stopped by the user. It appends an aborted record with `decision = "stop"` and keeps artifacts for review.
