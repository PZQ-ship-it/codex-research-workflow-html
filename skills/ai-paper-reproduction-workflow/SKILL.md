---
name: ai-paper-reproduction-workflow
description: Coordinate an end-to-end AI/ML paper reproduction through narrow atomic skills without bundling their implementations. Use when the user asks to reproduce a specific AI paper, validate paper results, rerun a benchmark, build a reproduction package, or go from paper/PDF/repo/dataset to claim map, source lock, environment smoke, experiment run, result audit, and final report.
---

# AI Paper Reproduction Workflow

## Overview

Use this as a thin coordinator. It should not copy the content of the atomic skills into context. Trigger the next skill only when its artifact is needed.

Read `references/stage-contract.md` before starting a substantial reproduction run.

## Stage Flow

1. Prepare paper text:
   - If the input is a PDF, use `$paper-pdf-to-structured-html` or another PDF extraction route.
   - If the user already provided notes, use them directly.
2. Map claims with `$paper-repro-claim-map`.
3. Lock sources with `$paper-repro-source-lock`.
   - Use `$paper-review-source-intel` for official paper/review/proceedings context.
   - Use `$code-model-benchmark-intel` for GitHub, Hugging Face, Kaggle, OpenML, benchmark, model, dataset, or leaderboard evidence.
   - Use `$external-api-onboarding` only when the chosen source route requires API keys, OAuth, or MCP login.
4. Smoke test environment with `$paper-repro-env-smoke`.
5. Run minimal reproduction:
   - For small local runs, execute the selected commands with logs.
   - For large or resumable benchmark runs, use `$resilient-llm-benchmark`.
6. Audit results with `$paper-repro-result-audit`.
7. Sync outputs into reports/figures only if requested:
   - `$research-fact-source-sync` for documents and claim-source sync.
   - `$thesis-figure-pipeline` for reproducible plots from result tables.
   - `$evidence-synthesis-docs` for evidence-backed synthesis.

## Directory Contract

For nontrivial runs, create or reuse:

```text
repro/<paper-slug>/
  inputs/
  claim_map.md
  claim_map.json
  source_lock.md
  source_lock.json
  env_smoke/
    env_smoke_plan.json
    env_smoke_report.md
    logs/
  runs/
    manifest.json
    results/
    logs/
  result_audit.md
  result_audit.json
  final_report.md
```

## Stop Gates

Stop and report before proceeding when:

- no official or trustworthy source can be locked;
- the required dataset/model is gated and the user has not authorized access;
- the smoke test fails with a blocker that would make further runs meaningless;
- full reproduction requires substantial compute, paid APIs, or long-running jobs;
- the user asked for a plan or audit only.

## Minimal Fallbacks

If an atomic skill is unavailable:

- For claim mapping, create the `claim_map` sections listed in `$paper-repro-claim-map` manually.
- For source locking, create the `source_lock` sections manually and mark every source priority.
- For environment smoke, run only inspection and cheap commands, preserving logs.
- For result audit, issue claim-level verdicts and avoid overall success claims.

## Guardrails

- Keep the workflow closed by artifacts, not by bundling dependencies.
- Do not load all related skills at once.
- Do not replace official artifacts with convenient third-party artifacts without marking them.
- Do not run full training as a first action.
- Do not expose secrets in manifests, logs, final answers, or repo files.

## Resources

- `references/stage-contract.md`: exact per-stage inputs, outputs, and handoff rules.
