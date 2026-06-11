# Zhihu MCP Setup

Use this reference only when the user explicitly wants the optional `zhihu-mcp` backend for agent-facing tools, comments, user profile/activity, or reusable MCP workflows. The default `public-browser-lite` route remains usable without this setup.

## What Gets Configured

The bundled setup script:

- clones or updates `https://github.com/alizeeblack-code/zhihu-mcp`;
- keeps it under the user-level global skill runtime by default:
  `%USERPROFILE%\.codex\skills\zhihu-public-intel\runtime\zhihu-mcp`;
- creates a local `.venv` with Python 3.10+;
- installs `requirements.txt`;
- installs Playwright Chromium;
- writes a safe `config.json` with `chrome_cookie_extraction=false`;
- registers a Codex stdio MCP server named `zhihu_mcp`.

Run from this repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\setup_zhihu_mcp.ps1
```

If the default Python is too old, pass a newer interpreter:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\setup_zhihu_mcp.ps1 `
  -PythonPath C:\ProgramData\Anaconda3\envs\gaokao_pg\python.exe
```

## Safety Defaults

- The setup does not copy, read, or extract real Zhihu cookies.
- `config.json` sets `chrome_cookie_extraction=false`.
- `HEADLESS=true`, `PYTHONUTF8=1`, and `PYTHONIOENCODING=utf-8` are registered in the MCP env.
- Runtime files are intentionally private and should remain ignored:
  `runtime/`, `cookies.json`, `auth.json`, `.env`, `storage_state.json`, browser profile directories, DB files, and logs.

Do not paste `z_c0`, `d_c0`, cookie strings, request headers, or browser storage into chat or committed files.

## Cookie Boundary And Assisted Login

Without `cookies.json`, the MCP server can start and tools can be listed, but Zhihu may return login walls, empty results, 401 responses, or partial public-only data.

For logged-in search/detail/comment/activity completeness, the user must authorize a local login state. Prefer the bundled visible-browser helper over asking the user to export cookies manually:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1
```

What happens:

- Codex opens a visible Playwright Chromium window at Zhihu login.
- The user completes login, MFA, and CAPTCHA directly in the browser.
- The helper waits for Zhihu auth cookies, writes Playwright-format Zhihu cookies to:
  `%USERPROFILE%\.codex\skills\zhihu-public-intel\runtime\zhihu-mcp\cookies.json`.
- The helper prints only status, path, and cookie count; it never prints cookie values.

Useful options:

```powershell
# Show paths and prerequisites without opening a browser
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1 -DryRun

# Refresh an existing cookies.json after the user approves
powershell -ExecutionPolicy Bypass -File .\skills\zhihu-public-intel\scripts\assist_zhihu_login.ps1 -Force
```

Manual export remains acceptable only if the user explicitly prefers it. Keep `chrome_cookie_extraction=false` unless the user has explicitly approved automatic extraction from an existing browser profile and understands the storage path.

## Smoke Tests

Safe setup checks:

```powershell
python C:\Users\Administrator\.codex\skills\zhihu-public-intel\scripts\zhihu_public_intel.py check-runtime
```

```powershell
python C:\Users\Administrator\.codex\skills\zhihu-public-intel\scripts\zhihu_public_intel.py plan `
  --target "大模型 Agent" `
  --needs search,question,answers,comments,report `
  --prefer-backend zhihu-mcp
```

```powershell
codex mcp list
```

```powershell
C:\Users\Administrator\.codex\skills\zhihu-public-intel\runtime\zhihu-mcp\.venv\Scripts\python.exe -c "import mcp_server; print('IMPORT_OK')"
```

The upstream `mcp_server.py --test` opens a browser and may create session cookies, a profile directory, DB files, and logs. Run it only when temporary runtime state is acceptable, then delete generated state if you do not intend to keep it.
