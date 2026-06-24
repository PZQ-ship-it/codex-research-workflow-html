---
name: ra-mainline-literature-orchestrator
description: Orchestrate HKUST(GZ) RA academic-fit mainline rankings into batched literature-collection work orders. Use when Codex has a mainline-ranking.md or mainline-ranking-scored.json table and needs to split ranked directions across subagents to find, verify, and download open-access field surveys plus 1-2 representative papers per teacher/direction into the separate D:\hkust-gz-ra-paper-reading artifact repository, while keeping D:\todo as planning/status only.
---

# RA Mainline Literature Orchestrator

Turn a direction-ranking table into bounded worker jobs for RA literature collection. This skill does not replace paper reading skills; it coordinates source-grounded collection so later agents can build HTML digests, glossaries, survey maps, and minimal reproduction plans.

## Hard Boundaries

- Treat `D:\todo\projects\hkust-gz-ra-academic-fit` as the planning source of truth.
- Store PDFs, source manifests, notes, and downstream reading artifacts in `D:\hkust-gz-ra-paper-reading`, not in `D:\todo`.
- Download only open-access or user-authorized PDFs. Do not use Sci-Hub-like sources, paywall bypasses, private cloud mirrors, cookies, tokens, or login-gated material.
- If no lawful PDF is found, write the metadata and failure reason instead of forcing a download.
- Keep each worker scope small: one ranked direction per worker by default; batch several workers only for scheduling.

## Default Inputs

- Ranking markdown: `D:\todo\projects\hkust-gz-ra-academic-fit\direction-map\mainline-ranking.md`
- Preferred ranking JSON: `D:\todo\projects\hkust-gz-ra-academic-fit\direction-map\mainline-ranking-scored.json`
- Direction maps: `D:\todo\projects\hkust-gz-ra-academic-fit\direction-map\*.md`
- Artifact repo: `D:\hkust-gz-ra-paper-reading`

## Workflow

1. Read the ranking table and project map.
   - Prefer `mainline-ranking-scored.json` when present because it carries professor/source mappings.
   - Use `mainline-ranking.md` for recommendations, reading order, and human-facing rank labels.
2. Generate a run plan.
   - Run `scripts/make_literature_work_orders.py` to create job JSON files, batch markdown files, a dispatcher, and a status file under the artifact repo.
   - Use `--max-rank` for staged runs. If the user says to cover the whole table, omit it.
3. Dispatch subagents in batches.
   - Use one subagent per job when possible.
   - Pass the job JSON path and `references/worker-contract.md` to each worker.
   - Instruct workers to use `paper-review-source-intel` for paper/source validation and `anysearch` for live discovery when needed.
4. Require each worker to save outputs in the target artifact repo.
   - PDF files go under `papers/mainline-literature/<rank-slug>/`.
   - Source manifests and summaries go under `sources/mainline-literature/<rank-slug>/`.
   - Do not put bulky artifacts or PDFs under `D:\todo`.
5. Merge results after each batch.
   - Check each job manifest for selected survey, selected representative papers, rejected candidates, and missing downloads.
   - Update the run status. Only then decide whether to launch the next batch.

## Work Order Command

From any workspace:

```powershell
python D:\工作流优化\codex-research-workflow-html\skills\ra-mainline-literature-orchestrator\scripts\make_literature_work_orders.py `
  --ranking D:\todo\projects\hkust-gz-ra-academic-fit\direction-map\mainline-ranking.md `
  --target-repo D:\hkust-gz-ra-paper-reading `
  --batch-size 4
```

Useful options:

- `--ranking-json <path>`: explicitly pass `mainline-ranking-scored.json`.
- `--max-rank 10`: generate jobs only for the top N ranked directions.
- `--run-id <id>`: make a deterministic run folder name.
- `--overwrite`: replace an existing run folder with the same run id.

## Worker Prompt Shape

Use this shape when launching each subagent:

```text
Use $paper-review-source-intel and $anysearch as needed.
Follow the worker contract at <skill>/references/worker-contract.md.
Process this RA mainline literature job: <target-repo>/sources/mainline-literature-runs/<run-id>/jobs/rank-XX-<slug>.json.
Write all PDFs, manifests, and summaries only under D:\hkust-gz-ra-paper-reading.
Do not bypass paywalls. If an open PDF is unavailable, record metadata and the reason.
```

## Output Contract

Each completed job should leave:

- `papers/mainline-literature/<rank-slug>/surveys/*.pdf` when an open survey PDF exists.
- `papers/mainline-literature/<rank-slug>/teachers/<teacher-slug>/*.pdf` for 1-2 open representative papers per teacher when available.
- `sources/mainline-literature/<rank-slug>/manifest.json` with selected and rejected candidates.
- `sources/mainline-literature/<rank-slug>/summary.md` explaining why the survey and representative papers were selected.

After PDFs exist, use `paper-pdf-to-structured-html` and `paper-term-glossary-builder` in separate downstream passes. Do not make this orchestrator perform PDF-to-HTML or glossary work.

## References

Read `references/worker-contract.md` before dispatching or acting as a worker.
