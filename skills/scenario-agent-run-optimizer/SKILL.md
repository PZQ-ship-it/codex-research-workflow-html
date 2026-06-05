---
name: scenario-agent-run-optimizer
description: Analyze and optimize a scenario-specific AI agent from runtime logs, traces, eval outputs, system prompts, tool schemas, or failure reports. Use when the user asks Codex to inspect another agent system's behavior, diagnose agent failures, evaluate runs, compare before/after agent traces, find root causes, improve system prompts or tool policies from evidence, or design an optimization loop for non-code or domain-specific agents.
---
# Scenario Agent Run Optimizer

Diagnose another agent system from evidence, then propose concrete optimizations. This skill is for scenario-specific agents, not only coding agents.

## Core Promise

Turn these inputs:

- runtime logs, traces, JSONL events, OpenTelemetry spans, LangChain/LangGraph traces, OpenAI/Anthropic call logs, CrewAI logs, screenshots, eval outputs, failure reports
- current system prompt, tool definitions, routing rules, retrieval policy, memory policy, guardrails, escalation rules
- expected task success criteria and known failures

into:

- an evidence-backed run health report
- root-cause hypotheses tied to trace evidence
- specific optimization proposals for prompt, tools, retrieval, routing, state, evals, logging, and human handoff
- an A/B or replay plan to test whether the fix improves the agent

Do not invent logs, metrics, trace fields, or outcomes. If evidence is missing, state the smallest artifact needed next.

## Quick Workflow

1. Inventory inputs.
   - Identify agent type, scenario, runtime, log format, trace files, prompt files, eval files, and success criteria.
   - Separate facts from assumptions.
   - If paths are provided, read only relevant files. Avoid secrets and private credentials.
2. Detect analysis path.
   - If `agent-xray` is available and trace format is compatible, use it for structural triage.
   - If not available, perform a manual evidence-based analysis using `references/diagnostic-rubric.md`.
   - For raw JSONL/JSON/CSV logs, use deterministic parsing where practical.
3. Normalize each run.
   - Task id, user goal, final outcome, steps, tools, retrieval calls, model calls, errors, retries, latency, cost/tokens if available, final answer, evaluator result, human corrections.
4. Score execution structure.
   - completion signal, loop resistance, tool choice, error handling, retrieval quality, output contract stability, latency/cost, escalation behavior, safety/privacy behavior.
   - Make scoring scale explicit. Distinguish structural quality from answer correctness.
5. Diagnose root causes.
   - Use evidence: prompt snippet, tool call, retrieval miss, state transition, evaluator result, or error line.
   - Classify likely causes: prompt ambiguity, missing success criteria, tool schema mismatch, retrieval weakness, router overlap, state leak, memory staleness, insufficient logging, evaluator drift, unsafe action policy, missing fallback.
6. Propose optimizations.
   - Rank fixes by expected impact and risk.
   - For prompt fixes, produce a patchable system-prompt section, not vague advice.
   - For tool fixes, propose tool schema/description/precondition/postcondition changes.
   - For retrieval fixes, propose query, chunking, reranking, citation, and evidence-gap policies.
   - For orchestration fixes, propose routing, retry budgets, loop caps, state validation, and human handoff gates.
7. Design verification.
   - Create an A/B, replay, task-bank, or golden-run plan.
   - Define metrics and pass/fail gates before recommending adoption.
   - If possible, produce a small eval table from the available runs.

## Agent-Xray Integration

Agent-Xray source was downloaded for reference at:

```text
D:\工作流优化\codex-research-workflow-html\tmp\agent-xray-source-20260602\Agent-Xray
```

Read `references/agent-xray-notes.md` when using Agent-Xray concepts or commands.

Use Agent-Xray when:

- the user provides trace directories or JSONL logs
- the run format is OpenAI, Anthropic, LangChain, CrewAI, OpenTelemetry, or generic JSONL
- structural grading, root-cause classification, decision-surface reconstruction, or before/after comparison would help

Suggested commands when `agent-xray` is installed:

```powershell
agent-xray format-detect <trace-file>
agent-xray triage <trace-dir>
agent-xray grade <trace-dir>
agent-xray root-cause <trace-dir>
agent-xray inspect <task-id> <trace-dir>
agent-xray compare <before-traces> <after-traces>
agent-xray flywheel <trace-dir>
```

If `agent-xray` is not installed, do not stop. Use the manual rubric and tell the user that Agent-Xray would add automated structural grading if installed.

## Output Shape

Use this structure unless the user requests a different format:

```text
Summary
- Agent/system inspected:
- Evidence used:
- Main diagnosis:
- Highest-impact fix:

Run Health
| Dimension | Status | Evidence | Risk |

Root Causes
| Rank | Cause | Evidence | Confidence | Fix |

Optimization Plan
1. Prompt/system-instruction changes
2. Tool/schema changes
3. Retrieval/knowledge changes
4. Routing/state/orchestration changes
5. Eval/logging changes

Verification Plan
| Test | Input/run | Metric | Pass gate |

Open Evidence Gaps
- ...
```

For a prompt edit, include a clearly copyable section:

```text
System Prompt Patch
<section name>
...
```

For logs with insufficient detail, output a minimal logging schema the target agent should emit next.

## Evidence Rules

- Cite local file paths and line numbers when available.
- Quote only short excerpts. Prefer paraphrase and line references.
- Do not expose secrets, API keys, tokens, passwords, cookies, or private user data.
- If a log may contain sensitive data, summarize patterns and redact values.
- Treat model reasoning traces as sensitive unless the user explicitly asks to inspect them and they are local artifacts.

## References

Load only what is needed:

- `references/diagnostic-rubric.md`: manual scoring, root-cause taxonomy, optimization mapping.
- `references/agent-xray-notes.md`: Agent-Xray concepts, commands, and when to use them.
- `references/logging-schema.md`: recommended trace schema for future runs and eval loops.

