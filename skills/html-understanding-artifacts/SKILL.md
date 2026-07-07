---
name: html-understanding-artifacts
description: "Create focused, self-contained HTML artifacts when a result, process, plan, code review, comparison, investigation, source ledger, timeline, dashboard, or concept explanation would be easier to understand visually or interactively than as plain Markdown. Use when the user asks for an HTML artifact, visual explanation, interactive report, process/result visualization, or when Codex's output is spatial, comparative, temporal, navigational, or too dense for linear text. Do not use for short answers, ordinary status updates, code-only edits, or fixed-format documents."
---

# HTML Understanding Artifacts

Create one atomic HTML artifact that helps the user understand the specific material at hand. Treat HTML as a cognitive interface for inspection, comparison, navigation, and lightweight interaction, not as decoration or a generic template.

## Core Rule

Let the content determine the structure. Do not force a fixed layout, category, template, palette, or section order. Choose only the visual and interactive devices that make the current result or process easier to understand.

## Good Artifact Criteria

A good artifact should:

- Make the important relationships visible: alternatives, dependencies, flow, hierarchy, evidence, risk, status, or change.
- Reduce mental load compared with Markdown by using space, grouping, color, tables, diagrams, progressive disclosure, or small interactions with clear purpose.
- Preserve the reasoning trail: show what was inspected, what changed, what evidence supports each conclusion, and what remains uncertain when relevant.
- Be self-contained: one `.html` file with inline CSS, JavaScript, and SVG as needed.
- Open locally without a server: support `file://` and double-click viewing.
- Avoid external runtime dependencies by default: no React, no build step, no package install, no CDN unless the user or task explicitly calls for it.
- Stay readable before it is pretty: typography, spacing, contrast, responsive behavior, and scan order matter more than visual novelty.
- Include export or copy controls only when the user can meaningfully bring artifact state back into the workflow.

## Shape Selection

Pick the shape from the material, not from this list mechanically:

- Compare alternatives with side-by-side lanes, tradeoff rows, decision criteria, and clear recommendation markers.
- Explain a process with a timeline, pipeline, state machine, sequence, or step inspector.
- Explain code with module maps, call paths, annotated diffs, entry points, data flow, and risk notes.
- Summarize research or investigation with source maps, evidence matrices, claim-to-source links, timelines, confidence labels, and open questions.
- Track long-running work with progress checklists, status lanes, blockers, evidence links, and next actions.
- Teach a concept with a compact model, glossary, tabs, toggles, small simulations, examples, and counterexamples.
- Support triage or editing with purpose-built controls and a `Copy as Markdown`, `Copy prompt`, or equivalent export path.

If none of these shapes genuinely improves understanding, do not create HTML.

## Atomicity

Keep this skill atomic:

- Do not route to another HTML skill, web-artifact framework, template pack, renderer, or design system skill.
- Do not create a reusable HTML generation subsystem unless the user explicitly asks for one.
- Do not make multiple HTML files when one page with anchors, tabs, or disclosure controls will do.
- Do not turn the artifact into an application with backend assumptions, persistence requirements, authentication, or routes.

## Output Rules

- Save the artifact in the active workspace unless the user gives another path.
- For ephemeral artifacts, prefer `.agent-html/<slug>-<timestamp>.html` when that directory convention is acceptable.
- For durable artifacts, follow the local project convention, such as `reports/`, `docs/`, `postmortems/`, or a project-specific artifact directory.
- Report the saved path and how to open it.
- If the artifact summarizes files, sources, commands, or code, include enough provenance inside the page for future review.

## Visual Discipline

- Derive visual style from the repo or artifact context when available.
- Use restrained, accessible styling: legible system fonts, stable spacing, sufficient contrast, and responsive layout.
- Avoid generic AI artifact habits: decorative gradients, card grids everywhere, needless hero sections, excessive rounded boxes, gratuitous animation, emoji-heavy headings, and visual polish that hides weak structure.
- Use color semantically and sparingly for status, risk, category, confidence, or selection.

## Before Finishing

Check that:

- The artifact answers the user's actual question or helps inspect the actual result/process.
- The page is self-contained and can be opened locally.
- Text does not overflow or overlap in common desktop and narrow widths.
- Interactions, if present, have an obvious purpose and do not require a backend.
- Any uncertainty, caveat, or next action visible in the reasoning is also visible in the artifact.
