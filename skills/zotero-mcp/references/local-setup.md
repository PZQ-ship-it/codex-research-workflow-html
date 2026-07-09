# Local Zotero MCP Setup

## Runtime Paths

This wrapper keeps third-party source checkouts and virtual environments outside Git:

```text
C:\Users\Administrator\AppData\Local\Codex\zotero-mcp
```

Current expected subpaths:

```text
source\54yyyu-zotero-mcp
.venv\Scripts\zotero-mcp.exe
.venv\Scripts\zotero-cli.exe
```

## Setup Commands

Install or refresh the local runtime:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\.codex\skills\zotero-mcp\scripts\zotero_mcp_local.ps1 install
```

Check status:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\.codex\skills\zotero-mcp\scripts\zotero_mcp_local.ps1 status
```

Print the Codex MCP TOML snippet:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\.codex\skills\zotero-mcp\scripts\zotero_mcp_local.ps1 mcp-config
```

Run a non-secret smoke check:

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\.codex\skills\zotero-mcp\scripts\zotero_mcp_local.ps1 smoke
```

## Python Selection

The helper needs Python 3.10+. On this machine, PATH `python` may point to Python 3.7, so the helper searches known conda environments first. Override with:

```powershell
$env:ZOTERO_MCP_PYTHON = "C:\path\to\python.exe"
```

Override runtime location with:

```powershell
$env:ZOTERO_MCP_RUNTIME = "D:\private-runtime\zotero-mcp"
```

## Zotero Desktop

For local read mode:

1. Start Zotero Desktop.
2. In Zotero, enable Advanced -> "Allow other applications on this computer to communicate with Zotero".
3. Keep `ZOTERO_LOCAL=true` in MCP server environment.

No Zotero API key is required for local read mode. Write operations may require hybrid mode with Zotero Web API credentials depending on the upstream server behavior.

## Codex Config

Safe local-read config:

```toml
[mcp_servers.zotero]
command = 'C:\Users\Administrator\AppData\Local\Codex\zotero-mcp\.venv\Scripts\zotero-mcp.exe'
args = ['serve']

[mcp_servers.zotero.env]
PYTHONIOENCODING = 'utf-8'
PYTHONUTF8 = '1'
ZOTERO_LOCAL = 'true'
```

Restart Codex after editing `C:\Users\Administrator\.codex\config.toml`.

Do not store `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_ID`, WebDAV credentials, cookies, or tokens in tracked files.
