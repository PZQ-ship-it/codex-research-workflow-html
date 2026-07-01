# Prompt Templates

Use these when the user wants concrete prompts or when handing work to another run.

Unless the user requests another language, add this line to handoff prompts:

```text
Write human-facing knowledge-tree prose in Chinese. Keep file names, code,
YAML/JSON keys, evidence labels, paper titles, URLs, source IDs, and benchmark
or model names in English/original form.
```

## Deep Interview

```text
Use $codex-deep-interview.
I want to build a knowledge tree for <field/direction>.
Clarify purpose, audience, scope, non-goals, acceptance criteria, and the right starting layer.
Separate learning goals from research/project self-check goals.
Confirm the long-term operation profile: mode flags, priority, cadence,
promotion path, and human confirmation gates.
Write human-facing knowledge-tree prose in Chinese while preserving technical tokens.
```

## Consensus Plan

```text
Use $codex-consensus-plan.
Design a layered knowledge tree for <field>.
Use 5-7 layers.
For each layer, explain why it exists, what nodes belong there,
which source types are needed, what learning questions it should answer,
and what files should represent the visible branch trunk.
Write human-facing knowledge-tree prose in Chinese while preserving technical tokens.
```

## Seed Corpus

```text
Find a compact seed corpus for <field>.
It should cover foundations, core mechanisms, method families, systems,
evaluation, and research hooks.
Prefer public/official/open sources.
Create a source manifest with source ID, title, URL, source type,
local evidence path, primary branch, status, and why included.
Write human-facing explanations in Chinese while preserving titles, URLs, and IDs.
```

## Research Card

```text
Convert <source> into a source-grounded research card for the <field> knowledge tree.
Include problem, core reusable idea, modified system position, mechanism,
evidence, limitations, relevance to the target field, taxonomy placement,
and follow-up hooks.
Separate source-stated facts, inferred connections, and needs-check items.
Write card prose in Chinese while preserving source titles and evidence labels.
```

## Comparison

```text
Create a comparison table for <method family>.
Columns should include mechanism, insertion point, assumptions,
cost, benefit target, best-fit tasks, failure modes, and evidence anchors.
End with what this teaches a learner and what it checks in research.
Do not rank by benchmark score unless version, split, metric, and protocol are clear.
Write explanations and takeaways in Chinese while preserving technical labels.
```

## Experiment Matrix

```text
Turn this research hook into an experiment matrix:
<hook>

Include falsifiable hypothesis, baseline, isolated modification,
ablation matrix, metrics, guardrails, resource estimate,
failure interpretation, reviewer-risk checklist, and review handoff.
```

## Protocol Draft

```text
Convert this review-ready experiment matrix into a protocol draft.
Name baselines, datasets, metrics, ablations, guardrails, compute/data assumptions,
license and leakage checks, pre-implementation gates, and unresolved blockers.
Keep it as a draft until benchmark version, checkpoints, data access, and review feedback are locked.
```

## Frontier Overlay

```text
Create a frontier overlay for this mature knowledge tree.
Do not replace the branch trunk.
Organize frontier lanes by research questions, technical tensions,
evidence strength, opportunities, and next steps.
Add a research opportunity ledger with trackable opportunity IDs.
```
