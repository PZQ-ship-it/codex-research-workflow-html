---
name: codex-adversarial-qa
description: Use when a solution, paper claim, experiment pipeline, prompt, or UI needs hostile scenario testing before being trusted. Inspired by oh-my-codex ultraqa/code-review patterns, adapted for native Codex review and verification tools.
---

# Codex Adversarial QA

Try to break the work before users, reviewers, or future you do.

## Workflow

1. State the promise.
   - What behavior, claim, metric, or user flow is supposed to hold?
2. Generate hostile scenarios.
   - Boundary inputs
   - Missing files or partial outputs
   - Stale caches or reruns
   - Contradictory terminology
   - Slow network/API failures
   - Mobile or narrow layouts
   - Reviewer objections
3. Test or inspect the highest-risk cases first.
   - Prefer real commands, rendered outputs, repo searches, or source-backed checks.
   - Do not treat speculation as a finding without evidence.
4. Fix what is in scope.
   - Apply focused changes when execution is requested.
   - For review-only tasks, list findings by severity with file/path evidence.
5. Close with residual risk.
   - State what was verified, what was not, and what would catch future regressions.

## Common Uses

- Code review before commit
- Thesis fact/term consistency checks
- Experiment rerun and resume logic review
- Figure and label consistency checks
- Prompt and workflow stress tests

## References

Read `references/qa-scenarios.html` for scenario prompts tailored to code, papers, figures, and benchmarks.
