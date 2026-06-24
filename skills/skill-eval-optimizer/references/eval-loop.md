# Skill Eval Loop

This reference gives a compact, repeatable loop for testing and improving Codex skills.

## Eval Pack Layout

Recommended layout outside the skill under review:

```text
evals/
  skill-eval/
    <skill-name>/
      prompts.csv
      style-rubric.schema.json
      artifacts/
        case-01.jsonl
        case-01.style.json
```

`prompts.csv` should include:

```csv
id,should_trigger,prompt,expected_artifacts,notes
direct-01,true,"Use $skill-name to ...",,
implicit-01,true,"Please ...",,
negative-01,false,"Adjacent task that should not use the skill",,
```

## Goal Mode Layout

When an eval or optimization run uses native goal mode, add a status file beside the eval pack:

```text
evals/
  skill-eval/
    <skill-name>/
      goal-status.md
      prompts.csv
      style-rubric.schema.json
      artifacts/
```

`goal-status.md` should stay short and current:

```markdown
# Goal Status: <skill-name>

- Objective:
- Target skill path:
- Current phase: static | eval-pack | before-run | diagnosis | patch | after-run | report | blocked | complete
- Eval cases:
- Last validation command:
- Evidence artifacts:
- Remaining risks:
- Next action:
- Blockers:
```

Use this file as coordination evidence, not as proof of success. The goal is complete only when the requested commands, traces, artifacts, and final report exist.

Run the lightweight goal contract check before behavior evals:

```powershell
python skills\skill-eval-optimizer\scripts\skill_eval_harness.py goal-check <skill-dir>
```

## Run Pattern

Use isolated workspaces. If the target skill writes files, run in a scratch directory or disposable branch.

```powershell
codex exec --json --full-auto "Use $<skill-name> to <task>" > evals\skill-eval\<skill-name>\artifacts\case-01.jsonl
```

For read-only style or policy checks, reduce permissions where practical.

## Deterministic Checks

Start with checks that do not require model judgment:

- Did the trace contain a required command?
- Did an expected file appear?
- Did command count stay below a sane limit?
- Did token use jump unexpectedly?
- Did the run leave unrelated files?
- Did the final artifact pass a build, lint, render, or smoke test?

Example:

```powershell
python skills\skill-eval-optimizer\scripts\skill_eval_harness.py summarize-trace `
  evals\skill-eval\<skill-name>\artifacts\case-01.jsonl `
  --require-command quick_validate.py `
  --max-commands 20
```

## Rubric Checks

Use rubric checks for quality that file existence cannot capture: clarity, output contract, citation style, visual quality, or whether the skill followed the intended route.

Use `--output-schema` so the result is machine-readable:

```powershell
codex exec `
  "Evaluate the artifact against the rubric in evals\skill-eval\<skill-name>\style-rubric.schema.json. Return only schema-compliant JSON." `
  --output-schema evals\skill-eval\<skill-name>\style-rubric.schema.json `
  -o evals\skill-eval\<skill-name>\artifacts\case-01.style.json
```

## Before/After Comparison

When optimizing a skill, keep before and after traces:

```text
artifacts/
  before/
    case-01.jsonl
  after/
    case-01.jsonl
```

Compare:

- trigger correctness
- required step completion
- goal-mode state updates, completion criteria, blocked criteria, and human gates when relevant
- output contract stability
- command count
- token use
- manual/rubric grade
- cleanup status

Only call a change an improvement when the target failure improves without introducing a worse regression.

## Goal-Mode Regression Cases

For a skill that claims goal-mode support, include at least two cases when practical:

- positive goal case: a bounded objective with a status artifact and verifiable completion criteria;
- blocked goal case: missing credentials, unavailable runtime, or an explicit human gate that must stop instead of being bypassed.

The trace should show that Codex updates status, keeps the goal honest, and does not mark complete from intention alone.
