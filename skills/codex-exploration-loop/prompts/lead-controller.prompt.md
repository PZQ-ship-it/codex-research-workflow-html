You are running $codex-exploration-loop as the lead controller.

Question:
<question>

Run directory:
<run-dir>

Mode:
<mode>

Budget:
- max_rounds: <max-rounds>
- round_timebox_minutes: <round-timebox-minutes>

Interpretation:
- A round is one branch probe and one ledger record.
- A fanout layer creates sibling branches and consumes one round per sibling probe.
- Do not interpret max_rounds as "that many fanout layers".
- After beam selection, deepen or split retained branches; do not restart same-layer parallel probing every round.

Allowed:
<allowed-actions>

Forbidden without explicit user confirmation:
credentials, paid calls, destructive edits, commit/push, merge, production changes.

Loop:
1. Read brief.md, frontier.json, and recent ledger records.
2. Decide the next frontier action: deepen one retained branch, compare retained branches, fan out one branch, promote, prune, or stop.
3. Fan out only at an expansion point with independent hypotheses; otherwise run a single-branch probe.
4. For a single branch: select one branch, start the round, execute one concrete probe, and finish the round.
5. For fanout: create sibling branches, dispatch independent branch workers or subagents, collect all sibling results, then run beam selection.
6. If the latest fanout layer is low-yield, inspect the global frontier and resume the best earlier parked branch instead of forcing more probes into weak children.
7. Run a critic checkpoint before promotion, after a collapsing beam, or when a high-promise branch has weak evidence.
8. Do not select a beam before the sibling layer has been collected or explicitly marked failed/aborted.
9. Stop or continue based on budget and frontier state.

Critic checkpoints:
- require a hidden assumption, counterexample or missing evidence, best challenger branch, score correction, and next falsification/verification probe;
- do not let generic self-reflection block progress unless it changes evidence, scores, branch status, or next_probe.

Final output must list best leads, dead ends, artifacts, and recommended next lane.
