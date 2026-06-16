# Third-party Adapter Notes

## Default adapter

Default source:

```text
https://github.com/HDdssX/dianping_crawler.git
```

The wrapper expects the checkout to contain:

- `main.py`
- `config.py`
- `pw.py`

The observed CLI contract is:

```powershell
python main.py --keyword "咖啡" --max_pages 1 --comment_pages 1 --output ".\out.csv"
```

The upstream crawler uses Playwright, opens a visible browser, searches configured cities, fetches shop comments, and writes CSV fields compatible with `normalize-csv`.

## Storage boundary

Do not vendor third-party crawler source into this skill. Keep it in an external runtime directory such as:

```text
%LOCALAPPDATA%\Codex\dianping-explore\HDdssX_dianping_crawler
```

Use `DIANPING_CRAWLER_ROOT` or `--crawler-root` when the checkout lives elsewhere.

The wrapper auto-loads private user-level configuration from:

```text
%USERPROFILE%\.codex\skills\dianping-explore\.env
```

Supported keys:

- `DIANPING_CRAWLER_ROOT`
- `DIANPING_COOKIE`

## Secrets boundary

Use `DIANPING_COOKIE` for cookies. Do not write real cookies into:

- `SKILL.md`
- `references/`
- `scripts/`
- git commits
- command examples
- chat responses

The setup command redacts the upstream sample `COOKIES` value in the local checkout by default. The runtime launcher injects the cookie from the environment before running `main.py`.

Use `scripts/assist_dianping_cookie.ps1` when the user wants assisted cookie setup. It opens `https://www.dianping.com/` and delegates storage to `external-api-onboarding/scripts/set_env_secret.ps1` with hidden input.

## Adapter selection

Prefer the default Playwright adapter for small, user-supervised samples because it keeps the browser visible and pauses for manual verification.

Use heavier projects only after explicitly checking license, maintenance status, and data scope. If a different crawler is chosen, preserve this skill's CLI contract:

- `status` reports readiness without secrets.
- `run-crawler` accepts keyword, cities, page limits, output path, and cookie env name.
- `normalize-csv` or an equivalent command emits JSONL matching `schema`.

## Operating limits

Keep runs small and resumable:

- Start with one city.
- Start with `--max-pages 1 --comment-pages 1`.
- Prefer visible browser mode.
- Stop on verification, account warnings, or repeated HTTP errors.
- Keep raw CSV and normalized JSONL separate.
