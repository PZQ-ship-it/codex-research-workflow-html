# Third-Party Plugins

This file records third-party Codex plugin snapshots vendored into this repository.

## Codex Council

- Plugin directory: `plugins/codex-council/`
- Marketplace file: `.agents/plugins/marketplace.json`
- Upstream: `https://github.com/ercoledevs/codex-council`
- Commit: `d10b134baa09240088133a559a67d0bc7b506b91`
- Plugin version: `0.7.0`
- License: MIT
- Install date: 2026-06-12
- Install commands used:

```powershell
npx codex-marketplace add ercoledevs/codex-council --plugin --global -y
npx codex-marketplace add ercoledevs/codex-council --plugin --project -y
```

- Global install path after install: `C:\Users\Administrator\.codex\plugins\codex-council`
- Global marketplace file: `C:\Users\Administrator\.agents\plugins\marketplace.json`
- Notes:
  - `codex plugin marketplace add ercoledevs/codex-council` does not work with this upstream because the repository is a single plugin repo, not a Codex marketplace root.
  - Use the VS Code bundled Codex binary for plugin visibility checks on this machine: `c:\Users\Administrator\.vscode\extensions\openai.chatgpt-26.5609.30741-win32-x64\bin\windows-x86_64\codex.exe`.
  - The helper script uses `str.removeprefix`, so validation needs Python 3.9+; the machine's default `python` is Python 3.7.0.
  - Plugin-local runtime state such as `.codex-council/` is intentionally gitignored by the plugin.
