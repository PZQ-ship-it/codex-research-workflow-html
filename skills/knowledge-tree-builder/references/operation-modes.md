# Operation Modes

Use this reference when the user is creating or maintaining a durable knowledge
tree and the long-term operating behavior matters.

## Profile Shape

```text
Operation Profile:
- Mode flags: learning, <optional modes>
- Priority: <primary mode first, then secondary modes>
- Update cadence: <cadence preset or custom rule>
- Source refresh cadence: <cadence preset or custom rule>
- Promotion path: <how sources become cards, hooks, matrices, protocols, or frontier opportunities>
- Human confirmation gates: <changes that require user approval>
```

## Mode Flags

`learning` is required and enabled by default.

Optional flags:

- `research-incubation`: add research lanes, hooks, experiment matrices, and protocol drafts.
- `frontier-tracking`: add frontier lanes, source refresh routines, and a research opportunity ledger.
- `project-execution`: connect selected protocols to a concrete project, codebase, dataset, manuscript, or experiment plan.
- `teaching-reference`: emphasize glossary, concept maps, reading routes, examples, and self-check questions.

Mode flags can be combined. Always state priority order when more than one mode
is active.

## Cadence Presets

Default:

- monthly update;
- quarterly review.

Other presets:

- low intensity: on-demand updates plus quarterly review;
- medium intensity: biweekly updates plus monthly review;
- high intensity: weekly source scan plus monthly consolidation.

Higher-frequency modes should be explicit because they increase maintenance
cost and uncontrolled expansion risk.

Do not infer weekly cadence from words like "fast," "serious," or "frontier"
alone. If the user has not explicitly selected high intensity, recommend the
default monthly update plus quarterly review and list weekly scanning as an
option requiring confirmation.

## Promotion Paths

Default learning path:

```text
source candidate -> sources.md -> card -> branch link -> learning guide or glossary update
```

Research-incubation path:

```text
source/card/comparison -> research hook -> experiment matrix -> protocol draft -> project or experiment handoff
```

Frontier-tracking path:

```text
source candidate -> frontier lane -> opportunity ledger -> branch/card consolidation -> matrix or protocol when justified
```

Project-execution path:

```text
protocol draft -> implementation constraints -> experiment/design review -> project plan -> execution handoff
```

## Mode-To-Maturity Guidance

- `learning`: usually targets v2 or v3.
- `learning + research-incubation`: usually targets v4.
- `learning + frontier-tracking`: usually targets v5 or v7, depending on whether the branch trunk is already explicit.
- `learning + research-incubation + frontier-tracking`: usually targets v7.
- `project-execution`: starts from an existing protocol-ready tree and moves through a separate project or experiment workflow.

These are recommended targets, not automatic permission to expand. Stop at the
next meaningful acceptance gate when scope, cost, or evidence quality changes.

If a mode implies a high maturity target but the current tree is missing earlier
capabilities, state the eventual target separately from the next gate. The next
gate wins.

For early `learning + frontier-tracking`, use this split:

- eventual target: v7 after confirmation;
- current gate: v2/v3 for learning usability or v5 for explicit branch trunk;
- current scope: no frontier artifacts, only future confirmation requirements.
