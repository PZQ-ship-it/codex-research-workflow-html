# Zotero MCP Tool Routing

## Choose Zotero MCP When

- The user asks to search, inspect, summarize, compare, or cite papers already in their Zotero library.
- The task needs the user's Zotero notes, annotations, tags, collections, item metadata, or local full text.
- The user asks to set up or debug Zotero MCP for Codex.

Use public-source skills instead when the paper is not known to be in Zotero:

- `paper-review-source-intel` for arXiv, OpenReview, ACL Anthology, CVF, PMLR, proceedings, and open paper metadata.
- `google-scholar-profile-intel` or OpenAlex-style routes for author/profile discovery.
- `anysearch` or browser search for current public discovery.

## Search Strategy

For nontrivial library discovery, do not rely on one search phrase:

1. Search by exact title, author, DOI, or citation key when available.
2. Search by 2-4 keyword variants.
3. Use semantic search for conceptual queries if the semantic database is configured.
4. Check notes/annotations when the user asks about their own highlights, claims, or reading history.
5. Retrieve metadata before full text; retrieve full text only for selected candidate items.

## Write Operations

Ask before any operation that mutates the Zotero library:

- add item by DOI/URL/file
- create or update note
- update metadata
- add/remove tags
- create/manage collections
- merge duplicates
- delete/trash items

Prefer dry-run or preview where the upstream tool supports it.

## Fallback CLI

If the MCP server is installed but not exposed in the current Codex session, use the CLI for small checks:

```powershell
& "$env:LOCALAPPDATA\Codex\zotero-mcp\.venv\Scripts\zotero-cli.exe" search "topic" --limit 5
& "$env:LOCALAPPDATA\Codex\zotero-mcp\.venv\Scripts\zotero-cli.exe" get metadata ITEMKEY
& "$env:LOCALAPPDATA\Codex\zotero-mcp\.venv\Scripts\zotero-cli.exe" ann search "term"
```

If CLI calls fail because Zotero is not running or the local API is disabled, report that as an environment readiness issue rather than a library-empty conclusion.
