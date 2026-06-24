Use $codex-exploration-loop to explore one branch.

Return only a JSON object matching round-result.schema.json.

Question:
<question>

Round:
<round>

Branch:
<branch-id>

Hypothesis:
<hypothesis>

Probe:
<probe>

Workspace:
<workspace>

Budget:
<minutes> minutes

Allowed:
<allowed-actions>

Forbidden:
credentials, paid calls, commit/push, destructive cleanup outside scratch, merge.

Do:
- run the smallest useful probe;
- cite evidence paths or URLs;
- score novelty, promise, evidence, risk, and cost from 0 to 5;
- write a delta-oriented reflection;
- choose one decision: continue, pivot, branch, prune, promote, or stop.
- include proposed_branches only when decision is branch and the branch should split further.

Do not:
- edit frontier.json, ledger.jsonl, runner state, or beam-selection artifacts;
- decide the overall beam;
- continue into sibling branches outside this assignment.
