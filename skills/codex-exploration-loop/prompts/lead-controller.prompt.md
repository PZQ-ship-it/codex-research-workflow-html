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

Allowed:
<allowed-actions>

Forbidden without explicit user confirmation:
credentials, paid calls, destructive edits, commit/push, merge, production changes.

Loop:
1. Read brief.md, frontier.json, and recent ledger records.
2. Decide whether this should be a single-branch round or a Tree-of-Thoughts fanout layer.
3. For a single branch: select one branch, start the round, execute one concrete probe, and finish the round.
4. For fanout: create sibling branches, dispatch independent branch workers or subagents, collect all sibling results, then run beam selection.
5. Do not select a beam before the sibling layer has been collected or explicitly marked failed/aborted.
6. Stop or continue based on budget and frontier state.

Final output must list best leads, dead ends, artifacts, and recommended next lane.
