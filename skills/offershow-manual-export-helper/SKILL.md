---
name: offershow-manual-export-helper
description: Open OfferShow in a user-controlled visible browser, inspect or export redacted visible-page salary/offer candidate hints, prepare a human review CSV, and append selected anonymized rows to a community salary ledger. Use when Codex needs low-volume OfferShow salary or offer-signal collection after user-authorized login, especially for Chinese AI/LLM/PhD career-value research, without cookies, tokens, private screenshots, hidden API scraping, or bulk crawling.
---

# OfferShow Manual Export Helper

Use this skill as a thin bridge between the private visible-browser OfferShow helper and `community-salary-sample-ledger`. It is for manual/user-reviewed collection, not automated scraping.

## Safety Defaults

- Use the visible browser helper in `C:\Users\Administrator\.codex\runtime\offershow-browser`.
- Let the user complete login, CAPTCHA, MFA, filtering, and paid/member actions in the browser.
- Do not print or store cookies, tokens, `localStorage`, auth headers, browser profile data, usernames, contact details, raw private posts, or private screenshots.
- Do not call private API endpoints directly, bypass CAPTCHA/paywalls, page through bulk results, or run old crawler code.
- Treat exported candidates as hints only. Append to a salary ledger only after a human-selected row has a short `human_summary`.
- Default OfferShow-only rows to `low` confidence; use `medium` only for specific, scoped, plausible rows. Do not use `high` for OfferShow manual rows.

## Quick Commands

Open/login manually:

```powershell
node C:\Users\Administrator\.codex\runtime\offershow-browser\offershow_helper.js login --url offerList --wait-ms 240000
```

Inspect current page without private state:

```powershell
node C:\Users\Administrator\.codex\runtime\offershow-browser\offershow_helper.js inspect --url offerList --wait-ms 60000 --max-rows 80
```

Export redacted visible candidates after manual filtering:

```powershell
node C:\Users\Administrator\.codex\runtime\offershow-browser\offershow_helper.js export-visible `
  --url offerList `
  --query "腾讯 大模型 博士 深圳" `
  --wait-ms 60000 `
  --max-rows 80
```

Inventory snapshots:

```powershell
$skill = "C:\Users\Administrator\.codex\skills\offershow-manual-export-helper"
python "$skill\scripts\offershow_manual_export_helper.py" inventory `
  --snapshot-dir C:\Users\Administrator\.codex\runtime\offershow-browser\out
```

Create a review CSV:

```powershell
python "$skill\scripts\offershow_manual_export_helper.py" new-review `
  --snapshot-dir C:\Users\Administrator\.codex\runtime\offershow-browser\out `
  --output C:\Users\Administrator\.codex\runtime\offershow-browser\reviews\offershow-review.csv
```

After manually selecting rows and writing `human_summary`, validate and append:

```powershell
python "$skill\scripts\offershow_manual_export_helper.py" validate-review `
  --review C:\Users\Administrator\.codex\runtime\offershow-browser\reviews\offershow-review.csv

python "$skill\scripts\offershow_manual_export_helper.py" append-ledger `
  --review C:\Users\Administrator\.codex\runtime\offershow-browser\reviews\offershow-review.csv `
  --ledger D:\todo\projects\hkust-gz-ra-academic-fit\career-maps\community-salary-samples.csv `
  --dry-run
```

Remove `--dry-run` only after the review passes.

## Workflow

1. Check whether OfferShow is already routed in `D:\todo\codex\tool-registry.md` and `codex\project-map.md`.
2. Run `login` if the persistent browser profile needs fresh user login.
3. Run `inspect` to see non-secret resource hints and visible candidate counts.
4. Let the user filter/navigate in the visible browser, then run `export-visible`.
5. Run `new-review` to create a CSV in the private runtime `reviews/` directory.
6. Have a human mark `selected=true` only for rows they personally verified and write `human_summary`.
7. Run `validate-review`.
8. Append selected rows to the `community-salary-sample-ledger`, then run that ledger's `validate` and `summarize`.

## Script Roles

- `offershow_helper.js` in the private runtime opens Chrome, polls visible page text, records redacted visible candidate hints, and saves JSON snapshots under runtime `out/`.
- `scripts/offershow_manual_export_helper.py` inventories snapshots, creates review CSVs, validates selected rows, and appends selected rows to the community salary ledger.

Read `references/review-schema.md` before editing review CSVs. Read `references/safety-boundary.md` before changing the helper or adding commands.

## Non-Goals

- No OfferShow crawler.
- No private API scraper.
- No copied cookies or headers.
- No automatic ledger append from raw visible text.
- No bulk paging, account automation, or platform-rule bypass.
