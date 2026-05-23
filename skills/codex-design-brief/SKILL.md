---
name: codex-design-brief
description: Use when product, UI, documentation, or workflow decisions need a lightweight human-readable source of truth before implementation. Inspired by oh-my-codex design workflow, adapted for repo-local DESIGN/decision notes in native Codex IDE.
---

# Codex Design Brief

Capture the design decision source before building or changing a user-facing workflow.

This is the native Codex adaptation of OMX `$design`: keep a lightweight decision source that guides implementation and review; omit OMX runtime state and automatic follow-up modes.

## Workflow

1. Inspect existing design sources.
   - Look for `DESIGN.md`, design docs, HTML notes, screenshots, Figma links, existing UI components, or style guides.
2. Write a compact brief.
   - Audience
   - Primary workflow
   - Non-goals
   - Information hierarchy
   - Interaction states
   - Visual constraints
   - Acceptance checks
3. Keep it practical.
   - Prefer concrete choices over abstract taste words.
   - Tie choices to the existing repo style.
   - Do not create a landing-page narrative unless the task is actually a landing page.
4. Use the brief during implementation.
   - Treat it as a working contract.
   - Update it when decisions change.
5. Verify the result.
   - For UI or HTML, pair with `$codex-visual-acceptance`.
   - For implementation planning, pair with `$codex-consensus-plan`.
   - For execution, pair with `$codex-completion-loop`.

## Output

Produce or update a brief in the user's requested format. If no format is specified, use a concise Markdown or HTML note consistent with the repo.

## Boundaries

- Keep the brief short enough to be used during implementation.
- Separate confirmed behavior from recommendations.
- Do not invent brand/product requirements that the user did not ask for.

## References

Read `references/design-brief-template.html` when drafting a brief from scratch.
