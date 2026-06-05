# Diagnostic Rubric

Use this file when diagnosing a scenario-specific agent from logs, traces, eval outputs, prompts, or failure reports.

## Scoring Dimensions

Use `pass`, `warning`, `fail`, or `unknown`.

| Dimension | What To Check | Common Evidence |
| --- | --- | --- |
| Task completion | Did the run reach a valid completion signal? | final status, evaluator pass, user correction |
| Answer correctness | Did output satisfy scenario criteria? | ground-truth eval, task-bank expected answer |
| Tool choice | Did the agent use the right tools at the right time? | tool sequence, skipped required tool, wrong tool |
| Tool reliability | Did tools fail or return malformed data? | error lines, retries, schema errors |
| Retrieval quality | Were sources relevant, sufficient, fresh, and cited when needed? | retrieved docs, scores, citations, evidence gaps |
| Loop resistance | Did the agent repeat actions without new information? | repeated tool calls, identical queries, retry count |
| State integrity | Did state, memory, or context stay consistent? | stale memory, wrong user/session, overwritten fields |
| Routing | Did the request go to the right specialist/path? | classifier output, route trace, fallback path |
| Output contract | Did output match required schema/tone/format? | JSON parse errors, missing fields, long prose |
| Safety/privacy | Did the run avoid unsafe actions and secret exposure? | redaction, approval gates, PII handling |
| Latency/cost | Was execution within budget? | duration, model calls, tokens, fan-out |
| Observability | Is there enough trace data to debug the run? | missing tool inputs/results, no task id, no timestamps |

## Root-Cause Taxonomy

Rank likely causes by evidence strength.

| Cause | Symptoms | Fix Pattern |
| --- | --- | --- |
| Ambiguous system prompt | inconsistent decisions, missing non-goals, weak role | rewrite role/scope/task flow |
| Missing success criteria | agent stops early or optimizes wrong thing | add measurable completion gates |
| Weak tool description | wrong tool, skipped tool, bad arguments | rewrite tool descriptions, add preconditions/examples |
| Tool schema mismatch | validation errors, malformed calls | tighten schema, add examples and error policy |
| Retrieval weakness | irrelevant docs, no answer despite existing source | hybrid retrieval, reranking, query rewrite, evidence policy |
| Router overlap | wrong specialist, oscillation between routes | mutually exclusive routing rules, confidence threshold |
| Loop budget missing | repeated calls, no convergence | retry caps, novelty checks, early-exit rule |
| Memory/state bug | stale or cross-user facts | state validation, memory TTL, source labels |
| Prompt injection weakness | follows untrusted content as instructions | instruction/data separation and source trust policy |
| Output contract underspecified | unstable JSON or missing fields | schema-first prompt, validation and repair pass |
| Evaluator drift | eval says pass while humans disagree | version eval rubrics, add counterexamples, audit judge |
| Logging gap | cannot explain failure | add trace schema fields and event IDs |

## Optimization Mapping

| Finding | Optimize |
| --- | --- |
| Hallucination with weak evidence | retrieval policy, citation rule, uncertainty language |
| Tool misuse | tool descriptions, preconditions, argument examples, allowed action set |
| Long loop | max iterations, no-progress detector, fallback/handoff gate |
| Slow path | routing, caching, parallel independent tools, cheaper model for low-risk steps |
| Bad routing | classifier labels, disjoint categories, confidence fallback |
| Output format errors | structured output schema, validator, repair prompt |
| Unsafe action | approval gate, sandbox policy, irreversible-action rule |
| Repeated human correction | add few-shot example and explicit rule to system prompt |

## Confidence Labels

- High: direct trace evidence and repeated pattern.
- Medium: direct evidence in one run or indirect pattern across runs.
- Low: plausible hypothesis but missing key artifact.

Do not present low-confidence hypotheses as confirmed facts.

