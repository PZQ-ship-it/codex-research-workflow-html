# Engine Setup

Read this reference when `doctor` cannot find `pdf2zh`, when selecting a non-default translator, or when the source document is private.

## Supported Boundary

- Use PDFMathTranslate-next as the user-facing CLI and BabelDOC as its PDF translation/layout engine.
- The wrapper was tested with `pdf2zh-next 2.9.0` and bundled `BabelDOC 0.6.2` on 2026-07-14.
- Treat other versions as compatible candidates, not verified equivalents. Run `doctor`, a dry run, and a short public-PDF smoke test after changing versions.

Official sources:

- PDFMathTranslate-next: https://github.com/PDFMathTranslate/PDFMathTranslate-next
- Command-line documentation: https://pdf2zh-next.com/getting-started/USAGE_commandline.html
- BabelDOC: https://github.com/funstory-ai/BabelDOC

## Isolated Installation

Prefer an existing project environment that already has a working `pdf2zh` CLI. Otherwise create a task-local environment:

```powershell
python scripts\bootstrap_pdf2zh.py --venv D:\paper-tools\pdf2zh-next
python scripts\translate_paper_pdf.py doctor `
  --pdf2zh-cli D:\paper-tools\pdf2zh-next\Scripts\pdf2zh.exe
```

The bootstrap script pins the tested version by default. Pass `--version` only when intentionally evaluating another release.

## Engine Selection

Default:

```text
--engine siliconflowfree
```

This requires no API key but sends paragraph text to an external service. Use it only for public or user-approved documents.

For OpenAI-compatible, Ollama, DeepSeek, Gemini, or other supported providers:

1. Configure the provider through PDFMathTranslate-next's own private config or environment mechanism.
2. Pass `--engine <name>` and optionally `--config-file <private-path>`.
3. Do not pass keys through `--extra-arg` or store them in the run directory.
4. Do not read or copy the private config into reports, manifests, repositories, or chat output.

The wrapper deliberately does not accept API-key flags.

## External Transfer Gate

Before using a remote provider, classify the PDF:

- public/open paper: remote translation is normally acceptable;
- unpublished draft, confidential review copy, licensed internal report, or private thesis material: obtain explicit user approval or use a local provider;
- restricted or credential-gated source: do not upload without verified authorization.

Record the provider class in the run trace, but never record credentials.

## Windows Path Length

Deep virtual-environment paths can exceed Windows path limits while installing PDF dependencies. Prefer a short environment path such as `D:\paper-tools\pdf2zh-next` and keep long paper artifacts in their normal project run directory.
