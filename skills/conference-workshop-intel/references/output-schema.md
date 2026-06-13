# Output Schema

Use this schema when merging or synthesizing conference/workshop evidence from multiple routes.

## Directory Contract

- `raw/`: untouched source captures, including JSON, JSONL, YAML, CSV, HTML, screenshots, PDFs, logs, and cloned metadata excerpts.
- `normalized/events.jsonl`: one row per conference/year/event.
- `normalized/workshops.jsonl`: one row per workshop edition or workshop-source record.
- `normalized/papers.jsonl`: one row per accepted paper, submission, workshop paper, proceedings entry, or program paper row.
- `normalized/policies.jsonl`: one row per CFP, review policy, ethics policy, compute policy, reviewer guidance, or policy-change source.
- `normalized/awards.jsonl`: one row per award, oral, spotlight, notable-paper, or program-label claim.
- `normalized/artifacts.jsonl`: one row per local file, screenshot, downloaded metadata file, or generated report.
- `sources.csv`: source review table.
- `manifest.json`: run plan, commands, limits, credentials policy, and blockers.
- `reports/summary.md`: final synthesis grounded in normalized row IDs.

## Required Common Fields

Every normalized row should include:

- `row_type`
- `row_id`
- `source`
- `source_priority`
- `source_id`
- `source_url`
- `fetched_at`
- `venue`
- `year`
- `raw_ref`

Use stable IDs derived from source, source-specific ID, venue, year, title/name, and URL.

## Event Rows

Recommended fields:

- `event_name`
- `venue`
- `year`
- `track`
- `location`
- `start_date`
- `end_date`
- `official_site`
- `program_url`
- `submission_site`
- `notes`

## Workshop Rows

Recommended fields:

- `workshop_name`
- `acronym`
- `venue`
- `year`
- `track`
- `topics`
- `deadline`
- `notification_date`
- `camera_ready_date`
- `workshop_date`
- `website`
- `openreview_group`
- `paper_list_url`
- `accepted_paper_count`
- `organizers`
- `status`
- `notes`

## Paper Rows

Recommended fields:

- `title`
- `authors`
- `abstract`
- `venue`
- `year`
- `track`
- `workshop`
- `decision`
- `presentation_type`
- `award`
- `doi`
- `arxiv_id`
- `openreview_forum`
- `acl_id`
- `pmlr_id`
- `cvf_id`
- `pdf_url`
- `software_url`
- `citations_count`
- `topics`

## Policy Rows

Recommended fields:

- `policy_type`: `cfp`, `review-policy`, `ethics`, `compute`, `responsible-ai`, `reviewer-guidance`, `timeline`, or `other`.
- `title`
- `venue`
- `year`
- `track`
- `effective_date`
- `deadline`
- `summary`
- `official`
- `page_date`
- `notes`

Do not over-quote policy text. Summarize and preserve the official URL.

## Award Rows

Recommended fields:

- `award_type`: `best-paper`, `best-paper-runner-up`, `honorable-mention`, `test-of-time`, `oral`, `spotlight`, `notable`, or `other`.
- `title`
- `paper_row_id`
- `authors`
- `venue`
- `year`
- `track`
- `session`
- `official`
- `notes`

## Dedupe Policy

Prefer identifiers in this order:

1. OpenReview forum ID.
2. DOI.
3. ACL Anthology ID, PMLR volume/page ID, CVF page ID, or NeurIPS proceedings path.
4. Normalized title plus venue plus year plus track/workshop.

When two sources conflict:

- keep both source rows if the conflict matters;
- mark official rows as primary;
- record a blocker or note in `manifest.json`;
- do not silently overwrite award, presentation type, deadline, or policy fields from a lower-priority source.

## Report Grounding

Reports should cite normalized row IDs and source URLs. For trend claims, include the row count and source family. For policy or award claims, include the official page URL and fetched timestamp.
