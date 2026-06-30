# Output Schema

Use JSONL for raw normalized records. Each line should be one public result.

## Required Fields

| Field | Meaning |
|---|---|
| `platform` | Always `nowcoder`. |
| `collected_at` | UTC ISO timestamp of collection. |
| `query` | Query string that produced the result. |
| `tag` | Optional tag: `面经`, `求职进度`, `内推`, `公司评价`, or empty. |
| `order` | Empty/default or `create`. |
| `page` | Result page number. |
| `title` | Public title. |
| `url` | Public Nowcoder URL when available. |
| `snippet` | Short public snippet or generated title context. |
| `source_type` | `feed`, `discuss`, `job`, `problem`, `search_fallback`, or `unknown`. |
| `created_at` | Source timestamp if public and parseable. |
| `view_count` | Public count if available. |
| `like_count` | Public count if available. |
| `comment_count` | Public count if available. |
| `company_hint` | Company name inferred from query/title/snippet/metadata. |
| `job_family_hint` | Role family inferred from keyword matches. |
| `degree_hint` | Degree/seniority hint inferred from text. |
| `city_hint` | City hint inferred from text. |
| `salary_signal` | Boolean. True only if salary/offer terms appear. |
| `signal_terms` | Matched keywords. |
| `confidence` | `low`, `medium`, or `high`; default low for community results. |
| `privacy_note` | Should say `public metadata only`. |

## Recommended Markdown Summary

For human reports, group by:

- query bundle
- company
- city
- job family
- degree/seniority
- offer/salary signal vs interview/JD signal
- source URLs
- confidence and caveats

Do not paste full posts into reports. Link and summarize briefly.
