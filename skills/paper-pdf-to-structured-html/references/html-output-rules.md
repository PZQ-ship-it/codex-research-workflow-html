# HTML Output Rules

Use these rules for every generated paper digest.

## Primary Output Goal

The HTML should be self-contained enough that the user can read it instead of the original PDF for normal understanding. Treat the PDF as the source of truth and the HTML as a compressed, structured reconstruction of the paper's content. Use page numbers, figure numbers, and section names for provenance, not as instructions to go read the PDF.

Do not produce a navigation-only artifact. If the page says a section, branch, dataset, method, experiment, or table is important, include its substance in the HTML.

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
- coverage status: what major sections are fully covered, condensed, figure/table-only, or omitted.

## Required Navigation

Use stable anchor IDs for:

- paper-in-one-page summary;
- structure map;
- core content or branch/method deep dives;
- taxonomy or method map;
- evidence, figures, and tables;
- datasets and metrics;
- seminal papers or related work;
- challenges and future directions;
- coverage and manual checks.

Every navigation target must contain explanatory content. A section with only a list of page references, a figure without interpretation, or "read Section X" fails this requirement.

## Structure Map / Taxonomy GPS Requirements

For any survey, review, tutorial, position, system, or benchmark paper with an overview/taxonomy figure, the structure map must explain the paper's logic, not only reproduce the figure.

The section should include:

- the paper's stated organization from the introduction or section overview;
- the organizing principle behind the figure;
- a hierarchy explanation: top-level categories, sub-branches, examples, datasets/metrics, applications;
- parallel/sibling groups under the same criterion;
- upstream/downstream or pipeline relationships when present;
- cross-cutting layers such as datasets, metrics, simulators, transfer, limitations, or evaluation protocols;
- one paragraph explaining how the taxonomy supports the paper's central thesis.

Use relationship labels such as `foundation`, `capability`, `task`, `evaluation`, `transfer`, `application`, or `open problem` when they clarify the map. If a relationship is inferred from layout rather than stated by the authors, mark it as an inference.

Anti-pattern: a `Taxonomy GPS` section that contains only an overview image plus a caption. That does not satisfy the standalone reading contract.

## Visual Asset Handling

For each included figure or table image:

- store the asset under the paper's output `assets/` folder;
- use a relative `src`;
- include figure/table number when known;
- include caption or a short reconstructed caption;
- include source page;
- include why the visual is important.
- explain the main takeaway in prose near the figure. For tables, summarize the key comparison dimensions and any non-obvious pattern the table supports.

Do not include decorative images. Do not crop so tightly that labels become unreadable.

## Readability

- Prefer concise explanatory paragraphs over dense bullet dumps, but include enough detail to replace normal PDF reading.
- Use tables for comparisons, datasets, metrics, branches, and reading lists.
- Keep long extracted passages out of the page; paraphrase and synthesize with page provenance.
- Use callouts for uncertainty, limitations, and next-reading guidance.
- Preserve Chinese explanatory text when the user works in Chinese; keep paper terms in English when that prevents ambiguity.
- Avoid filler phrases such as "the paper discusses..." unless followed by the actual substance.
- Avoid leaving important content as only "source page: N" or "see Table X"; include the interpreted content directly.
- For long surveys, organize depth progressively: short overview first, then substantive branch sections, then detailed comparison tables. Do not cut branch content merely to keep the page short unless the user asked for a brief summary.

## Content Depth Checklist

Before final delivery, verify that the HTML answers these questions without opening the PDF:

- What is the paper's central thesis and scope?
- What are the major sections or taxonomy branches?
- What does each major branch actually contain?
- What methods, systems, datasets, metrics, or experiments are central?
- What are the paper's main claims, evidence, limitations, and future directions?
- Which figures/tables are essential, and what should the reader learn from each?
- If the paper has a taxonomy or overview figure, what logic does the figure encode: hierarchy, parallel groups, upstream/downstream relations, and cross-cutting axes?
- What was omitted or marked uncertain?

## Validation

Before final delivery:

- open the HTML in a browser or run Playwright when available;
- check console errors;
- verify all image paths resolve;
- check desktop and narrow viewport layout;
- inspect figure readability;
- confirm tables do not create accidental horizontal overflow beyond intentional table scrolling.
- spot-check content coverage against the paper outline or coverage ledger;
- ensure no navigation section is only a pointer to the PDF.
- ensure any taxonomy/overview figure is accompanied by a detailed logic interpretation, not only a caption.
