---
name: official-career-page-watcher
description: Monitor official public recruiting pages for lightweight AI, PhD, postdoc, research scientist, LLM, Agent, RAG, Infra, medical AI, robotics, and lab hiring signals. Use when Codex needs to seed, run, or maintain a low-risk watcher for company/lab career pages, campus recruiting pages, postdoc pages, or official role-detail URLs; when a project needs JD-change detection from official sources; or when recruiting evidence should be collected without logging in, scraping private APIs, bypassing CAPTCHA/paywalls, or storing raw HTML/full text.
---

# Official Career Page Watcher

Use this skill to create and run a safe watcher over official public recruiting pages. The watcher stores only metadata, visible-text hash, status, title, character count, and keyword hit counts. It does not archive raw HTML or full page text.

## Workflow

1. Confirm the project output location.
   - Prefer `references/recruiting/official-career-page-watcher/` inside the active project or repo.
   - Keep project-specific seeds and run outputs in the project; keep reusable logic in this skill.
2. Initialize seeds if needed.
   - Copy `references/default-seeds.json` from this skill to the project as `seeds.json`.
   - Edit project seeds for the task's company list, cities, job families, and source notes.
3. Run validation before network fetching.
   - Use `--validate-only` to catch malformed seeds.
4. Run a small smoke test.
   - Use `--limit 5 --verbose` before full runs.
5. Run the full watcher.
   - Write outputs to the project `runs/` directory.
6. Interpret outputs conservatively.
   - Treat `matched_keywords` and `change_status` as discovery hints only.
   - Inspect official pages before citing a JD.
   - Treat JavaScript-only or low visible-text pages as browser/manual follow-up, not as "no roles".

## Commands

Use PowerShell on Windows:

```powershell
$skill = "C:\Users\Administrator\.codex\skills\official-career-page-watcher"
$project = "D:\todo\references\recruiting\official-career-page-watcher"
New-Item -ItemType Directory -Force $project | Out-Null
Copy-Item "$skill\references\default-seeds.json" "$project\seeds.json" -Force
python "$skill\scripts\official_career_page_watcher.py" --seeds "$project\seeds.json" --out-dir "$project\runs" --validate-only
python "$skill\scripts\official_career_page_watcher.py" --seeds "$project\seeds.json" --out-dir "$project\runs" --limit 5 --verbose
python "$skill\scripts\official_career_page_watcher.py" --seeds "$project\seeds.json" --out-dir "$project\runs" --verbose
```

Use custom seeds:

```powershell
python "$skill\scripts\official_career_page_watcher.py" --seeds "path\to\seeds.json" --out-dir "path\to\runs" --verbose
```

## Seed Schema

Each seed should include:

- `id`: stable lowercase id.
- `company`: company, lab, or institute name.
- `url`: official public URL.
- `page_type`: home, search, campus, postdoc, role detail, or lab recruitment.
- `priority`: project-specific priority such as `shenzhen_gba`, `hong_kong_gba`, `reference_city`.
- `tags`: company type, topic, city, and source hints.
- `source_note`: where the URL came from, such as AnySearch query, official site navigation, or university career page.

Optional fields:

- `keywords`: extra seed-specific keywords in addition to `global_keywords`.

## Output Semantics

- `latest.json`: full structured metadata for the latest run.
- `latest.csv`: compact table for sorting/filtering.
- `latest.md`: human-readable summary.
- `status=ok`: simple public fetch and parse succeeded.
- `status=http_error` / `status=fetch_error`: simple fetch failed; use browser/manual inspection if important.
- `change_status=new`: no previous `latest.json` entry existed.
- `change_status=changed`: normalized visible-text hash changed from previous run.
- `change_status=unchanged`: normalized visible-text hash matches previous run.

## Safety

- Use only official public pages and public university/lab recruitment announcements.
- Do not log in, bypass CAPTCHA, reverse engineer private APIs, automate outreach, or store private platform content.
- Do not store raw HTML, full page text, cookies, tokens, API keys, private screenshots, usernames, or personal identifiers.
- Use AnySearch or public search only for seed discovery; do not treat snippets as final JD/salary evidence.
- For salary or offer conclusions, create a separate source ledger and cross-check multiple sources.

## References

- Read `references/source-notes.md` when you need the provenance of the bundled default seed list.
- Use `references/default-seeds.json` as a starter, not as a complete or always-current company universe.
