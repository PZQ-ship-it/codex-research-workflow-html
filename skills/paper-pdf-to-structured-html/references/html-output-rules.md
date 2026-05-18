# HTML Output Rules

Use these rules for every generated paper digest.

## Required Metadata

Include near the top:

- title;
- authors if reliably extracted;
- venue/year if reliably extracted;
- source PDF path;
- generated date;
- paper type and confidence;
- extraction status;
- important manual-check items.

## Required Navigation

Use stable anchor IDs for:

- quick takeaways;
- reading map;
- taxonomy or method map;
- figures and tables;
- datasets and metrics;
- seminal papers or related work;
- challenges and future directions;
- branch deep dives when present.

## Visual Asset Handling

For each included figure or table image:

- store the asset under the paper's output `assets/` folder;
- use a relative `src`;
- include figure/table number when known;
- include caption or a short reconstructed caption;
- include source page;
- include why the visual is important.

Do not include decorative images. Do not crop so tightly that labels become unreadable.

## Readability

- Prefer concise explanatory paragraphs over dense bullet dumps.
- Use tables for comparisons, datasets, metrics, branches, and reading lists.
- Keep long extracted passages out of the page; summarize and cite page numbers.
- Use callouts for uncertainty, limitations, and next-reading guidance.
- Preserve Chinese explanatory text when the user works in Chinese; keep paper terms in English when that prevents ambiguity.

## Validation

Before final delivery:

- open the HTML in a browser or run Playwright when available;
- check console errors;
- verify all image paths resolve;
- check desktop and narrow viewport layout;
- inspect figure readability;
- confirm tables do not create accidental horizontal overflow beyond intentional table scrolling.
