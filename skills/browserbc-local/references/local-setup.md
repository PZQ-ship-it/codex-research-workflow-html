# BrowserBC Local Setup

Date: 2026-06-30

BrowserBC / Journey Forge is installed at:

```text
D:\agent-workflow-lab\harnesses\browser-bc
```

Control panel:

```text
http://127.0.0.1:8099/
```

Chrome extension build directory:

```text
D:\agent-workflow-lab\harnesses\browser-bc\extension\dist\chrome-mv3
```

## Environment

- Python venv: `D:\agent-workflow-lab\harnesses\browser-bc\.venv`
- Python used to create it: `C:\ProgramData\Anaconda3\envs\devdefender-lab\python.exe`
- Node observed during setup: `v24.13.0`
- pnpm invocation: `npx --yes pnpm@11.9.0`

No LLM API key was written during setup. Runtime data lives under `data/`, which is git-ignored by the BrowserBC checkout.

## Manual Start

```powershell
cd D:\agent-workflow-lab\harnesses\browser-bc
.\.venv\Scripts\python.exe -m uvicorn server.server:app --host 127.0.0.1 --port 8099 --log-level warning
```

## Manual Extension Load

Open `chrome://extensions`, enable Developer mode, click Load unpacked, and select:

```text
D:\agent-workflow-lab\harnesses\browser-bc\extension\dist\chrome-mv3
```

## Verified Setup

Verified on 2026-06-30:

- Server import passed.
- Harness CLI via `python -m harness.main --help` passed.
- Extension typecheck passed.
- Extension build passed.
- HTTP `/` returned 200 on `127.0.0.1:8099`.
- Protected `/api/config` with the local default bearer key passed with `llm_key_set=false`.

## Notes

BrowserBC's default skill output target is `C:\Users\Administrator\.claude\skills`. For Codex use, first direct output to a temporary review folder, inspect the generated skill, then adapt and sync it into Codex's maintained skill workflow.
