#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def venv_paths(root: Path) -> tuple[Path, Path]:
    if os.name == "nt":
        return root / "Scripts" / "python.exe", root / "Scripts" / "pdf2zh.exe"
    return root / "bin" / "python", root / "bin" / "pdf2zh"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install pdf2zh-next into an isolated virtual environment.")
    parser.add_argument("--venv", required=True)
    parser.add_argument("--version", default="2.9.0")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.venv).expanduser().resolve()
    python_exe, cli = venv_paths(root)
    commands: list[list[str]] = []
    if not python_exe.is_file():
        commands.append([str(Path(args.python).resolve()), "-m", "venv", str(root)])
    commands.append(
        [
            str(python_exe),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--quiet",
            f"pdf2zh-next=={args.version}",
        ]
    )

    if args.dry_run:
        print(json.dumps({"venv": str(root), "commands": commands}, indent=2))
        return 0

    root.parent.mkdir(parents=True, exist_ok=True)
    for command in commands:
        result = subprocess.run(command, check=False)
        if result.returncode:
            return result.returncode
    if not cli.is_file():
        print(f"error: installation completed but CLI was not found at {cli}", file=sys.stderr)
        return 3
    version = subprocess.run([str(cli), "--version"], check=False, capture_output=True, text=True, errors="replace")
    version_text = (version.stdout + "\n" + version.stderr).strip()
    version_match = re.search(r"pdf2zh(?:-next)?\s+version:\s*([^\s]+)", version_text, re.IGNORECASE)
    print(
        json.dumps(
            {
                "status": "ready",
                "venv": str(root),
                "python": str(python_exe),
                "pdf2zh_cli": str(cli),
                "requested_version": args.version,
                "pdf2zh_next_version": version_match.group(1) if version_match else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
