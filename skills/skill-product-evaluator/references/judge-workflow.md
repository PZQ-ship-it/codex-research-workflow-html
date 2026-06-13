# Judge Workflow

Use this reference when invoking `skill_product_judge`.

## Judge Contract

The judge is read-only. It must not:

- edit files;
- run commands;
- install packages;
- browse or call APIs;
- expose secrets or raw private data;
- pass a case when deterministic checks show a hard failure.

## Evidence To Provide

Provide:

- target skill name and path;
- relevant `SKILL.md` excerpts or product promise summary;
- benchmark/source notes;
- case metadata from `product_cases.csv`;
- validation logs;
- final artifact excerpts or generated file paths;
- prior deterministic/style JSON;
- trace summaries, command summaries, exit codes, and stderr status;
- known limitations in the evidence.

Do not give only a narrative summary. The judge needs concrete excerpts or logs.

## Prompt Shape

Ask for one JSON block with:

- `overall_pass`;
- `overall_score`;
- `product_score`;
- `process_score`;
- `benchmark_alignment`;
- `dimension_scores`;
- `critical_failures`;
- `evidence`;
- `recommended_fixes`;
- `judge_confidence`;
- `case_scores`.

After the JSON block, allow at most five bullets for strongest evidence, benchmark fit, highest-impact fix, and residual risk.

## Fallback

If the custom `skill_product_judge` agent is unavailable after restart:

1. Record that the native judge was unavailable.
2. Validate the TOML if it exists.
3. Use a schema-limited `codex exec --output-schema` judge only as a fallback.
4. Mark the report as `judge_fallback_used: true`.

