# Logging Schema

Use this schema when existing traces are too thin, or when designing an eval loop for future agent runs.

## Minimum Event Fields

Each event should include:

```json
{
  "task_id": "stable task id",
  "run_id": "stable run id",
  "step": 1,
  "timestamp": "ISO-8601",
  "event_type": "user|model|tool_call|tool_result|retrieval|route|eval|handoff|final",
  "user_goal": "short goal or task text",
  "agent_name": "agent or specialist name",
  "model": "model name if known",
  "system_prompt_version": "version or hash",
  "tool_name": "tool name when applicable",
  "tool_input_summary": "redacted summary",
  "tool_result_summary": "redacted summary",
  "retrieval_query": "query when applicable",
  "retrieval_sources": ["source ids"],
  "route": "selected route when applicable",
  "status": "success|warning|error|blocked",
  "error": "redacted error if any",
  "latency_ms": 0,
  "tokens": {
    "input": 0,
    "output": 0
  },
  "final_answer_summary": "redacted summary when applicable",
  "eval": {
    "passed": true,
    "score": 0.0,
    "rubric_version": "v1"
  }
}
```

## Recommended Run-Level Fields

```json
{
  "run_id": "stable run id",
  "task_id": "stable task id",
  "scenario": "domain scenario",
  "input": "redacted user input",
  "expected_behavior": "success criteria",
  "final_status": "success|failed|partial|blocked",
  "human_correction": "redacted correction if any",
  "known_labels": ["hallucination", "routing_error"]
}
```

## Redaction Rules

- Never log raw API keys, tokens, cookies, passwords, private credentials, or personal identifiers unless the system has an approved secure logging policy.
- Prefer summaries or stable hashes for sensitive values.
- Keep enough detail to explain decisions: tool names, source ids, route ids, validation outcomes, and error categories.

## Eval Loop

For every optimization campaign, keep:

- baseline traces
- candidate traces
- unchanged task bank
- rubric version
- prompt/tool schema version
- before/after metric table

Never compare runs scored under different rubric versions without labeling evaluator drift.

