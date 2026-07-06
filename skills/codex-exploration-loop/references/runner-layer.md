# Runner Layer

Use the v2.0 runner when a fuzzy exploration should advance across multiple bounded rounds with durable state.

Terminology:

- A runner `round` is one branch probe and one ledger record.
- A ToT `fanout layer` is not a round. It creates sibling branches, runs one probe per sibling, then performs beam selection.
- `max_rounds` limits total branch probes, not the number of fanout layers.
- A plan should not schedule every remaining round as a fresh same-layer fanout.

## Contract

The runner owns:

- selecting active frontier branches;
- preparing schema-backed worker artifacts;
- running deterministic `mock`, `replay`, or external `codex exec` rounds;
- recording attempts, failures, and final state;
- calling `digest` after the planned budget.

The lead/controller owns:

- deciding whether the next frontier action is deepen, compare, fanout, promote, prune, or stop;
- ensuring a fanout layer is collected before beam selection;
- continuing from retained beam branches rather than repeatedly restarting top-level parallel exploration.
- resuming the best earlier parked branch when the newest fanout layer is low-yield.

The runner does not own:

- model/tool reasoning;
- approvals;
- sandbox policy beyond passing Codex CLI flags;
- scheduling wake-ups;
- merging or committing work.

Use official Codex mechanisms for those surfaces.

## Files

```text
runner-plan.json
runner-state.json
runner-attempts.jsonl
artifacts/
  b001-round-001.prompt.md
  b001-round-001.codex-exec.ps1
  b001-round-001.schema.json
  b001-round-001.result.json
```

`runner-plan.json` may follow `schemas/runner-plan.schema.json`.

## Modes

- `mock`: prepare a worker and import a deterministic result. Use for smoke tests.
- `replay`: import an existing worker output file. Use for fixture-based validation.
- `external`: run the generated PowerShell `codex exec` worker. Use only when live model/runtime calls are acceptable.

## Stop Rules

Stop when:

- a ledger record has `decision = promote` or `decision = stop`;
- no active branches remain;
- `max_rounds` is reached;
- `max_failures` is reached;
- the user redirects.

Before stopping for "no useful active branch", inspect parked branches with `next-frontier --include-parked`. A weak newest layer is not enough reason to stop if an earlier parked branch remains stronger.

## Handoff

After the runner stops:

- Use `codex-completion-loop` for a promoted implementation lead.
- Use `codex-adversarial-qa` for a promising but risky lead.
- Use Codex Automations for recurring scheduled wake-ups.
- Use SDK/app-server only when an external trusted controller must own scheduling, approvals, streaming, or resume.
