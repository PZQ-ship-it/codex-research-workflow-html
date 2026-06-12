# AI Paper Reproduction Stage Contract

This workflow is closed by artifacts, not by bundling every dependency into one large skill.

## Stage 0 - Intake

Inputs:

- paper PDF/URL/HTML digest;
- optional official repo, dataset path, model path, benchmark target;
- requested scope and compute/auth constraints.

Outputs:

- `inputs/` with source pointers, not copied secrets.
- scope note in the run directory.

## Stage 1 - Claim Map

Skill:

- `$paper-repro-claim-map`

Outputs:

- `claim_map.md`
- optional `claim_map.json`

Pass only these artifacts into the next stage unless the source text is needed to resolve ambiguity.

## Stage 2 - Source Lock

Skill:

- `$paper-repro-source-lock`

Optional helpers:

- `$paper-review-source-intel` for proceedings/OpenReview/official paper context.
- `$code-model-benchmark-intel` for GitHub/HF/Kaggle/OpenML/benchmark/model/dataset evidence.
- `$external-api-onboarding` for user-approved API/MCP/OAuth setup.

Outputs:

- `source_lock.md`
- optional `source_lock.json`

## Stage 3 - Environment Smoke

Skill:

- `$paper-repro-env-smoke`

Outputs:

- `env_smoke/env_smoke_plan.json`
- `env_smoke/env_smoke_report.md`
- `env_smoke/logs/`

Proceed only if the verdict is `ready_for_minimal_reproduction` or `ready_with_minor_fixes`, unless the user asks for diagnosis only.

## Stage 4 - Run

Use direct commands for small runs. Use `$resilient-llm-benchmark` for long, sharded, API-backed, multi-model, multi-seed, or resumable runs.

Outputs:

- `runs/manifest.json`
- `runs/results/`
- `runs/logs/`

The manifest must include command, cwd, environment, source refs, seeds, and status without secrets.

## Stage 5 - Result Audit

Skill:

- `$paper-repro-result-audit`

Outputs:

- `result_audit.md`
- optional `result_audit.json`

## Stage 6 - Report or Sync

Optional downstream skills:

- `$research-fact-source-sync`
- `$thesis-figure-pipeline`
- `$evidence-synthesis-docs`

Outputs:

- `final_report.md`
- tables/figures only when requested.

## Closure Conditions

The reproduction loop is closed when one of these is true:

- requested claims are reproduced or audited with evidence;
- a claim is not testable and the missing artifact/detail is documented;
- environment/source/auth/license/resource blocker is documented with next action;
- user asked for a partial artifact only.
