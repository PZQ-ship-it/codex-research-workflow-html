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
2. Select one branch and one concrete probe.
3. Start the round.
4. Execute the probe in the allowed workspace.
5. Finish the round with evidence, scores, reflection, and decision.
6. Stop or continue based on budget and frontier state.

Final output must list best leads, dead ends, artifacts, and recommended next lane.
