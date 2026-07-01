# OfferShow Review CSV Schema

The review CSV is a temporary human-audit layer. It should normally live under:

```text
C:\Users\Administrator\.codex\runtime\offershow-browser\reviews\
```

Do not commit review CSVs unless they are fully anonymized and intentionally public-safe.

## Key Columns

| Column | Meaning |
|---|---|
| `selected` | Mark `true` only after a human verifies the row in the visible browser. |
| `review_id` | Stable local review id. |
| `snapshot_file` | Source JSON snapshot path. Keep private runtime paths out of public reports when possible. |
| `candidate_id` | Candidate id from `export-visible`. |
| `visible_hint` | Redacted/truncated visible text hint for orientation only. Do not treat it as final evidence. |
| `human_summary` | Required for selected rows. Write a short human-authored summary, not copied raw page text. |
| `company`, `city`, `job_family`, `degree`, `entry_type` | Normalized scope fields. Use `unknown` if unclear. |
| `salary_period` | `monthly`, `annual_base`, `total_comp`, `range`, `unknown`, or `not_salary`. |
| salary components | Fill separately: `monthly_base`, `annual_base`, `bonus`, `stock_or_options`, `signing_bonus`, `subsidy`, `total_comp`. |
| `confidence` | `low` or `medium`; OfferShow manual rows should not be `high`. |
| `uncertainty_notes` | Explain missing city/degree/year/source ambiguity and cross-check needs. |
| RA mapping columns | Optional direction ranks/names and career-value notes for HKUST(GZ) RA mapping. |

## Selection Rule

A row can be appended only when:

- `selected` is true;
- `human_summary` is filled;
- `company`, `job_family`, `salary_period`, and `confidence` are filled;
- `confidence` is `low` or `medium`;
- no cookies, tokens, phone numbers, usernames, contact details, or raw private text are present.

## Historical Schema Hints

Old public OfferShow projects are not current access routes, but their data model is useful when normalizing human-reviewed rows:

- `company`
- `position` / `job_title`
- `salary`
- `city`
- `remark` / summary notes
- `score` / confidence or popularity hint
- `time` / sample year or source date
- `number` / sample count hint

Treat these as naming hints only. Do not run old crawlers or reuse captured mini-program token/referer flows.
