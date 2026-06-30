---
name: community-salary-sample-ledger
description: Create, validate, append, normalize, summarize, and export anonymized community salary and offer-signal ledgers from Offershow, Nowcoder, Maimai, BOSS, Liepin, Zhihu, Xiaohongshu, official JD pages, and manual notes. Use when Codex needs comparable evidence for Chinese AI/LLM/PhD career-value research, salary/total-comp analysis, JD-to-research-direction mapping, or source-ledger updates without storing cookies, tokens, private screenshots, usernames, or raw private content.
---

# Community Salary Sample Ledger

Use this skill to turn messy salary, offer, JD, and community signals into an auditable ledger. Treat every row as evidence with scope and uncertainty, not as a fact by itself.

## Safety Defaults

- Store only normalized, anonymized rows and source metadata.
- Do not store cookies, tokens, private headers, browser profiles, usernames, contact data, private message text, raw comments, or raw private screenshots.
- Do not bypass login, CAPTCHA, paywalls, rate limits, anti-bot controls, or platform permissions.
- Prefer official JD/source links plus short user-written summaries over copied raw platform content.
- Mark single-post, screenshot-only, ambiguous-degree, or non-city-specific salary signals as low confidence.
- Keep screenshots outside Git unless the user explicitly asks and the file is safe to store.

## Quick Commands

```powershell
$skill = "C:\Users\Administrator\.codex\skills\community-salary-sample-ledger"
python "$skill\scripts\community_salary_sample_ledger.py" schema
```

Create a CSV template:

```powershell
python "$skill\scripts\community_salary_sample_ledger.py" init `
  --output projects\hkust-gz-ra-academic-fit\career-maps\community-salary-samples.csv
```

Append one normalized sample:

```powershell
python "$skill\scripts\community_salary_sample_ledger.py" append `
  --ledger projects\hkust-gz-ra-academic-fit\career-maps\community-salary-samples.csv `
  --company 腾讯 `
  --city 深圳 `
  --job-family "大模型算法 / Agent" `
  --degree 博士 `
  --entry-type 博士应届 `
  --year 2026 `
  --salary-period total_comp `
  --total-comp "低置信：样本称百万级，未拆 base/bonus/stock" `
  --source-platform Offershow `
  --source-type manual_logged_in_summary `
  --source-url "https://www.offershow.cn/jobs/offerlist" `
  --matched-direction-ranks "1;2;3" `
  --confidence low `
  --notes "人工筛选样本，需牛客/官方JD交叉验证"
```

Validate and summarize:

```powershell
python "$skill\scripts\community_salary_sample_ledger.py" validate --ledger community-salary-samples.csv
python "$skill\scripts\community_salary_sample_ledger.py" summarize --ledger community-salary-samples.csv
```

Export a direction-level matrix:

```powershell
python "$skill\scripts\community_salary_sample_ledger.py" export-matrix `
  --ledger community-salary-samples.csv `
  --output community-salary-direction-matrix.csv
```

## Workflow

1. Normalize the scope.
   - Identify company, city, degree, entry type, job family, year, salary period, and source channel.
   - If a field is unknown, use `unknown` or leave the numeric/split fields blank; do not invent values.
2. Classify the source.
   - Official JD / official program: high for existence and requirements, not salary unless salary is explicit.
   - Offershow / 牛客 / 脉脉 / BOSS / 猎聘 / 知乎 / 小红书: community signal; confidence depends on specificity and cross-checks.
   - Manual logged-in reading: record only your own summary and source metadata.
3. Record salary components separately.
   - Distinguish `monthly_base`, `annual_base`, `bonus`, `stock_or_options`, `signing_bonus`, `subsidy`, and `total_comp`.
   - Record `pre_tax_or_after_tax`, `currency`, `level`, `degree`, `entry_type`, `experience_years`, `city`, and `sample_year`.
4. Map to research direction only at the job-family level.
   - Avoid overfitting a row to a very narrow RA topic.
   - Use `matched_direction_ranks` for broad direction ranks such as `1;3;4`.
5. Validate before synthesis.
   - Run `validate` to catch missing source, missing company/city/job family, ambiguous salary period, or confidence misuse.
   - Use low confidence for unverified screenshots, hearsay, and mixed硕士/博士口径.
6. Synthesize conservatively.
   - Use `summarize` and `export-matrix` to compare channels, companies, cities, job families, and RA direction ranks.
   - State caveats when using ledger rows in career-value conclusions.

## Script Behavior

The bundled script manages CSV ledgers with stable columns. It can initialize a template, append a row from CLI flags, validate rows, summarize counts, and export a direction-level matrix.

Read `references/schema.md` before creating project-specific ledgers or adding fields.

## Non-Goals

- No platform crawling.
- No login automation.
- No cookie or token workflows.
- No private-content archiving.
- No claim that community salary samples prove true compensation without cross-validation.
