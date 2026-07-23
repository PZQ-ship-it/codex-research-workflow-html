"""Check the local prerequisites for PDF two-column reconstruction."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def command_info(name: str) -> dict[str, object]:
    path = shutil.which(name)
    return {"available": path is not None, "path": path}


def babeldoc_info() -> dict[str, object]:
    candidates = [os.environ.get("BABELDOC_PYTHON"), sys.executable]
    for candidate in candidates:
        if not candidate:
            continue
        path = shutil.which(candidate) or candidate
        if not Path(path).exists():
            continue
        probe = subprocess.run(
            [path, "-c", "import babeldoc; print(babeldoc.__version__)"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if probe.returncode == 0:
            return {"available": True, "python": str(Path(path).resolve()), "version": probe.stdout.strip()}
    return {"available": False, "python": os.environ.get("BABELDOC_PYTHON")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="保持 JSON 输出（默认也是 JSON）")
    args = parser.parse_args()

    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "commands": {
            name: command_info(name)
            for name in ("pdfinfo", "pdftotext", "pdftoppm", "pandoc", "xelatex")
        },
        "python_modules": {
            name: importlib.util.find_spec(name) is not None
            for name in ("win32com", "pythoncom", "fitz", "docling", "pdf2docx", "marker", "babeldoc")
        },
        "babeldoc": babeldoc_info(),
    }

    if sys.platform == "win32" and report["python_modules"]["win32com"]:
        try:
            import win32com.client

            word = win32com.client.DispatchEx("Word.Application")
            try:
                report["word"] = {
                    "available": True,
                    "version": str(word.Version),
                    "build": str(word.Build),
                }
            finally:
                word.Quit()
        except Exception as exc:  # pragma: no cover - depends on local Office
            report["word"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    else:
        report["word"] = {"available": False, "reason": "Windows + pywin32 required"}

    docling_ok = bool(report["python_modules"].get("docling")) and all(
        report["commands"][name]["available"]
        for name in ("pandoc", "xelatex", "pdfinfo", "pdftotext", "pdftoppm")
    )
    word_ok = bool(report.get("word", {}).get("available"))
    report["recommended_backend"] = (
        "docling-markdown-xelatex" if docling_ok else ("word-com" if word_ok else None)
    )
    report["docling_backend_ready"] = docling_ok
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if docling_ok or word_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
