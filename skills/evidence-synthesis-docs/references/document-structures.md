# Document Structure Patterns

Use this reference when creating substantial synthesis documents from crawled or collected evidence.

## Structure Selection

Choose structure from the dominant user intent and data shape:

| Intent | Data Shape | Recommended Output |
|---|---|---|
| Understand a domain | Many cases, repeated patterns, year differences, uncertainty | Synthesis report |
| Prepare or execute | Stable actions, stages, deliverables, risks | Action playbook |
| Audit or reuse evidence | Many source records with ids and metadata | Evidence matrix |
| Continue research | Sparse areas, contradictions, weak signals | Gap and crawl plan |
| Compare entities or periods | Balanced evidence across categories or years | Comparison matrix plus short report |

When several outputs are useful, write a role statement for each before drafting:

- Synthesis report role: explain what the evidence means.
- Action playbook role: tell the user what to do and how to judge completion.
- Evidence matrix role: preserve traceability and enable filtering.
- Gap plan role: direct the next collection pass.

## Synthesis Report Pattern

Use this when the user needs understanding, interpretation, or strategic judgment.

Recommended sections:

1. Scope and data boundary
2. Executive summary
3. Evidence map: source types, years, density, confidence
4. Core pattern taxonomy
5. Concrete cases by theme or stage
6. Mechanisms: why the patterns appear
7. Requirements or success factors
8. Risks, counterexamples, and weak assumptions
9. Year or period differences when relevant
10. Practical implications
11. Source index or evidence appendix

Quality bar:

- Every top-level pattern has at least one concrete case.
- Claims distinguish direct evidence from synthesis.
- Time-sensitive claims include year or period labels.
- Sparse areas are labeled instead of generalized.

## Action Playbook Pattern

Use this when the user needs something to follow, prepare, or execute.

Recommended sections:

1. Scope and assumptions
2. How to use this playbook
3. Action matrix overview
4. Stage-by-stage actions
5. Templates or checklists
6. Acceptance criteria
7. Failure modes and counterexamples
8. Minimal viable preparation or execution plan
9. Evidence index

Good action rows include:

| Field | Purpose |
|---|---|
| ID | Stable reference |
| Stage | Where this action belongs |
| Timing | When to do it |
| Action | Verb-led instruction |
| Execution details | How to do it concretely |
| Deliverable | What artifact is produced |
| Success signal | What good performance looks like |
| Risk or counterexample | What to avoid |
| Applies to | Relevant backgrounds or contexts |
| Acceptance criteria | How to verify it is done |
| Evidence strength | Direct, strong, medium, weak, prediction |
| Source ids | Traceability |

Quality bar:

- Every action is executable and verifiable.
- Each action links to evidence or an explicit inference.
- Risks are paired with observable failure modes.
- The playbook does not repeat long explanatory sections from the synthesis report.

## Evidence Matrix Pattern

Use this when the corpus has many records or the final document needs auditability.

Recommended fields:

| Field | Notes |
|---|---|
| record_id | Stable id assigned during processing |
| source_id | Original note id, URL, file id, or source key |
| source_file | Local path or exported file |
| source_title | Human-readable title |
| source_type | Post, comment, interview, report, OCR, transcript, web page |
| author | If available |
| published_at | Original date if available |
| year_or_period | Extracted or inferred year label |
| topic | Main category |
| subtopic | Specific category |
| claim | What the source supports |
| concrete_detail | Specific example, action, fact, or observation |
| inference_level | direct, paraphrase, synthesis, weak_signal, prediction |
| evidence_strength | strong, medium, weak, historical_reference, prediction |
| output_use | Where this record is used |

Keep the matrix factual. Put interpretation in reports, not in raw evidence rows.

## Gap And Crawl Plan Pattern

Use this when evidence is uneven or the user wants proactive research.

Recommended sections:

1. Current evidence coverage
2. Missing questions
3. Contradictions or suspicious claims
4. Search terms and source targets
5. Priority order
6. Expected extraction fields
7. Stop conditions

Each gap should explain why it matters to the user's decision.

## Multi-Document Validation

Before finalizing multiple documents, check:

- Does each document have a different reader job?
- Can the user tell which document to open for understanding versus execution?
- Are shared facts stored once in an evidence table or appendix instead of repeated?
- Do cross-references point to stable file names or record ids?
- Would deleting one document remove a distinct capability, not just a duplicate format?

## Anti-Patterns

Avoid:

- Abstract summaries without concrete source-backed examples.
- "Common experience" sections that do not say who, when, where, and based on what.
- Action plans without deliverables or acceptance criteria.
- Treating forecast, speculation, or marketing interpretation as fact.
- Organizing by source when the user needs decisions.
- Creating many documents because the corpus is large rather than because the documents have distinct roles.
