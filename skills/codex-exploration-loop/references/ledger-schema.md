# Ledger Schema

Use the ledger as the source of truth for an exploration run. Chat context can be compacted or interrupted; ledger files must be recoverable.

## Run Directory

Default:

```text
explorations/<YYYY-MM-DD>-<slug>/
  brief.md
  ledger.jsonl
  frontier.json
  worktrees.json
  branches/
    b001.md
  artifacts/
    b001-round-002.prompt.md
    b001-round-002.codex-exec.ps1
    b001-round-002.worker.json
    b001-round-002.events.jsonl
    b001-round-002.result.json
  pending_rounds/
    b001-round-002.json
  fanout.jsonl
  scratch-worktree.md
  final-digest.md
```

When the target repo is public-sensitive, prefer a public-safe lab repo or an ignored/private artifact directory.

## Branch Record

`frontier.json` shape:

```json
{
  "active": ["b001"],
  "max_active": 3,
  "fanout_width": 3,
  "beam_width": 2,
  "branches": {
    "b001": {
      "status": "active",
      "hypothesis": "Initial broad exploration branch.",
      "last_score": 0,
      "parent_branch_id": "",
      "layer_id": "",
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
- `branched`: split into child branches.
- `parked`: outside the current beam; can be resumed later.

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
- `next_probe`

All records are appended to `ledger.jsonl` as one compact JSON object per line.

Optional fanout fields:

- `parent_branch_id`
- `layer_id`
- `proposed_branches`: child branch candidates. When `decision = branch`, the controller may turn these into child branches in `frontier.json`.

Fanout and selection coordination events are appended to `fanout.jsonl`; they do not replace round records.

## Worktree State

`worktrees.json` records branch-level Git worktree isolation:

```json
{
  "version": "1.0",
  "repo_root": "D:/repo",
  "default_root": "D:/repo/explorations/2026-06-25-demo/worktrees",
  "items": {
    "b002": {
      "branch_id": "b002",
      "path": "D:/repo/explorations/2026-06-25-demo/worktrees/b002",
      "git_branch": "explore/2026-06-25-demo-b002",
      "base_ref": "HEAD",
      "repo_root": "D:/repo",
      "status": "active",
      "created_at": "2026-06-25T10:00:00+08:00",
      "last_pre_status": ["## master...origin/master"]
    }
  }
}
```

Statuses:

- `active`: eligible as the default workspace for that branch.
- `promoted`: kept for follow-up completion or review; still usable by `prepare-worker`.
- `retired`: removed from disk through `git worktree remove`.

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

Use `start-round` before a probe. It writes `pending_rounds/<branch>-round-<n>.json`. Older runs with `pending_round.json` remain readable.

Use `finish-round` after a probe. It validates and appends the final record, updates frontier state, and removes the pending file.

Use `abort-round` when a probe is interrupted, times out, or is stopped by the user. It appends an aborted record with `decision = "stop"` and keeps artifacts for review.
