# Artifact Contract

Use this reference when creating, extending, or auditing files in a knowledge tree.

## Minimal v0 Tree

```text
<field>/
  index.md
  manifest.md
  sources.md
  check_tree.py
  papers/
  extracted-text/
  cards/
    research/
    modules-or-concepts/
    architectures-or-systems/
    experiments/
    evaluation/
  comparisons/
  learning/
  build-ledger.md
  workflow-build-process.md
```

## Mature Tree

```text
<field>/
  index.md
  manifest.md
  sources.md
  LOCATION.md
  check_tree.py
  build-ledger.md
  workflow-build-process.md
  research-lanes.md
  download-status.json
  text-extraction-status.json
  branches/
    00-overview.md
    01-<branch>.md
    02-<branch>.md
  frontier/
    00-frontier-map.md
    01-<frontier-lane>.md
    08-research-opportunity-ledger.md
  plans/
  protocols/
  papers/
  extracted-text/
  cards/
    research/
    modules-or-concepts/
    architectures-or-systems/
    platforms/
    evaluation/
    experiments/
  comparisons/
  learning/
```

## File Responsibilities

- `index.md`: human reading entry and current navigation.
- `manifest.md`: purpose, scope, operation profile, directory layout, and status.
- `sources.md`: source IDs, titles, public URLs/citations, source type, primary branch, local evidence path, inclusion reason, and status.
- `build-ledger.md`: inputs inspected, changes made, validation results, remaining risks, and next lane.
- `workflow-build-process.md`: tree-specific construction rules and version history.
- `research-lanes.md`: scored or prioritized research directions.
- `LOCATION.md`: local-location notes only when needed.
- `download-status.json`: machine-readable source acquisition status.
- `text-extraction-status.json`: machine-readable extraction status.
- `check_tree.py`: repeatable validation.
- `branches/`: visible conceptual trunk.
- `frontier/`: v7 long-term research overlay; never replace the branch trunk.
- `protocols/`: selected experiment lanes that are actionable but not yet implementation-ready.

## Language Contract

Default to Chinese for human-facing prose in knowledge-tree artifacts:

- navigation text in `index.md`;
- purpose, scope, non-goals, status, and build summaries;
- learning routes, glossary explanations, misconception checks, and self-check questions;
- branch role descriptions, core questions, missing nodes, and next additions;
- card summaries, learning roles, limitations, and synthesis notes;
- comparison explanations and teaching takeaways.

Keep these tokens in English or original source language:

- file and directory names;
- code, commands, YAML/JSON keys, Markdown link targets, and scripts;
- evidence labels: `source-stated`, `paper-stated`, `Codex-inferred`, `needs-check`, `not-reported`;
- source IDs and card IDs;
- paper titles, venue names, benchmark names, model names, dataset names, URLs, and citations.

If the user explicitly requests English or a bilingual artifact, record that
language preference in `manifest.md` or the operation profile.

## Branch Files

Each branch file should contain:

- role or positioning;
- core questions;
- knowledge nodes;
- existing evidence and linked cards;
- missing nodes;
- expansion rules;
- next additions.

## Card Boundary Labels

Every card should preserve:

- `source-stated` or `paper-stated`;
- `Codex-inferred`;
- `needs-check`;
- `not-reported` when the source omits a needed detail.

## Ownership Rule

Every new artifact gets one primary branch owner. Other branches link to it
instead of duplicating it.
