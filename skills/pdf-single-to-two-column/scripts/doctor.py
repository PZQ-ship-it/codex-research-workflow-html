"""Check the local prerequisites for PDF two-column reconstruction."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path


def command_info(name: str) -> dict[str, object]:
    path = shutil.which(name)
    return {"available": path is not None, "path": path}


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
            for name in ("win32com", "pythoncom", "fitz", "docling", "pdf2docx", "marker")
        },
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

    print(json.dumps(report, ensure_ascii=False, indent=2))
    word_ok = bool(report.get("word", {}).get("available"))
    return 0 if word_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
