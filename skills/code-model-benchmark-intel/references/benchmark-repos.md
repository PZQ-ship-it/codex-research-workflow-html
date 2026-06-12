# Benchmark Repos

Use this list as a starting point for benchmark-specific source routing. Prefer official repos, official sites, and official HF datasets before aggregators. Clone only what the task needs and keep clones under `runtime/benchmark-repos/`.

## Curated Defaults

| Name | Primary URL | Kind | Notes |
|---|---|---|---|
| `swebench` | https://github.com/SWE-bench/SWE-bench | repo + HF datasets + official site | Real-world GitHub issue resolution benchmark. Use official site/HF datasets for leaderboards and splits. |
| `livebench` | https://github.com/livebench/livebench | repo + site + HF data | Contamination-limited LLM benchmark with official repo and livebench.ai site. |
| `livecodebench` | https://github.com/livecodebench/livecodebench | repo + site + HF org | Continuously updated code benchmark. Preserve time window and split in score rows. |
| `bigcodebench` | https://github.com/bigcode-project/bigcodebench | repo + site | Practical code-generation benchmark. Capture benchmark version and leaderboard mode. |

## HF-First Benchmark Datasets

Use Hugging Face public API/Dataset Viewer where available:

- `SWE-bench/SWE-bench`
- `SWE-bench/SWE-bench_Verified`
- `gaia-benchmark/GAIA`
- benchmark datasets discovered through `https://huggingface.co/api/datasets?filter=benchmark:official`

Some HF datasets are gated or have private test answers. Treat gated access as a blocker unless the user has authorized access and the task terms allow the read.

## Clone Policy

- Use `git clone --depth 1` for inspection by default.
- Record commit SHA, clone time, repo URL, and whether the repo is official.
- Do not run benchmark submissions, downloads, or evaluation jobs unless explicitly requested.
- Do not commit cloned repos or generated outputs.
- If a repo's leaderboard is generated from site data, scripts, or HF datasets, capture that upstream source separately rather than citing only the cloned code.

## Supplemental Sources

- Arena/LMArena pages or snapshot JSON should be marked `secondary` unless an official public API is confirmed for the exact data.
- Papers with Code archive and CodeSOTA-like pages should be marked `archive` or `fallback` for paper-code-benchmark linkage.
- Aggregators such as ALL-Bench or LLM Stats are useful for discovery, but every score must retain its original source URL and source priority.
