# Agent-Xray Notes

Agent-Xray is a local-first trace diagnosis tool for AI agents. It reconstructs what an agent saw at each decision point and helps debug behavioral failures that do not produce normal stack traces.

Source copy:

```text
D:\工作流优化\codex-research-workflow-html\tmp\agent-xray-source-20260602\Agent-Xray
```

Upstream repository:

```text
https://github.com/GeeIHadAGoodTime/Agent-Xray
```

## Key Concepts

- Structural grade is not answer correctness. It measures execution structure: tool diversity, loop resistance, error rate, completion signals, and similar signals.
- Decision surface means the relevant prompt context, tool set, conversation history, page/browser state, model reasoning, corrections, and context pressure available at a step.
- Root cause classification should point to the subsystem to fix: prompt, tool, retrieval, router, state, memory, evaluator, permissions, or workflow.
- The improvement flywheel is:

```text
triage -> identify worst failure -> surface decision point -> fix root cause -> controlled check -> compare runs
```

## Supported Inputs

Agent-Xray supports:

- Generic JSONL
- OpenAI traces
- Anthropic traces
- LangChain / LangGraph traces
- CrewAI traces
- OpenTelemetry GenAI spans

Use `agent-xray format-detect <file>` before assuming a format.

## Useful Commands

```powershell
agent-xray triage <trace-dir>
agent-xray analyze <trace-dir>
agent-xray grade <trace-dir>
agent-xray root-cause <trace-dir>
agent-xray inspect <task-id> <trace-dir>
agent-xray surface <task-id> --log-dir <trace-dir>
agent-xray compare <traces-before> <traces-after>
agent-xray flywheel <trace-dir>
agent-xray completeness <trace-dir>
agent-xray report <trace-dir>
```

## How To Use Inside This Skill

1. Use Agent-Xray to produce structural signals when installed.
2. Read generated output as evidence, not as final truth.
3. Combine structural diagnosis with product-specific success criteria.
4. Convert findings into a fix plan and verification plan.
5. Avoid optimizing to generic grades alone; custom rules or task-bank success criteria are required before serious optimization.

## Fallback

If Agent-Xray is unavailable, perform a manual analysis using:

- step count and loops
- repeated tool failures
- missing completion signals
- retrieval miss/conflict patterns
- output contract violations
- latency/cost spikes
- human correction patterns
- evaluator false positives/false negatives

