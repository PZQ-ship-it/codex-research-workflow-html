---
name: codex-visual-acceptance
description: Use when a UI, HTML note, figure, PDF page, or visual artifact needs browser/screenshot-based validation. Inspired by oh-my-codex visual-ralph, adapted for native Codex Playwright, PDF, and screenshot workflows.
---

# Codex Visual Acceptance

Validate what a human will actually see. Use this skill for HTML pages, frontend UI, generated figures, rendered PDFs, and other visual outputs.

## Workflow

1. Identify the visual surface.
   - HTML/browser page: use Playwright.
   - PDF: render or inspect key pages with PDF tooling.
   - Static image/figure: inspect dimensions, file outputs, and screenshots where useful.
2. Define viewports or pages.
   - Always include a desktop check.
   - Add a narrow/mobile check for responsive HTML or UI.
   - For PDFs, inspect title/summary pages and any figure/table-heavy pages.
3. Capture evidence.
   - Save screenshots under the repo's existing output/artifact convention.
   - Check browser console warnings/errors when using Playwright.
4. Review visually.
   - Look for overlap, clipped text, blank canvases, broken images, unreadable labels, missing fonts, wrong aspect ratios, and accidental horizontal scroll.
5. Iterate if needed.
   - Fix the source artifact, regenerate, and repeat the capture.

## Output

Report:

- surfaces checked
- screenshot or rendered artifact paths
- console status when applicable
- visual issues found and fixed
- remaining manual checks, if any

## References

Read `references/visual-checklist.html` for a compact acceptance checklist.
