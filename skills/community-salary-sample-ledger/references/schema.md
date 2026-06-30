# Community Salary Sample Ledger Schema

Use one row per salary, offer, JD, or community signal. Split multiple companies, cities, levels, years, or degrees into separate rows when possible.

## Required Core Columns

| Column | Meaning |
|---|---|
| `sample_id` | Stable row id. Auto-generated when appended by script. |
| `collected_at` | ISO timestamp when the row was recorded. |
| `sample_year` | Year the salary/JD/offer signal refers to; use `unknown` if unclear. |
| `company` | Company, lab, institute, or employer. |
| `city` | City of role or sample; use `unknown` if not specified. |
| `region` | `深圳`, `大湾区`, `北京`, `上海`, `杭州`, `其他中国大陆`, `香港`, or `unknown`. |
| `job_family` | Broad role family, for example `大模型算法`, `Agent/RAG`, `LLM Infra`, `医疗AI`, `机器人`, `黑盒优化`. |
| `job_title` | Original or normalized title if available. |
| `degree` | `博士`, `硕士`, `本科`, `不限`, or `unknown`. |
| `entry_type` | `博士应届`, `博士社招0-3年`, `博士后转企业`, `研究院`, `硕士校招`, `社招`, or `unknown`. |
| `experience_years` | Experience requirement or sample experience. |
| `level` | Company level if known. |

## Salary Columns

| Column | Meaning |
|---|---|
| `salary_period` | `monthly`, `annual_base`, `total_comp`, `range`, `unknown`, or `not_salary`. |
| `monthly_base` | Monthly base or range, as written. |
| `annual_base` | Annual base or range, as written. |
| `bonus` | Bonus, months, percentage, or range. |
| `stock_or_options` | Stock/options/RSU/significant equity notes. |
| `signing_bonus` | Signing bonus. |
| `subsidy` | Housing/talent/博士后/subsidy notes. |
| `total_comp` | Total compensation signal or range. |
| `currency` | Usually `CNY`; use `HKD` or `unknown` if needed. |
| `pre_tax_or_after_tax` | `pre_tax`, `after_tax`, or `unknown`. |

## Evidence Columns

| Column | Meaning |
|---|---|
| `source_platform` | Offershow, Nowcoder, Maimai, Boss, Liepin, Zhihu, XHS, OfficialJD, Other. |
| `source_type` | `official_jd`, `public_post`, `manual_logged_in_summary`, `screenshot_summary`, `salary_site`, `recruiter_note`, or `other`. |
| `source_url` | Public URL or platform landing page. Do not include private tokenized URLs. |
| `source_date` | Date of source publication if known. |
| `quote_or_summary` | Short user-written summary or compliant short excerpt. |
| `confidence` | `high`, `medium`, or `low`. |
| `uncertainty_notes` | What is unclear, mixed, old, inferred, or unverified. |

## RA Mapping Columns

| Column | Meaning |
|---|---|
| `matched_direction_ranks` | Semicolon-separated RA direction ranks, for example `1;3;4`. |
| `matched_direction_names` | Broad RA direction names. |
| `skill_requirements` | Skills/JD requirements: papers, C++, CUDA, PyTorch, serving, clinical domain, etc. |
| `ra_transfer_assets` | RA-stage assets that transfer to this role. |
| `career_value_note` | Short implication for career-value scoring. |

## Confidence Guidance

Use `high` only when the row is official, explicit, recent, and scoped to company/city/role/degree, or when multiple independent sources agree.

Use `medium` when the row is specific and plausible but from one community channel or lacks one important field.

Use `low` when it is a rumor, single screenshot, mixed degree, mixed city, old sample, inferred role family, or ordinary algorithm salary used only as weak context.
