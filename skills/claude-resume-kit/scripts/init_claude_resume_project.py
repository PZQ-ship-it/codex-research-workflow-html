#!/usr/bin/env python3
"""Copy the bundled Claude Resume Kit scaffold into a working directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


EXCLUDE_DIRS = {".git", "__pycache__"}
EXCLUDE_SUFFIXES = {".pyc"}


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    return path.suffix in EXCLUDE_SUFFIXES


def copy_tree(src: Path, dst: Path, overwrite: bool) -> None:
    if dst.exists() and any(dst.iterdir()) and not overwrite:
        raise SystemExit(f"Destination is not empty: {dst}")
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        if should_skip(rel):
            continue
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not overwrite:
                raise SystemExit(f"File exists, use --overwrite: {target}")
            shutil.copy2(item, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", help="Working directory to create or update")
    parser.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parents[1] / "assets" / "upstream-project"),
        help="Scaffold source directory",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    src = Path(args.source).resolve()
    dst = Path(args.destination).resolve()
    if not src.exists():
        raise SystemExit(f"Source scaffold not found: {src}")
    copy_tree(src, dst, args.overwrite)
    print(f"Copied Claude Resume Kit scaffold to {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
