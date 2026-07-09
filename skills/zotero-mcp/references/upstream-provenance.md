# Upstream Provenance

## Runtime Source

- Project: `54yyyu/zotero-mcp`
- Upstream URL: `https://github.com/54yyyu/zotero-mcp`
- Local runtime clone: `C:\Users\Administrator\AppData\Local\Codex\zotero-mcp\source\54yyyu-zotero-mcp`
- Package installed in isolated venv: `zotero-mcp-server`
- Installed version checked on 2026-07-09: `Zotero MCP v0.6.1`
- Runtime clone commit checked on 2026-07-09: `f4eb88a2ee463cbddd4b83c9f38cc12d1263968a`
- License observed in upstream clone: MIT License

## Storage Policy

Do not vendor the full upstream repository or virtual environment into this skill. Keep them under the local runtime path and record commit/package provenance here and in the storage repo third-party ledger.

When updating:

1. Run `scripts\zotero_mcp_local.ps1 setup-source`.
2. Run `scripts\zotero_mcp_local.ps1 setup-env`.
3. Update this provenance file with the new commit and version.
4. Revalidate global and storage repo skill copies.
5. Recheck SHA-256 parity.
