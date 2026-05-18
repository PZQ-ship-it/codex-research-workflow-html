# Algorithm And Method Paper Workflow

Use this reference for papers where the main contribution is an algorithm, model, architecture, optimization method, benchmark result, system, dataset, or implementation pipeline.

## Classification Signals

Treat a paper as algorithm/method-oriented when the abstract or introduction emphasizes:

- a new model, method, architecture, pipeline, objective, loss, training strategy, or inference procedure;
- theoretical properties or complexity;
- experimental improvement over baselines;
- ablations, benchmark tables, or implementation details.

Treat a paper as empirical/benchmark-oriented when it emphasizes:

- new evaluation protocol, dataset, benchmark suite, leaderboard, or large comparison;
- broad empirical findings rather than a single new method.

Treat a paper as system/tool/dataset-oriented when it emphasizes:

- system architecture, data collection, annotation, tooling, deployment, or resource release.

## Required HTML Sections

Build the digest around these sections:

- `Problem`: task, assumptions, inputs, outputs, and constraints;
- `Prior Gap`: what previous work could not do;
- `Method At A Glance`: one-paragraph method intuition plus overview figure;
- `Core Mechanics`: algorithm steps, model modules, objective, data flow, or pseudo-code;
- `Novelty Claims`: what is actually new, separated from normal engineering choices;
- `Experiments`: datasets, metrics, baselines, setup, hyperparameters if provided;
- `Results`: main tables/plots, ablations, sensitivity analyses, and statistical caveats;
- `Limitations`: failure cases, assumptions, resource cost, external validity;
- `Implementation Notes`: dependencies, inputs, outputs, reproducibility hints, and likely missing details.

## Figure Priorities

Prefer these visuals:

- architecture diagram;
- pipeline or flowchart;
- algorithm pseudo-code;
- main result table or plot;
- ablation figure;
- qualitative examples or failure cases;
- dataset construction diagram.

## Reading Heuristics

- Compare the method overview figure against the claimed novelty before writing the summary.
- Keep datasets and metrics close to the result claims.
- Mark result numbers as `needs manual check` if table extraction is uncertain.
- Separate "paper claims" from "your interpretation".
- Preserve formulas or pseudo-code as images or page references if extraction is unreliable.
