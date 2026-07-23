---
name: pdf-single-to-two-column
description: Use when a user asks to permanently reconstruct one-column PDFs as two-column PDFs, especially in batch. Distinguish real layout reconstruction from reader reflow, zoom, or 2-up printing; preserve originals, run a representative pilot, choose a backend, and report fidelity risks for formulas, tables, figures, OCR, and reading order.
---

# PDF Single To Two Column

## Goal and boundary

This skill creates new, searchable two-column PDFs. It is not reader Reflow, zoom, or 2-up printing. A PDF usually has no reversible "change one column to two" layout model, so text flow and pages must be reconstructed. Academic PDFs can lose formulas, tables, figures, footnotes, bilingual fonts, or reading order during reconstruction; every batch must pass a representative pilot first.

Never overwrite an original. Use a separate output directory, append `_2col` to output names, and write a JSON manifest. Stop the full run when the pilot fails.

## Backend decision

Use this order:

1. If the original DOCX, LaTeX, or publishing source exists, change its column setting and export again. This is the preferred path for paper-grade fidelity.
2. If an editable DOCX exists and Word is available on Windows, use `scripts/word_com_batch.py`. The Word API is `Section.PageSetup.TextColumns.SetCount(2)`, followed by `Document.ExportAsFixedFormat(..., 17)`; this route was verified locally.
3. If only PDF exists, inspect whether it is text-based and reliably parseable. Word PDF import can be tested explicitly with `--allow-pdf-import`, but headless import may block in the Office PDF converter and is not a default promise. Layout-aware parsers such as Docling, pdf2docx, or Marker may be evaluated as separate backends with pinned versions and representative-page checks.
4. If the PDF is scanned, OCR and layout analysis must come first. Do not feed raw OCR text to Pandoc. `pdftotext -> Pandoc -> Word` is a `lossy` diagnostic baseline only; formulas, author blocks, abstracts, and paragraph order can be damaged.

An Office MCP only exposes Word to Codex; it does not automatically provide PDF two-column reconstruction. `word-mcp-live` can connect over stdio and call Word, but its current tools have no body-text `TextColumns/SetCount` operation; table-column tools are different. Microsoft Work IQ Word MCP is a cloud OneDrive/SharePoint preview requiring tenant, license, and admin governance; it is not local desktop Word automation. Do not use a server exposing arbitrary `RunPython` as the default backend.

## Standard workflow

### 1. Inventory and pilot

- Record input location, PDF page count, fonts, text extractability, source DOCX/TeX availability, Word version, and parser versions.
- Choose 3-5 representative pages covering title/author blocks, body text, formulas, tables, figures, footnotes, and the densest page. Work on a copied sample.
- Check the environment:

```powershell
python scripts/doctor.py
```

### 2. Editable-source Word COM route

Run on a DOCX directory without changing the source:

```powershell
python scripts/word_com_batch.py `
  --input D:\papers\docx `
  --output D:\papers\two-column-pilot `
  --max-files 3
```

To explicitly test Word PDF import, use only a small copied sample:

```powershell
python scripts/word_com_batch.py `
  --input D:\papers\pdf-pilot `
  --output D:\papers\two-column-pilot `
  --allow-pdf-import `
  --max-files 1
```

This switch cannot bypass Office conversion dialogs or licensing. If the process times out, produces no output, or leaves Word running, stop and switch to a layout-aware parser.

### 3. Quality gate

At minimum check:

- `pdfinfo` page count, page size, and non-empty output;
- `pdftotext -layout` title, authors, abstract, section order, and page numbers;
- rendered screenshots of the first page, the densest body page, and formula/table/figure pages;
- true left-column top-to-bottom then right-column flow, with no cross-column mixing, overlap, clipping, blank regions, or font substitution;
- text coverage, page-count change, formula/table integrity, and manual comparison against the source.

Only after the pilot passes should `--max-files` be removed for the full batch. A PDF being openable or having a changed page count is not sufficient evidence of success.

## Failure handling

- If Word COM is unavailable, report the Word version and COM error and name an alternative parser; do not silently downgrade.
- If direct PDF import blocks, terminate that Word instance, preserve the copy and logs, and do not retry the whole directory.
- If reading order or math is damaged, mark the result `lossy` and return to DOCX/LaTeX or a layout-aware parser.
- For scans, record OCR engine, language, confidence, and manual-review pages.
- For MCP failures, check `codex mcp list`, the stdio command, dependencies, and Word COM separately. A successful MCP handshake does not prove that a two-column tool exists.

## References

- Codex MCP: https://developers.openai.com/codex/mcp
- Word text columns: https://learn.microsoft.com/en-us/office/vba/api/word.textcolumns.setcount
- Word fixed-format export: https://learn.microsoft.com/en-us/office/vba/api/word.document.exportasfixedformat
- Microsoft Work IQ Word MCP: https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-word-work-iq
- word-mcp-live: https://github.com/ykarapazar/word-mcp-live

See `references/backends.md` for the backend audit and evidence boundary.
