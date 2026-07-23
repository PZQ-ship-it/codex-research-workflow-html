"""Rebuild a PDF with Docling Markdown and a two-column XeLaTeX export.

The script keeps the intermediate Markdown, extracted picture assets, text
layout dump, rendered pages, and a manifest beside the output PDF. It is
intentionally single-file: callers can run it once for a pilot and then loop
over a directory after the pilot passes review.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def command_version(name: str) -> str | None:
    executable = shutil.which(name)
    if not executable:
        return None
    try:
        flag = "-v" if name in {"pdfinfo", "pdftotext", "pdftoppm"} else "--version"
        probe = subprocess.run(
            [executable, flag],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    output = (probe.stdout or probe.stderr).splitlines()
    return output[0].strip() if output else None


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def pdfinfo(path: Path) -> dict[str, Any]:
    executable = shutil.which("pdfinfo")
    if not executable:
        raise RuntimeError("pdfinfo is required")
    result = run([executable, str(path)])
    if result.returncode != 0:
        raise RuntimeError(f"pdfinfo failed: {result.stderr.strip()}")
    values: dict[str, Any] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip().lower().replace(" ", "_")] = value.strip()
    if "pages" in values:
        values["pages"] = int(values["pages"])
    return values


def page_numbers(selection: str) -> list[int]:
    pages: set[int] = set()
    for part in selection.split(","):
        item = part.strip()
        if not item:
            continue
        if "-" in item:
            start, end = (int(value) for value in item.split("-", 1))
            if start < 1 or end < start:
                raise ValueError(f"invalid page range: {item}")
            pages.update(range(start, end + 1))
        else:
            value = int(item)
            if value < 1:
                raise ValueError(f"invalid page number: {item}")
            pages.add(value)
    if not pages:
        raise ValueError("render page selection is empty")
    return sorted(pages)


def parse_pandoc_major(version: str | None) -> int:
    if not version:
        raise RuntimeError("pandoc is required")
    match = re.search(r"(\d+)\.", version)
    if not match:
        raise RuntimeError(f"cannot parse Pandoc version: {version}")
    return int(match.group(1))


def doctor() -> int:
    modules = {
        name: importlib.util.find_spec(name) is not None
        for name in ("docling", "docling_core")
    }
    commands = {
        name: {"available": shutil.which(name) is not None, "version": command_version(name)}
        for name in ("pandoc", "xelatex", "pdfinfo", "pdftotext", "pdftoppm")
    }
    report = {
        "python": sys.version.split()[0],
        "modules": modules,
        "commands": commands,
        "docling_version": package_version("docling"),
        "recommended_backend_ready": all(modules.values())
        and all(commands[name]["available"] for name in commands),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["recommended_backend_ready"] else 2


def export_markdown(source: Path, markdown: Path, assets_dir: Path) -> list[str]:
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling_core.types.doc import ImageRefMode

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = False
    pipeline_options.generate_picture_images = True
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    result = converter.convert(str(source))
    result.document.save_as_markdown(
        markdown,
        artifacts_dir=assets_dir,
        image_mode=ImageRefMode.REFERENCED,
    )
    return [
        str(path.relative_to(assets_dir))
        for path in sorted(assets_dir.rglob("*"))
        if path.is_file()
    ]


def convert(args: argparse.Namespace) -> int:
    source = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown = output_dir / f"{source.stem}.docling.md"
    assets_dir = output_dir / "assets"
    output_pdf = output_dir / f"{source.stem}_2col.pdf"
    text_dump = output_dir / f"{source.stem}_2col.layout.txt"
    manifest_path = output_dir / "manifest.json"
    render_dir = output_dir / "render"
    started = time.time()

    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise ValueError(f"input must be an existing PDF: {source}")
    if output_pdf.exists() and not args.overwrite:
        raise FileExistsError(f"output exists; use --overwrite: {output_pdf}")
    for executable in ("pandoc", "xelatex", "pdfinfo", "pdftotext"):
        if not shutil.which(executable):
            raise RuntimeError(f"required command is unavailable: {executable}")
    if not args.no_render and not shutil.which("pdftoppm"):
        raise RuntimeError("pdftoppm is required unless --no-render is used")

    manifest: dict[str, Any] = {
        "status": "running",
        "backend": "docling-markdown-xelatex",
        "input": str(source),
        "input_sha256": sha256(source),
        "output_dir": str(output_dir),
        "markdown": str(markdown),
        "assets_dir": str(assets_dir),
        "output_pdf": str(output_pdf),
        "text_dump": str(text_dump),
        "pipeline": {
            "do_ocr": False,
            "do_table_structure": False,
            "generate_picture_images": True,
            "image_mode": "referenced",
        },
        "review_gate": "pending_manual_visual_review",
    }

    try:
        input_info = pdfinfo(source)
        manifest["input_pdfinfo"] = input_info
        assets_dir.mkdir(parents=True, exist_ok=True)
        artifact_files = export_markdown(source, markdown, assets_dir)
        markdown_text = markdown.read_text(encoding="utf-8")
        if not markdown_text.strip():
            raise RuntimeError("Docling produced an empty Markdown file")
        manifest.update(
            {
                "docling_version": package_version("docling"),
                "markdown_sha256": sha256(markdown),
                "markdown_chars": len(markdown_text),
                "artifact_files": artifact_files,
            }
        )

        pandoc_version = command_version("pandoc")
        major = parse_pandoc_major(pandoc_version)
        engine_flag = "--latex-engine=xelatex" if major < 2 else "--pdf-engine=xelatex"
        page_size = str(input_info.get("page_size", "")).lower()
        variables = [
            "-V",
            "classoption=twocolumn",
            "-V",
            f"CJKmainfont={args.cjk_font}",
            "-V",
            "geometry:margin=0.55in",
        ]
        if "612 x 792" in page_size:
            variables.extend(["-V", "papersize=letter"])
        elif "595 x 842" in page_size:
            variables.extend(["-V", "papersize=a4"])
        command = [
            shutil.which("pandoc") or "pandoc",
            "-f",
            "markdown",
            "-t",
            "latex",
            engine_flag,
            *variables,
            "-o",
            str(output_pdf),
            str(markdown),
        ]
        pandoc_result = run(command, cwd=output_dir)
        (output_dir / "pandoc.log").write_text(
            (pandoc_result.stdout or "") + (pandoc_result.stderr or ""),
            encoding="utf-8",
        )
        if pandoc_result.returncode != 0 or not output_pdf.exists() or output_pdf.stat().st_size == 0:
            raise RuntimeError(f"Pandoc/XeLaTeX failed; inspect {output_dir / 'pandoc.log'}")

        text_result = run(
            [
                shutil.which("pdftotext") or "pdftotext",
                "-enc",
                "UTF-8",
                "-layout",
                str(output_pdf),
                str(text_dump),
            ]
        )
        if text_result.returncode != 0 or not text_dump.exists():
            raise RuntimeError(f"pdftotext failed: {text_result.stderr.strip()}")

        rendered: list[str] = []
        if not args.no_render:
            render_dir.mkdir(parents=True, exist_ok=True)
            output_pages = int(pdfinfo(output_pdf).get("pages", 0))
            for page in page_numbers(args.render_pages):
                if page > output_pages:
                    continue
                prefix = render_dir / f"page-{page}"
                render_result = run(
                    [
                        shutil.which("pdftoppm") or "pdftoppm",
                        "-png",
                        "-r",
                        str(args.render_dpi),
                        "-f",
                        str(page),
                        "-l",
                        str(page),
                        "-singlefile",
                        str(output_pdf),
                        str(prefix),
                    ]
                )
                if render_result.returncode != 0:
                    raise RuntimeError(
                        f"pdftoppm failed for page {page}: {render_result.stderr.strip()}"
                    )
                rendered.append(str(prefix.with_suffix(".png")))

        output_info = pdfinfo(output_pdf)
        manifest.update(
            {
                "status": "ok",
                "pandoc_version": pandoc_version,
                "xelatex_version": command_version("xelatex"),
                "pandoc_command": command,
                "output_sha256": sha256(output_pdf),
                "output_bytes": output_pdf.stat().st_size,
                "output_pdfinfo": output_info,
                "text_dump_chars": len(
                    text_dump.read_text(encoding="utf-8", errors="replace")
                ),
                "rendered_pages": rendered,
                "elapsed_seconds": round(time.time() - started, 3),
            }
        )
    except Exception as exc:
        manifest.update(
            {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "elapsed_seconds": round(time.time() - started, 3),
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="check the Docling/XeLaTeX prerequisites")
    convert_parser = subparsers.add_parser(
        "convert", help="run one auditable PDF reconstruction"
    )
    convert_parser.add_argument(
        "--input", required=True, help="source PDF; it is never overwritten"
    )
    convert_parser.add_argument("--output-dir", required=True, help="new output directory")
    convert_parser.add_argument(
        "--render-pages", default="1", help="pages to render, e.g. 1,2,5-6"
    )
    convert_parser.add_argument("--render-dpi", type=int, default=150)
    convert_parser.add_argument("--cjk-font", default="Microsoft YaHei")
    convert_parser.add_argument("--no-render", action="store_true")
    convert_parser.add_argument("--overwrite", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "doctor":
        return doctor()
    return convert(args)


if __name__ == "__main__":
    raise SystemExit(main())
