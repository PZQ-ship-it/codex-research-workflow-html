# Source Routing

Use the lightest official public source that can satisfy the request. The default closure must work without required MCP servers, paid services, private tokens, or login-gated data. This skill is about evidence routing and normalization; it does not vendor third-party crawlers.

## Priority Matrix

| Need | Primary route | Secondary route | Notes |
|---|---|---|---|
| GitHub repo/code evidence | GitHub public REST/GraphQL, local clone | optional GitHub MCP | Best for repo tree, files, search, commits, issues, PRs, releases, Actions, security alerts. |
| GitHub org/project activity | GitHub public REST/GraphQL | optional GitHub MCP/API token | Use read-only public access unless the user explicitly authorizes a token. |
| HF model/dataset/Space discovery | HF public API, Dataset Viewer, `hf`, `huggingface_hub` | optional HF MCP | Supports model/dataset/Space/paper search and repo details. |
| HF dataset rows and SQL-like inspection | Dataset Viewer REST API / HF `huggingface-datasets` skill | `datasets` library | Use for configs, splits, row pagination, filtering, and parquet inspection. |
| HF benchmark leaderboards | HF leaderboard API | `huggingface_hub.HfApi.get_dataset_leaderboard` | Official benchmark datasets expose ranked scores. |
| Per-model eval results | `model_info(..., expand=["evalResults"])` | model card `.eval_results/*.yaml` | Good for model-centric benchmark views. |
| Kaggle competitions/datasets/models/benchmarks | public Kaggle pages | Kaggle API, official MCP, `kaggle-mcp` | Authenticated downloads/discussions are optional and require approval. |
| OpenML data/tasks/runs | OpenML Python/API | OpenML website exports | Strong for classic ML benchmark suites and reproducible runs. |
| LiveBench | LiveBench official repo and HF datasets | livebench.ai site | Data and leaderboard assets are available through repo/HF. |
| Arena/LMArena | Arena official site | daily JSON snapshot repos/APIs | No official public API was found; mark snapshots as supplemental. |
| Papers with Code linkage | PWC historical archive | CodeSOTA-like replacement pages | Treat old PWC as historical/archive, not live truth. |
| Unified benchmark summaries | official benchmark repos first | ALL-Bench/LLM Stats/third-party aggregators | Aggregators must retain per-score provenance. |

## GitHub

Use GitHub public REST/GraphQL and local clones by default when the user asks for:

- repo metadata, language mix, stars/forks, releases, license;
- source tree, selected files, README, docs, examples;
- code search by symbol, path, language, or query;
- issues, PRs, discussions, commits, contributors;
- GitHub Actions runs/logs, dependency/security alerts;
- implementation evidence for a paper/model/benchmark.

GitHub MCP is an optional convenience layer when already configured or when richer authenticated access is explicitly approved. Keep token scopes minimal. Avoid write tools unless the user explicitly asks to create/update issues, PRs, comments, releases, or workflows.

## Hugging Face

Use HF public API, Dataset Viewer, `hf` CLI, `huggingface_hub`, or HF skills when the user asks for:

- model/dataset/Space search and details;
- model card or dataset card content;
- downloads, tags, library/task metadata, files, safetensors/parameter metadata;
- linked papers, Spaces, datasets, or model derivatives;
- benchmark eval results stored in `.eval_results/` or model card metadata;
- official benchmark dataset leaderboards.

For benchmark datasets:

- discover official benchmarks with `GET https://huggingface.co/api/datasets?filter=benchmark:official`;
- fetch rankings with `GET https://huggingface.co/api/datasets/{dataset_id}/leaderboard`;
- use `HfApi.get_dataset_leaderboard(dataset_id)` when a Python environment is available;
- use `model_info(model_id, expand=["evalResults"])` for per-model score views.

## Kaggle

Use public Kaggle pages first for competitions, datasets, notebooks/kernels, models, and benchmark leaderboards. Use Kaggle API, official MCP, or third-party `kaggle-mcp` only when the user explicitly accepts authenticated setup, download terms, or discussion/write-up access.

Treat Kaggle tokens as private. Do not commit `kaggle.json`, `KAGGLE_API_TOKEN`, or downloaded restricted competition data.

## OpenML

Use OpenML for classic ML datasets and reproducible benchmark evidence:

- datasets: metadata, features, qualities, licenses;
- tasks: task type, target, train/test split;
- flows: models/pipelines;
- runs/evaluations: reproducible results and metrics;
- benchmark suites: curated task collections.

Prefer `openml-python` for automation and record task/run IDs in normalized rows.

## Benchmark-Specific Sources

For modern AI benchmark claims, use benchmark-specific official repos/datasets before broad aggregators:

- LiveBench: official GitHub repo, HF datasets, downloadable leaderboard/results scripts.
- SWE-bench: official HF datasets and leaderboards.
- GAIA: official HF Space/dataset pages when available.
- LiveCodeBench/BigCodeBench: official sites/repos.
- Arena/LMArena: official site first; daily snapshot repos only as supplemental because no official public API was found.

## Papers with Code and CodeSOTA

The historical Papers with Code API/pages are not a reliable live source. Use:

- PWC archive for historical paper-code-benchmark linkage;
- CodeSOTA-like replacement pages for live SOTA discovery only when official benchmark data is unavailable;
- GitHub/HF links and benchmark official repos to verify individual scores.

## Synthesis Policy

Separate evidence layers:

- source code evidence: repository, commit, release, issue/PR, license;
- Hub evidence: model/dataset/Space metadata, card, files, eval results;
- benchmark evidence: task, split, metric, version, score, rank, source, verification status;
- derived analysis: model comparison, trend summary, capability routing, implementation readiness.

In reports, label derived analysis clearly and link it back to normalized row IDs.
