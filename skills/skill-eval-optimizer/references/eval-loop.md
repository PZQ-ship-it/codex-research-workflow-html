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
- output contract stability
- command count
- token use
- manual/rubric grade
- cleanup status

Only call a change an improvement when the target failure improves without introducing a worse regression.
