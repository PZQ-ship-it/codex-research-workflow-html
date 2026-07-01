# Validation

## Skill Structure

Run:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/frontend-design-codex
```

Expected:

```text
Skill is valid!
```

## Trigger Prompts

### Landing Page

```text
Use $frontend-design-codex to design and implement a non-generic landing page for a small robotics studio called Northline Kinetics. The first viewport should feel industrial, precise, and memorable, with strong typography, a clear CTA, and a real browser verification pass.
```

Expected behavior:

- Selects a distinct visual direction before coding.
- Avoids default purple gradients, generic cards, and filler badges.
- Produces a runnable page with desktop and mobile verification.

### Dashboard / App UI

```text
Use $frontend-design-codex to build a compact operational dashboard for a port logistics team. It should prioritize dense scanability, status rows, filters, and a detail inspector instead of marketing cards. Verify the main filter or selected-state interaction in a browser.
```

Expected behavior:

- Treats the surface as an operational app, not a landing page.
- Keeps tables, filters, rows, and inspector state prominent.
- Provides at least one working interaction.

### Existing UI Redesign

```text
Use $frontend-design-codex to redesign the existing settings screen in this repo without changing its data model or route behavior. Keep the same controls and labels, but make the typography, spacing, state hierarchy, and responsive layout feel production-grade. Verify no labels or controls disappeared.
```

Expected behavior:

- Inspects existing code first.
- Preserves controls, labels, routes, and state behavior.
- Improves visual hierarchy without replacing the workflow.

## Codex CLI Evaluation Summary

Three simple UI cases were generated and browser-verified:

| Case | Result |
| --- | --- |
| Landing page | Natural frontend prompt loaded the skill and generated an editorial type-foundry page. |
| Dashboard | Explicit `$frontend-design-codex` prompt generated a rail-yard dispatch dashboard. |
| Existing UI redesign | Natural redesign prompt loaded the skill and updated a settings screen while preserving controls. |

Browser verification used Chrome via Playwright at desktop `1366x900` and mobile `390x844`.

Checks performed:

- No console errors.
- No page errors.
- No page-level horizontal overflow.
- No external network assets.
- Primary interactions worked.
- Desktop and mobile screenshots were captured.
- Visual output avoided generic purple-gradient/card-grid AI UI.

Example files and screenshots are included under `examples/`.
