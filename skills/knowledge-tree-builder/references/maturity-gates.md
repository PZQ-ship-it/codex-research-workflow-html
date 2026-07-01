# Maturity Gates

Use this reference when deciding how far to build or extend a tree.

Version stages are capability milestones, not mandatory releases. The user does
not need to manually choose every version number. Align the operation profile,
infer a likely maturity target, then build only to the next acceptance gate.

## Version Pattern

| Version | Capability |
|---|---|
| v0 | Minimal source-grounded scaffold: source manifest, index, initial cards, and validation. |
| v1 | Deepen one central branch with stronger evidence, comparisons, and first review-ready matrix. |
| v2 | Add learning path, misconception checks, and experiment-as-learning guides. |
| v3 | Add current-source refresh, benchmark/evaluation norms, and stronger result-boundary checks. |
| v4 | Convert one selected research lane into a protocol draft or project-facing plan. |
| v5 | Make the branch trunk explicit in storage through `branches/` if it was previously only implicit. |
| v6 | Sequentially expand all branches without skipping layers; add missing learning notes, cards, and comparisons. |
| v7 | Add `frontier/` as a long-term research overlay and maintain a research opportunity ledger. |

`frontier/` is a v7 overlay. This also applies to names such as
`frontier_overlay`, frontier radar, watchlist, trend ledger, and opportunity
ledger. Before v7, mention these only as future options or explicitly confirmed
exceptions. Do not make them part of v1-v4 current scope, artifact layout, or
acceptance criteria.

When `frontier-tracking` is requested early, the next gate should usually be:
build the learning trunk, make branch ownership explicit, and define what
confirmation would unlock v7 later. Do not add frontier branches, frontier
templates, opportunity ledgers, or research hooks to the current deliverable.

Invariant:

```text
usable scaffold -> deeper evidence -> learning layer -> evaluation norms -> protocol -> visible trunk -> branch completion -> frontier tracking
```

## Gate Rule

Before crossing a gate, ask whether the move changes:

- scope;
- cost;
- cadence;
- evidence burden;
- project commitment;
- branch trunk;
- public/private boundary.

If yes, confirm with the user before proceeding.

## Mode Target Examples

- Learning-only tree: usually stop at v2 or v3.
- Research-incubation tree: usually needs v4.
- Frontier-tracking tree: usually needs explicit trunk at v5 and may need v7.
- Project-execution work: starts after protocol readiness and should move to a separate project or experiment workflow.
