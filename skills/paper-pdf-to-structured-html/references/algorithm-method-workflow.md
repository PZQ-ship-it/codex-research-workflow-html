# Algorithm And Method Paper Workflow

Use this reference for papers where the main contribution is an algorithm, model, architecture, optimization method, benchmark result, system, dataset, or implementation pipeline. The output should be a self-contained compressed reading of the paper, not a guide to which sections to inspect.

## Coverage Standard

Before writing, create a coverage ledger for:

- problem setup and assumptions;
- method components, modules, objectives, algorithms, and data flow;
- theorem/proof sections if present;
- datasets, baselines, metrics, and implementation setup;
- main results, ablations, qualitative examples, and failure cases;
- limitations and reproducibility details.

Cover every central item in the HTML as `full` or `condensed`. Use `figure/table only` only when the visual itself is the clearest representation and add prose explaining it. Record omissions and uncertainty in the manifest.

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

- `Paper In One Page`: thesis, task, contribution, and main result;
- `Problem`: task, assumptions, inputs, outputs, constraints, and why the problem matters;
- `Prior Gap`: what previous work could not do and how the paper positions itself;
- `Method At A Glance`: method intuition plus overview figure;
- `Core Mechanics`: algorithm steps, model modules, objective, data flow, pseudo-code, and how inputs become outputs;
- `Novelty Claims`: what is actually new, separated from normal engineering choices;
- `Experiments`: datasets, metrics, baselines, setup, hyperparameters if provided, and what each experiment tests;
- `Results`: main tables/plots, actual trends or numbers when reliably extracted, ablations, sensitivity analyses, and statistical caveats;
- `Limitations`: failure cases, assumptions, resource cost, external validity;
- `Implementation Notes`: dependencies, inputs, outputs, reproducibility hints, and likely missing details;
- `Coverage And Manual Checks`: uncertain extraction, omitted details, and result values that need PDF verification.

Each section must include content, not just source page references.

## Figure Priorities

Prefer these visuals:

- architecture diagram;
- pipeline or flowchart;
- algorithm pseudo-code;
- main result table or plot;
- ablation figure;
- qualitative examples or failure cases;
- dataset construction diagram.

For each figure or table, explain what the reader should learn from it. Do not rely on the caption alone.

## Reading Heuristics

- Compare the method overview figure against the claimed novelty before writing the summary.
- Keep datasets and metrics close to the result claims.
- Mark result numbers as `needs manual check` if table extraction is uncertain.
- Separate "paper claims" from "your interpretation".
- Preserve formulas or pseudo-code as images or page references if extraction is unreliable.
- If formulas or pseudo-code are preserved as images, add a plain-language explanation of each variable, step, or block that is central to understanding the method.
- If benchmark values are reliably extractable, include the main numbers or relative rankings. If not, summarize the direction of results and mark the exact values as `needs manual check`.
- If a paper has multiple experiments, explain the role of each experiment rather than listing dataset names only.
