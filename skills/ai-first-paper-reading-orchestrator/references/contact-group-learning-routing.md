# Contact-Group And Learning Routing

Read this reference when the run seed includes a professor contact group, several same-batch professors, or a request for learning support while reading papers.

## Contact-Group Input

Accept a JSON group object or a pointer to a project file. Extract:

- `id`, `title`, `order`, `reading_goal`, `contact_logic`;
- `professors[].professor`, `pool`, `priority`, `source`, `mainlines`;
- `coverage_directions[]`, especially market rank, tier, capability cluster, recommended action, and teacher links.

Do not assume the contact-group file is globally current. If the date or source matters, record it in `source-search-log.md`.

## Scheduling Policy

Use contact group as the upper batch and market rank only as within-group ordering.

Score candidate anchor directions by:

- contact value: group order, primary-pool professors, and usefulness for near-term contact material;
- market value: market rank and route-fit;
- material readiness: local survey / representative-paper HTML, glossary, source lock, or existing artifact status.

Default first-run unit:

```text
contact group
  -> anchor direction
  -> 1 survey or tutorial
  -> 1-3 node papers
  -> per-professor direction-fit evidence
  -> pending-human-fit paragraph draft
  -> next action recommendation
```

Never read the entire group by default. Defer non-anchor directions unless they change the anchor choice or a professor coverage gap.

## Group-Aware Outputs

Add these files or sections when useful:

```text
group/group-brief.md
group/professor-coverage-matrix.md
group/professor-fit-draft.md
learning/learning-plan.md
learning/teachback-check.md
```

At minimum, include:

- Contact Group Context: id, title, professors, anchor direction, non-anchor directions deferred.
- Professor Coverage Matrix: professor, mainline, evidence source, confidence, contact use, pending gap.
- Group Reading Boundary: what this run reads, what it does not read, and why.
- Contact Material Use: evidence that may later support CV / personal statement / research plan, marked `pending-human-fit`.
- Per-Professor Fit Notes: evidence-backed links only, not final outreach wording.

## Learning-Support Routing

Use this matrix to decide which local skill should assist the human learning lane.

| Need | Primary Skill | When To Use | Output |
|---|---|---|---|
| Paper-reading mechanics | `guided-learning` | The user wants step-by-step triage, claim/evidence practice, or teach-back | `learning/teachback-check.md`, gap list |
| Prerequisite concepts | `paper-term-glossary-builder` | Dense terms, acronyms, benchmarks, metrics, losses, system components, or overloaded concepts block reading | `glossary.md`, prerequisite map |
| Standalone readable paper digest | `paper-pdf-to-structured-html` | The PDF/survey is too dense or figure/table structure matters | HTML digest, figure/table coverage |
| Canonical paper/source lock | `paper-review-source-intel` | Paper title, DOI, arXiv, OpenReview, venue, OA PDF, accepted-paper status, or citation metadata must be verified | `source-lock.md`, normalized source rows |
| Code / dataset / benchmark intuition | `code-model-benchmark-intel` | Repository, model card, dataset, leaderboard, metric, or reproduction readiness affects paper choice | benchmark/code table, repro-scout notes |
| Current public web verification | `anysearch` | Current tutorials, official docs, public course pages, benchmark docs, or disambiguation are needed | query log and candidate URLs |
| Human-side parallel work | `human-ai-async-work-planner` | AI scout may take minutes and the user can do an interruptible drill | learning lane and return checkpoint |

## AnySearch Query Patterns

Use AnySearch as an entry point, not final evidence. Good templates:

- `{topic} course notes assignment systems`
- `{topic} survey arxiv {year}`
- `{system_name} paper arxiv`
- `{system_name} docs metrics benchmark`
- `{benchmark_name} official docs rules`
- `{professor_name} {direction} OpenReview`
- `{professor_name} {direction} arxiv`
- `HKUST GZ {professor_name} {direction}`
- `{paper_title} ACM DOI`
- `{paper_title} GitHub`

If AnySearch returns an auto-registered API key, do not save it unless the user explicitly confirms where to store it.

## Source Quality

- A-level: official course/docs, arXiv, ACM, USENIX, OpenReview, ACL, CVF, PMLR, MLCommons, professor homepage, lab homepage.
- B-level: survey/tutorial pages, course lecture notes, conference tutorials.
- C-level: blogs, Hugging Face paper pages, mirrors, student repositories, aggregators. Use these as leads only.
- Do not use as final evidence: SEO copies, non-canonical PDF mirrors, pages without author/date/venue, paywalled AI summaries, or login-gated material without user approval.

## Human Gates

AI may draft:

- group evidence packet;
- learning drill;
- source and node-paper recommendation;
- per-professor evidence links;
- pending fit paragraph candidate.

Human must confirm:

- subjective interest and boredom signals;
- reading budget;
- teach-back quality;
- high-cost downloads, GPU/API, authenticated access, or long reproduction;
- final `continue / split-and-continue / pause`;
- any wording used in contact emails, personal statements, or research plans.
