---
name: codex-adversarial-qa
description: Use when a solution, paper claim, experiment pipeline, prompt, or UI needs hostile scenario testing before being trusted. Inspired by oh-my-codex ultraqa/code-review patterns, adapted for native Codex review and verification tools.
---

# Codex Adversarial QA

Try to break the work before users, reviewers, or future you do.

This is the native Codex adaptation of OMX `$ultraqa` and code-review loops: keep hostile scenario design, real evidence, fix-and-rerun discipline, and cleanup reporting; omit OMX lifecycle state and automatic Stop-hook retries.

## Workflow

1. State the promise.
   - What behavior, claim, metric, or user flow is supposed to hold?
2. Build a scenario matrix before testing.
   - User or attacker model
   - Scenario
   - Expected signal
   - Command, rendered artifact, source file, or manual check
   - Cleanup expectation
3. Generate hostile scenarios.
   - Boundary inputs
   - Missing files or partial outputs
   - Stale caches or reruns
   - Contradictory terminology
   - Slow network/API failures
   - Mobile or narrow layouts
   - Reviewer objections
   - Prompt injection or instruction-conflict attempts when reviewing prompts/workflows
   - Misleading success output, flaky checks, and hung commands when testing tools
4. Test or inspect the highest-risk cases first.
   - Prefer real commands, rendered outputs, repo searches, or source-backed checks.
   - Do not treat speculation as a finding without evidence.
   - Use bounded timeouts for commands that can hang.
5. Fix what is in scope.
   - Apply focused changes when execution is requested.
   - For review-only tasks, list findings by severity with file/path evidence.
6. Clean up and close with residual risk.
   - Remove temporary harnesses or state whether they were intentionally kept.
   - State what was verified, what was not, and what would catch future regressions.

## Common Uses

- Code review before commit
- Thesis fact/term consistency checks
- Experiment rerun and resume logic review
- Figure and label consistency checks
- Prompt and workflow stress tests

## Output Shape

- Promise under test
- Scenario matrix
- Findings by severity
- Fixes or recommendations
- Verification evidence
- Cleanup and residual risk

## References

Read `references/qa-scenarios.html` for scenario prompts tailored to code, papers, figures, and benchmarks.
