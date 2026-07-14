# Translation Quality Contract

Use this reference before accepting a translated PDF or describing its fidelity.

## Profiles

### quick-read

Purpose: understand the paper without constantly switching to the English PDF.

Minimum evidence:

- translation process exited successfully;
- expected mono/dual PDFs exist;
- output page counts match the source when page-count tooling is available;
- title, abstract, one figure/table page, one formula page, and the last page receive spot checks.

Allowed claim: `quick-read translation generated`.

Do not claim citation, code, or publication fidelity.

### fidelity-review

Purpose: preserve layout while making every remaining risk visible.

Required evidence:

- all quick-read checks;
- source, mono, and dual PDFs rendered page by page;
- every rendered page visually inspected, preferably through contact sheets plus full-size priority pages;
- all automatically flagged risk pages inspected at full size;
- failures recorded in `qa-report.md` or an equivalent page ledger.

Initial allowed claim: `translation generated; manual review required`.

Only change this to `fidelity reviewed` after the visual pass. Do not use `fidelity passed` when any hard failure remains.

## Hard Failure Categories

- author names or affiliations are mistranslated, merged, or assigned to the wrong person;
- bibliography titles, author lists, citation numbers, URLs, or DOIs are materially altered;
- source code, variable names, function signatures, commands, or syntax are translated or corrupted;
- formulas, symbols, subscripts, superscripts, or equation numbers are lost or changed;
- table cells overlap, disappear, move to the wrong row/column, or become unreadable;
- translated text is clipped, covered by masks, duplicated, or placed over unrelated content;
- dense appendices, prompts, trajectories, or colored annotations lose content or ordering;
- output pages are blank, missing, or unexpectedly differ in count.

## Acceptable Limitations With Disclosure

- figure-internal labels remain English when they are part of a raster or vector drawing;
- minor line wrapping or font substitution does not hide content or change meaning;
- translated captions expand vertically but remain associated with the correct figure/table;
- bilingual pages are wider than source pages because original and translation are side by side.

## Mandatory Review Order

1. First page: title, method name, authors, affiliations, abstract.
2. All bibliography/reference pages.
3. All code, pseudocode, prompt, and command pages.
4. All dense trajectory or colored-highlight appendix pages.
5. All figure/table/formula pages.
6. Remaining pages for clipping, overlap, blank output, and page-order errors.

## Reflexion Baseline

The 19-page Reflexion benchmark demonstrated why the gates are necessary:

- glossary control fixed `Reflexion -> 反射` in the title;
- author/affiliation translation still contained errors;
- bibliography entries were translated and compressed;
- Python code was translated into invalid syntax;
- dense appendix trajectories had masks, clipping, and reordered content.

This baseline supports the quality contract; it does not imply every paper will fail on the same pages.
