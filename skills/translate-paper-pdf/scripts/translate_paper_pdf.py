#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENGINE_FLAGS = {
    "siliconflowfree": "--siliconflowfree",
    "openai": "--openai",
    "openaicompatible": "--openaicompatible",
    "ollama": "--ollama",
    "deepseek": "--deepseek",
    "gemini": "--gemini",
    "claudecode": "--claudecode",
}

DEFAULT_PROMPT = (
    "Translate academic prose accurately and concisely. Preserve author names, affiliations, "
    "method names, model names, dataset names, benchmark names, citations, bibliography entries, "
    "URLs, DOIs, equations, code, identifiers, function names, variable names, and command lines "
    "verbatim unless a supplied glossary explicitly says otherwise. Do not translate or rewrite "
    "executable code. When uncertain about a technical proper noun, keep the source form."
)

SENSITIVE_WORDS = ("api-key", "apikey", "token", "secret", "password", "auth-key")
MANAGED_FLAGS = {
    "--output",
    "--lang-in",
    "--lang-out",
    "--glossaries",
    "--config-file",
    "--custom-system-prompt",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def find_command(explicit: str | None, env_name: str, names: list[str]) -> str | None:
    candidates = [explicit, os.environ.get(env_name)]
    candidates.extend(shutil.which(name) for name in names)
    for candidate in candidates:
        if not candidate:
            continue
        expanded = os.path.expandvars(os.path.expanduser(candidate))
        resolved = shutil.which(expanded) or (expanded if Path(expanded).is_file() else None)
        if resolved:
            return str(Path(resolved).resolve())
    return None


def capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def command_version(command: str | None) -> str | None:
    if not command:
        return None
    result = capture([command, "--version"])
    text = (result.stdout + "\n" + result.stderr).strip()
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    match = re.search(r"pdf2zh(?:-next)?\s+version:\s*([^\s]+)", text, re.IGNORECASE)
    if match:
        return match.group(1)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else None


def doctor_data(pdf2zh_cli: str | None) -> dict[str, Any]:
    pdf2zh = find_command(pdf2zh_cli, "PDF2ZH_CLI", ["pdf2zh", "pdf2zh.exe"])
    tools = {
        name: find_command(None, f"{name.upper()}_CLI", [name, f"{name}.exe"])
        for name in ("pdfinfo", "pdftotext", "pdftoppm")
    }
    return {
        "translation_ready": pdf2zh is not None,
        "fidelity_tooling_ready": all(tools.values()),
        "pdf2zh": {"path": pdf2zh, "version": command_version(pdf2zh)},
        "qa_tools": tools,
        "tested_pdf2zh_next_version": "2.9.0",
    }


def validate_glossary(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"Glossary not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = {field.strip().lower() for field in (reader.fieldnames or [])}
        if not {"source", "target"}.issubset(fields):
            raise ValueError(f"Glossary must have source,target columns: {path}")
        for row_number, row in enumerate(reader, start=2):
            normalized = {str(key).strip().lower(): (value or "").strip() for key, value in row.items()}
            if not normalized.get("source") or not normalized.get("target"):
                raise ValueError(f"Glossary row {row_number} has an empty source or target: {path}")


def parse_extra_args(values: list[str]) -> list[str]:
    tokens: list[str] = []
    for value in values:
        tokens.extend(shlex.split(value, posix=os.name != "nt"))
    for token in tokens:
        lowered = token.lower()
        if any(word in lowered for word in SENSITIVE_WORDS):
            raise ValueError("Do not pass credentials through --extra-arg; use a private config or environment.")
        if token in MANAGED_FLAGS:
            raise ValueError(f"{token} is controlled by the wrapper and cannot be passed through --extra-arg")
    return tokens


def redacted_command(command: list[str]) -> list[str]:
    output: list[str] = []
    replacement: str | None = None
    for token in command:
        if replacement:
            output.append(replacement)
            replacement = None
            continue
        output.append(token)
        if token == "--config-file":
            replacement = "<user-managed-config>"
        elif token == "--custom-system-prompt":
            replacement = "<translation-policy>"
    return output


def selected_page_numbers(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    selected: set[int] = set()
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if "-" in item:
            start_text, end_text = item.split("-", 1)
            start, end = int(start_text), int(end_text)
            if start < 1 or end < start:
                raise ValueError(f"Invalid page range: {item}")
            selected.update(range(start, end + 1))
        else:
            page = int(item)
            if page < 1:
                raise ValueError(f"Invalid page number: {item}")
            selected.add(page)
    return selected


def pdf_page_count(pdf: Path, pdfinfo: str | None) -> int | None:
    if not pdfinfo:
        return None
    result = capture([pdfinfo, str(pdf)])
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    return int(match.group(1)) if match else None


def extract_pages(pdf: Path, pdftotext: str | None) -> list[str]:
    if not pdftotext:
        return []
    result = capture([pdftotext, "-layout", "-enc", "UTF-8", str(pdf), "-"])
    if result.returncode != 0:
        return []
    pages = result.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def detect_risk_pages(pages: list[str]) -> dict[int, list[str]]:
    risks: dict[int, list[str]] = {}
    code_pattern = re.compile(
        r"(?m)^\s*(?:\d+\s+)?(def\s+\w+|class\s+\w+|import\s+\w+|from\s+\w+.*import|"
        r"for\s+\w+\s+in\s+|while\s+.+:|return\s+|if\s+.+:)"
    )
    for index, page in enumerate(pages, start=1):
        categories: list[str] = []
        if re.search(r"(?im)^\s*(references|bibliography)\s*$", page):
            categories.append("bibliography")
        code_context = re.search(
            r"(?i)(sample function (signature|body implementation)|python writing assistant|"
            r"programming function implementation example)",
            page,
        )
        if len(code_pattern.findall(page)) >= 2 or page.count("```CODE_BLOCK_") >= 1 or code_context:
            categories.append("code_or_pseudocode")
        trajectory_hits = sum(
            page.lower().count(term)
            for term in ("trial #", "observation", "reflection:", "status:", "> think:", "> go ", "> use ", "action ")
        )
        if trajectory_hits >= 5:
            categories.append("dense_agent_trajectory")
        if len(re.findall(r"(?im)^\s*(figure|table)\s*\d+", page)) >= 3:
            categories.append("dense_figures_or_tables")
        if categories:
            risks[index] = categories
    return risks


def render_pdf(pdf: Path, pdftoppm: str | None, root: Path, dpi: int) -> dict[str, Any]:
    if not pdftoppm:
        return {"status": "skipped", "reason": "pdftoppm not found", "pages": 0}
    target = root / re.sub(r"[^A-Za-z0-9._-]+", "-", pdf.stem)
    target.mkdir(parents=True, exist_ok=True)
    prefix = target / "page"
    result = capture([pdftoppm, "-png", "-r", str(dpi), str(pdf), str(prefix)])
    pages = sorted(target.glob("page-*.png"))
    messages = [line for line in (result.stdout + "\n" + result.stderr).splitlines() if line.strip()]
    return {
        "status": "rendered" if result.returncode == 0 and pages else "failed",
        "directory": str(target),
        "pages": len(pages),
        "exit_code": result.returncode,
        "diagnostic_lines": len(messages),
        "diagnostic_tail": messages[-5:] if result.returncode else [],
    }


def artifact_record(pdf: Path, pdfinfo: str | None, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "path": str(pdf.resolve()),
        "bytes": pdf.stat().st_size,
        "sha256": sha256(pdf),
        "pages": pdf_page_count(pdf, pdfinfo),
    }


def make_qa(
    source: Path,
    outputs: list[Path],
    output_dir: Path,
    profile: str,
    tools: dict[str, str | None],
    dpi: int,
    render: bool,
    selected_pages: set[int] | None,
) -> dict[str, Any]:
    source_pages = pdf_page_count(source, tools.get("pdfinfo"))
    text_pages = extract_pages(source, tools.get("pdftotext"))
    risks = detect_risk_pages(text_pages)
    if selected_pages is not None:
        risks = {page: categories for page, categories in risks.items() if page in selected_pages}
    records = []
    mismatch = False
    for pdf in outputs:
        role = "mono" if ".mono." in pdf.name else "dual" if ".dual." in pdf.name else "translated"
        record = artifact_record(pdf, tools.get("pdfinfo"), role)
        records.append(record)
        if source_pages is not None and record["pages"] is not None and record["pages"] != source_pages:
            mismatch = True

    renders: dict[str, Any] = {}
    if render:
        render_root = output_dir / "qa" / "rendered"
        for pdf in [source, *outputs]:
            renders[str(pdf.resolve())] = render_pdf(pdf, tools.get("pdftoppm"), render_root, dpi)

    known_counts = source_pages is not None and all(item["pages"] is not None for item in records)
    structural_status = "failed" if mismatch else "passed" if known_counts else "partial"
    boundary_pages = (
        {min(selected_pages), max(selected_pages)}
        if selected_pages
        else {1, source_pages or 1}
    )
    priority_pages = sorted({*boundary_pages, *risks.keys()})
    return {
        "structural_status": structural_status,
        "manual_review": "required" if profile == "fidelity-review" else "recommended",
        "source_pages": source_pages,
        "expected_output_pages": source_pages,
        "output_artifacts": records,
        "risk_pages": {str(page): categories for page, categories in risks.items()},
        "priority_pages": priority_pages,
        "renders": renders,
        "allowed_claim": (
            "translation_generated_manual_review_required"
            if profile == "fidelity-review"
            else "quick_read_translation_generated"
        ),
    }


def write_qa_report(path: Path, qa: dict[str, Any], profile: str) -> None:
    lines = [
        "# Paper PDF Translation QA",
        "",
        f"Profile: `{profile}`",
        f"Structural status: `{qa['structural_status']}`",
        f"Manual review: `{qa['manual_review']}`",
        f"Allowed claim before visual review: `{qa['allowed_claim']}`",
        "",
        "## Priority Pages",
        "",
    ]
    for page in qa["priority_pages"]:
        categories = qa["risk_pages"].get(str(page), ["first_or_last_page"])
        lines.append(f"- Page {page}: {', '.join(categories)}")
    lines.extend(
        [
            "",
            "## Mandatory Visual Checks",
            "",
            "- Inspect every rendered page for clipping, overlap, masks, missing text, and blank output.",
            "- Compare author names and affiliations on the first page.",
            "- Keep bibliography entries, citations, URLs, and DOIs source-faithful.",
            "- Treat translated or syntactically changed code as a fidelity failure.",
            "- Check figures, tables, formulas, captions, legends, and dense appendices separately.",
            "- Record pages that require the original PDF for reliable reading.",
            "",
            "## Render Directories",
            "",
        ]
    )
    for pdf, record in qa["renders"].items():
        lines.append(f"- `{pdf}`: `{record.get('status')}` -> `{record.get('directory', 'not rendered')}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_command(args: argparse.Namespace, cli: str, source: Path, output_dir: Path) -> list[str]:
    command = [
        cli,
        str(source),
        "--lang-in",
        args.lang_in,
        "--lang-out",
        args.lang_out,
        "--output",
        str(output_dir),
        "--watermark-output-mode",
        "no_watermark",
        "--no-auto-extract-glossary",
        "--disable-rich-text-translate",
        "--translate-table-text",
        "--custom-system-prompt",
        Path(args.custom_prompt_file).read_text(encoding="utf-8") if args.custom_prompt_file else DEFAULT_PROMPT,
        ENGINE_FLAGS[args.engine],
    ]
    if args.scanned:
        command.append("--auto-enable-ocr-workaround")
    else:
        command.append("--skip-scanned-detection")
    if args.config_file:
        command.extend(["--config-file", str(Path(args.config_file).resolve())])
    if args.glossary:
        command.extend(["--glossaries", ",".join(str(path) for path in args.glossary)])
    if args.pages:
        command.extend(["--pages", args.pages])
    if args.ignore_cache:
        command.append("--ignore-cache")
    if args.no_mono:
        command.append("--no-mono")
    if args.no_dual:
        command.append("--no-dual")
    command.extend(args.extra_tokens)
    return command


def doctor_command(args: argparse.Namespace) -> int:
    data = doctor_data(args.pdf2zh_cli)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if data["translation_ready"] else 2


def qa_command(args: argparse.Namespace) -> int:
    source = Path(args.pdf).expanduser().resolve()
    outputs = [Path(path).expanduser().resolve() for path in args.translated]
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise ValueError(f"Source must be an existing PDF: {source}")
    missing = [str(path) for path in outputs if not path.is_file() or path.suffix.lower() != ".pdf"]
    if missing:
        raise ValueError(f"Translated PDF not found: {', '.join(missing)}")
    selected_pages = selected_page_numbers(args.pages)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime = doctor_data(args.pdf2zh_cli)
    qa = make_qa(
        source,
        outputs,
        output_dir,
        args.profile,
        runtime["qa_tools"],
        args.qa_dpi,
        args.profile == "fidelity-review" or args.render,
        selected_pages,
    )
    write_qa_report(output_dir / "qa-report.md", qa, args.profile)
    payload = {"schema_version": 1, "generated_at": utc_now(), "profile": args.profile, "qa": qa}
    (output_dir / "qa-manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    run_manifest_path = output_dir / "run-manifest.json"
    if run_manifest_path.is_file():
        run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
        run_manifest["qa"] = qa
        if run_manifest.get("exit_code") == 0:
            run_manifest["status"] = "completed" if qa["structural_status"] != "failed" else "completed_with_structural_failure"
        run_manifest_path.write_text(
            json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 4 if qa["structural_status"] == "failed" else 0


def translate_command(args: argparse.Namespace) -> int:
    source = Path(args.pdf).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise ValueError(f"Source must be an existing PDF: {source}")
    if args.no_mono and args.no_dual:
        raise ValueError("Cannot combine --no-mono and --no-dual")
    selected_pages = selected_page_numbers(args.pages)

    args.glossary = [Path(path).expanduser().resolve() for path in args.glossary]
    for glossary in args.glossary:
        validate_glossary(glossary)
    args.extra_tokens = parse_extra_args(args.extra_arg)

    runtime = doctor_data(args.pdf2zh_cli)
    cli = runtime["pdf2zh"]["path"]
    if not cli:
        raise RuntimeError("pdf2zh CLI not found. Run doctor or bootstrap_pdf2zh.py first.")
    output_dir = Path(args.output_dir).expanduser().resolve()
    command = build_command(args, cli, source, output_dir)
    if args.dry_run:
        print(json.dumps({"command": redacted_command(command), "runtime": runtime}, ensure_ascii=False, indent=2))
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    started_epoch = time.time()
    result = subprocess.run(command, check=False)
    finished_at = utc_now()
    candidates = sorted(
        path
        for path in output_dir.glob("*.pdf")
        if path.resolve() != source and path.stat().st_mtime >= started_epoch - 2
    )

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "failed" if result.returncode else "completed",
        "profile": args.profile,
        "engine": args.engine,
        "source": {"path": str(source), "bytes": source.stat().st_size, "sha256": sha256(source)},
        "output_dir": str(output_dir),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round(time.time() - started_epoch, 3),
        "exit_code": result.returncode,
        "command": redacted_command(command),
        "runtime": runtime,
    }
    if result.returncode == 0 and not candidates:
        manifest["status"] = "failed_no_output"
    if candidates:
        qa = make_qa(
            source,
            candidates,
            output_dir,
            args.profile,
            runtime["qa_tools"],
            args.qa_dpi,
            args.profile == "fidelity-review" or args.render,
            selected_pages,
        )
        manifest["qa"] = qa
        write_qa_report(output_dir / "qa-report.md", qa, args.profile)
        if qa["structural_status"] == "failed":
            manifest["status"] = "completed_with_structural_failure"
    (output_dir / "run-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if result.returncode:
        return result.returncode
    if not candidates:
        return 5
    return 4 if manifest["status"] == "completed_with_structural_failure" else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Translate academic PDFs through PDFMathTranslate-next/BabelDOC.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check translation and fidelity-review tooling.")
    doctor.add_argument("--pdf2zh-cli")
    doctor.set_defaults(handler=doctor_command)

    qa = subparsers.add_parser("qa", help="Run structural and render QA on existing translated PDFs.")
    qa.add_argument("pdf")
    qa.add_argument("--translated", action="append", required=True)
    qa.add_argument("--output-dir", required=True)
    qa.add_argument("--profile", choices=("quick-read", "fidelity-review"), default="fidelity-review")
    qa.add_argument("--pages", help="Source pages that were selected for translation.")
    qa.add_argument("--pdf2zh-cli")
    qa.add_argument("--render", action="store_true")
    qa.add_argument("--qa-dpi", type=int, default=120)
    qa.set_defaults(handler=qa_command)

    translate = subparsers.add_parser("translate", help="Translate one academic PDF and write QA artifacts.")
    translate.add_argument("pdf")
    translate.add_argument("--output-dir", required=True)
    translate.add_argument("--profile", choices=("quick-read", "fidelity-review"), default="quick-read")
    translate.add_argument("--pdf2zh-cli")
    translate.add_argument("--engine", choices=tuple(ENGINE_FLAGS), default="siliconflowfree")
    translate.add_argument("--config-file")
    translate.add_argument("--glossary", action="append", default=[])
    translate.add_argument("--lang-in", default="en")
    translate.add_argument("--lang-out", default="zh")
    translate.add_argument("--pages", help="Page range accepted by pdf2zh-next, for example 1-5,8.")
    translate.add_argument("--custom-prompt-file")
    translate.add_argument("--extra-arg", action="append", default=[], help="One non-secret pdf2zh argument string.")
    translate.add_argument("--ignore-cache", action="store_true")
    translate.add_argument("--scanned", action="store_true")
    translate.add_argument("--no-mono", action="store_true")
    translate.add_argument("--no-dual", action="store_true")
    translate.add_argument("--render", action="store_true", help="Render pages even in quick-read mode.")
    translate.add_argument("--qa-dpi", type=int, default=120)
    translate.add_argument("--dry-run", action="store_true")
    translate.set_defaults(handler=translate_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
