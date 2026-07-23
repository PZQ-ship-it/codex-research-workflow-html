"""Batch-export DOCX (or explicitly tested PDF imports) as two-column PDFs.

The script intentionally does not overwrite an input or an existing output by
default. It uses a fresh Word COM instance and writes a JSON manifest.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PDF_FORMAT = 17  # wdExportFormatPDF


def pdf_pages(path: Path) -> int | None:
    tool = shutil.which("pdfinfo")
    if not tool:
        return None
    try:
        proc = subprocess.run(
            [tool, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    except OSError:
        return None
    for line in proc.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def output_path(source: Path, output_dir: Path, suffix: str) -> Path:
    return output_dir / f"{source.stem}{suffix}.pdf"


def convert_one(word: Any, source: Path, destination: Path, allow_pdf_import: bool) -> dict[str, Any]:
    started = time.time()
    row: dict[str, Any] = {
        "source": str(source),
        "output": str(destination),
        "source_type": source.suffix.lower().lstrip("."),
        "status": "failed",
    }
    if source.suffix.lower() == ".pdf" and not allow_pdf_import:
        row["error"] = "PDF import is opt-in; pass --allow-pdf-import after a manual pilot"
        return row
    if destination.exists():
        row["error"] = "output exists; use --overwrite to replace it"
        return row

    doc = None
    try:
        # Named arguments avoid PowerShell/pywin32 positional-variant issues.
        doc = word.Documents.Open(
            FileName=str(source),
            ConfirmConversions=False,
            ReadOnly=source.suffix.lower() != ".pdf",
            AddToRecentFiles=False,
            Visible=False,
        )
        before = [int(section.PageSetup.TextColumns.Count) for section in doc.Sections]
        for section in doc.Sections:
            section.PageSetup.TextColumns.SetCount(2)
        after = [int(section.PageSetup.TextColumns.Count) for section in doc.Sections]
        doc.ExportAsFixedFormat(OutputFileName=str(destination), ExportFormat=PDF_FORMAT, OpenAfterExport=False)
        if not destination.exists() or destination.stat().st_size == 0:
            raise RuntimeError("Word returned without creating a non-empty PDF")
        row.update(
            {
                "status": "ok",
                "sections": len(before),
                "columns_before": before,
                "columns_after": after,
                "output_bytes": destination.stat().st_size,
                "output_pages": pdf_pages(destination),
            }
        )
    except Exception as exc:  # pragma: no cover - COM failures are environment-specific
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if doc is not None:
            try:
                doc.Close(0)
            except Exception:
                pass
    row["elapsed_seconds"] = round(time.time() - started, 3)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="单个 DOCX/PDF 或包含它们的目录")
    parser.add_argument("--output", required=True, help="独立输出目录")
    parser.add_argument("--max-files", type=int, default=0, help="最多处理多少个文件，0 表示全部")
    parser.add_argument("--suffix", default="_2col", help="输出文件名后缀")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖同名输出")
    parser.add_argument(
        "--allow-pdf-import",
        action="store_true",
        help="显式允许 Word 直接导入 PDF；可能受 Office 转换器/无界面模式影响",
    )
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    if not source.exists():
        parser.error(f"input does not exist: {source}")
    if source.is_dir():
        files = sorted(p for p in source.rglob("*") if p.suffix.lower() in {".docx", ".pdf"})
    else:
        files = [source] if source.suffix.lower() in {".docx", ".pdf"} else []
    if args.max_files > 0:
        files = files[: args.max_files]
    if not files:
        parser.error("no DOCX/PDF inputs found")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        print(f"Word COM requires pywin32: {exc}", file=sys.stderr)
        return 2

    pythoncom.CoInitialize()
    word = None
    rows: list[dict[str, Any]] = []
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        for item in files:
            destination = output_path(item, output_dir, args.suffix)
            if args.overwrite and destination.exists():
                # Avoid a destructive delete; Word's export will replace it only
                # after the caller explicitly opted in.
                destination.unlink()
            rows.append(convert_one(word, item, destination, args.allow_pdf_import))
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()

    manifest = {
        "input": str(source),
        "output": str(output_dir),
        "allow_pdf_import": args.allow_pdf_import,
        "file_count": len(rows),
        "success_count": sum(row["status"] == "ok" for row in rows),
        "files": rows,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["success_count"] == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
