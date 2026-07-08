# Selection Heuristics

Use this reference when ranking node papers.

## Reading-Path Inspiration

`Reading-Path-Generation` / SurveyBank is a useful conceptual prior, but not a runnable Codex skill dependency. The public repository inspected on 2026-07-08 contains README files plus two dataset JSON files, not an executable RePaGer pipeline.

Portable ideas:

- treat survey references as layered signals rather than a flat bibliography;
- distinguish broad mention (`once`) from stronger repeated/deeper labels (`twice`, `triple`);
- infer a reading path instead of a search-result list;
- keep the path small enough for a newcomer to act on.

For current work, approximate this without depending on SurveyBank:

- `once-like`: paper is mentioned once or appears in a broad related-work list;
- `twice-like`: paper appears in a taxonomy branch plus a table/figure/history paragraph;
- `triple-like`: paper appears in multiple structural places, defines a benchmark/task, or is reused as a baseline across method families.

Never treat this depth heuristic as proof of importance by itself. Combine it with purpose fit.

## Scoring Dimensions

Use a light qualitative score, not a fake numeric precision:

- `survey_depth`: once-like / twice-like / triple-like.
- `node_role_strength`: weak / medium / strong.
- `purpose_fit`: learning / contact-fit / repro-scout relevance.
- `source_lock`: canonical / secondary-only / needs-check.
- `readability`: easy / medium / hard.
- `code_data_readiness`: ready / partial / unknown / not-needed.
- `professor_group_relevance`: direct / bridge / weak / unknown.

## Ranking Policy

For RA contact-group reading:

1. Prefer direct professor-group relevance when source-grounded.
2. Prefer a paper that explains a method family or task boundary over a paper that only adds incremental performance.
3. Prefer one readable anchor plus one method-turn or benchmark node, rather than three equally dense papers.
4. Use code/data readiness as a tie-breaker when minimal reproduction may follow.
5. Mark attractive but risky papers as `defer`, not `must-read`.

For survey-to-node conversion:

- Do not output every cited paper.
- Do not let citation count dominate if the user's task is contact material or first learning.
- Do not recommend a paper whose title/source cannot be locked unless explicitly labeled `needs-check`.
- Do not claim the paper fits the user's interest before a human confirms.

## External Pattern Borrowing

Useful patterns from external repositories:

- `research-units-pipeline-skills` / `research-brief`: compact snapshot, `core_set`, taxonomy, and "what to read first" are good shape constraints.
- `research-harness` / `literature-mapping`: cluster papers by problem/method/dataset/evaluation and identify baseline coverage.
- `Reading-Path-Generation`: reading path and reference-depth labels.

Borrow these as design patterns only unless the user explicitly asks to install those full systems.
