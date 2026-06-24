# Automation And SDK Runner

This is v2 guidance. Do not require it for v1 or v1.5.

## Local Runner First

Use `scripts/explore_ledger.py run-plan` before adding an external controller.

The local runner is enough when:

- one Codex turn can own the run;
- deterministic smoke or replay mode is sufficient;
- the user can manually restart or resume later;
- the run only needs filesystem ledgers and `codex exec` workers.

## Thread Automation

Use when the same exploration thread should wake up on a schedule and preserve context.

Durable prompt should say:

- what question is being explored;
- where the run directory is;
- how many more rounds are allowed;
- what counts as an important finding;
- when to stop or ask the user.

## Standalone Or Project Automation

Use when each scheduled run should be independent or should span multiple projects.

Good for recurring scouting and monitoring. Less good for a single branch that needs accumulated context.

## SDK/App-Server

Use when a trusted external process must own:

- scheduling,
- approvals,
- streamed events,
- resume,
- UI,
- cross-run dashboards.

The controller should call official Codex surfaces. It should not implement its own model/tool loop unless there is a separate, explicit research goal.

## Escalation Rule

Escalate from local runner to Automations/SDK/app-server only for one of these needs:

- exact schedule or heartbeat;
- unattended overnight continuation;
- external approval UI;
- streamed event dashboard;
- cross-run analytics;
- resume/fork control outside the current Codex thread.
