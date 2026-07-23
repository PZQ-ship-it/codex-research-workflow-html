# Backend evidence and boundaries

## Default decision

The maintained default for PDF-only reconstruction is:

```text
Docling 2.114.0 -> referenced Markdown + picture assets
-> Pandoc 1.19.2.1 -> XeLaTeX (TeX Live 2025, twocolumn)
```

The 2026-07-23 pilot used the same 3-page Chinese Letter input for every route. The source SHA-256 was `6611AB4A17F633DF3D7854D565048E054AA482FC64F5C784FB5087B8927CE433`.

## Representative comparison

| Route | Result | Evidence boundary |
|---|---|---|
| Docling -> Markdown (referenced pictures) -> XeLaTeX | Best non-BabelDOC pilot; clean two-column body text and two extracted pictures | 2 output pages; figure order/captions, title/author parsing, formulas, and pagination still require review |
| pdf2docx -> DOCX -> Word COM | Output generated but rejected | Author/institution became character-level vertical columns; figures had black blocks, gibberish, and overlap |
| pdftotext -layout -> Pandoc -> Word | Diagnostic only; rejected | Reading order, formulas, control characters, and figure fidelity were damaged |
| Word direct PDF import | Failed | Headless `Documents.Open` stalled during Office PDF import; no accepted output |

The comparison artifacts are stored under:

`D:\hkust-gz-ra-paper-reading\research\runs\pdf-two-column-backend-comparison-20260723`

Use its `comparison-manifest.json` and `comparison-report.html` as the evidence record. This was a representative pilot, not a full-batch acceptance.

## Docling contract

- Pin the Python environment and record `docling` version in every manifest.
- Set `do_ocr=False` for born-digital/text PDFs unless a separate OCR contract has been approved.
- Set `do_table_structure=False` in the validated baseline; table extraction is not silently presented as faithful table reconstruction.
- Set `generate_picture_images=True` and `ImageRefMode.REFERENCED`; keep the extracted files in `assets/` beside the Markdown.
- Preserve Markdown, assets, `pandoc.log`, `pdftotext -layout` output, renders, and `manifest.json` even when the pilot is rejected.
- Treat figure order, caption placement, title/author blocks, formula spacing, page breaks, and blank columns as manual review fields.

## Office and MCP boundary

The earlier Office checks remain useful for routing but are not the default backend:

- Word VBA `TextColumns.SetCount` is a DOCX body-column operation, and `ExportAsFixedFormat` can export a DOCX to PDF.
- `word-mcp-live` exposed Word tools but no body-text `TextColumns/SetCount` tool; names referring to “columns” referred to table columns.
- Microsoft Work IQ Word MCP is a cloud OneDrive/SharePoint preview requiring tenant, license, and governance; it is not local PDF reconstruction.
- An MCP handshake proves connectivity only. It does not prove a two-column PDF operation.

If a future Office connector is added, expose a narrow audited `set_text_columns(count=2)` contract rather than arbitrary code execution.

## Why the text-only routes stay diagnostic

Text extraction loses coordinates, object grouping, fonts, equations, and figure placement. A text stream can be made to flow into two columns while still putting authors, abstract, captions, or formula glyphs in the wrong reading order. It is useful for debugging and coverage checks, not for the skill's accepted output.

## Acceptance evidence

Use the following evidence together:

1. Manifest: source/output hashes, versions, command, page count, assets, render paths, and status.
2. Text: `pdftotext -layout` comparison of title, author block, abstract, headings, formulas, captions, and page numbers.
3. Visual: rendered first page, densest body page, and formula/table/figure pages.
4. Human decision: `pilot_passed`, `pilot_rejected`, or `needs_review` recorded beside the manifest.

Do not infer paper-grade fidelity from an openable PDF, a changed page count, or a successful subprocess exit code.
