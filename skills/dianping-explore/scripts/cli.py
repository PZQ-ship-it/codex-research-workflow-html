#!/usr/bin/env python3
"""Thin wrapper for low-frequency Dianping crawler workflows."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_SOURCE_URL = "https://github.com/HDdssX/dianping_crawler.git"
DEFAULT_ROOT = (
    Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    / "Codex"
    / "dianping-explore"
    / "HDdssX_dianping_crawler"
)
REQUIRED_FILES = ("main.py", "config.py", "pw.py")
DEFAULT_COOKIE_ENV = "DIANPING_COOKIE"


def emit(payload: Dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def fail(message: str, **extra: Any) -> int:
    payload: Dict[str, Any] = {"ok": False, "error": message}
    payload.update(extra)
    return emit(payload, 1)


def resolve_root(value: str | None = None) -> Path:
    raw = value or os.environ.get("DIANPING_CRAWLER_ROOT")
    return Path(raw).expanduser().resolve() if raw else DEFAULT_ROOT


def find_python(root: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    if os.name == "nt":
        candidate = root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = root / ".venv" / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    return sys.executable


def crawler_status(root: Path, cookie_env: str = DEFAULT_COOKIE_ENV) -> Dict[str, Any]:
    files = {name: (root / name).exists() for name in REQUIRED_FILES}
    venv_python = (
        root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    return {
        "root": str(root),
        "exists": root.exists(),
        "required_files": files,
        "ready": root.exists() and all(files.values()),
        "venv_python": str(venv_python) if venv_python.exists() else None,
        "cookie_env": cookie_env,
        "cookie_configured": bool(os.environ.get(cookie_env)),
    }


def ensure_ready(root: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (root / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"crawler root is missing required files: {', '.join(missing)}"
        )


def run(cmd: List[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def redact_config_cookie(root: Path) -> bool:
    config_path = root / "config.py"
    if not config_path.exists():
        return False
    text = config_path.read_text(encoding="utf-8", errors="replace")
    redacted = re.sub(
        r"(?m)^COOKIES\s*=\s*(['\"]).*?\1\s*$",
        'COOKIES = ""',
        text,
        count=1,
    )
    if redacted != text:
        config_path.write_text(redacted, encoding="utf-8")
        return True
    return False


def cmd_setup_source(args: argparse.Namespace) -> int:
    root = resolve_root(args.target)
    if root.exists() and any(root.iterdir()):
        status = crawler_status(root)
        if status["ready"] and not args.force:
            return emit({"ok": True, "action": "reuse-existing", "status": status})
        if not args.force:
            return fail(
                "target exists but is not a ready crawler checkout; pass --force to use it anyway or choose another --target",
                status=status,
            )

    root.parent.mkdir(parents=True, exist_ok=True)
    if not root.exists():
        if shutil.which("git") is None:
            return fail("git is required to clone the third-party crawler")
        clone = run(["git", "clone", "--depth", "1", args.source_url, str(root)])
        if clone.returncode != 0:
            return fail("git clone failed", stdout=clone.stdout, stderr=clone.stderr)

    redacted = False
    if not args.keep_upstream_config:
        redacted = redact_config_cookie(root)

    steps: List[Dict[str, Any]] = []
    if args.with_venv:
        venv_dir = root / ".venv"
        if not venv_dir.exists():
            created = run([sys.executable, "-m", "venv", str(venv_dir)])
            steps.append(
                {
                    "step": "create-venv",
                    "returncode": created.returncode,
                    "stderr_tail": created.stderr[-1000:],
                }
            )
            if created.returncode != 0:
                return fail("failed to create venv", steps=steps)
        py = find_python(root)
        install = run([py, "-m", "pip", "install", "playwright", "beautifulsoup4"], cwd=root)
        steps.append(
            {
                "step": "install-python-deps",
                "returncode": install.returncode,
                "stdout_tail": install.stdout[-1200:],
                "stderr_tail": install.stderr[-1200:],
            }
        )
        if install.returncode != 0:
            return fail("failed to install Python dependencies", steps=steps)
        if args.install_browser:
            browser = run([py, "-m", "playwright", "install", "chromium"], cwd=root)
            steps.append(
                {
                    "step": "install-playwright-browser",
                    "returncode": browser.returncode,
                    "stdout_tail": browser.stdout[-1200:],
                    "stderr_tail": browser.stderr[-1200:],
                }
            )
            if browser.returncode != 0:
                return fail("failed to install Playwright browser", steps=steps)

    return emit(
        {
            "ok": True,
            "source_url": args.source_url,
            "redacted_upstream_cookie": redacted,
            "status": crawler_status(root),
            "steps": steps,
        }
    )


def cmd_status(args: argparse.Namespace) -> int:
    return emit({"ok": True, "status": crawler_status(resolve_root(args.crawler_root), args.cookie_env)})


def split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def cmd_run_crawler(args: argparse.Namespace) -> int:
    root = resolve_root(args.crawler_root)
    try:
        ensure_ready(root)
    except FileNotFoundError as exc:
        return fail(str(exc), status=crawler_status(root, args.cookie_env))

    cookie = os.environ.get(args.cookie_env, "")
    if not cookie and not args.allow_empty_cookie:
        return fail(
            f"{args.cookie_env} is not set; provide cookies through an environment variable, not chat or command-line arguments",
            status=crawler_status(root, args.cookie_env),
        )

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    cities = split_csv(args.cities)
    if not cities:
        return fail("--cities must contain at least one city slug, for example Shanghai")

    main_args = [
        "main.py",
        "--keyword",
        args.keyword,
        "--max_pages",
        str(args.max_pages),
        "--comment_pages",
        str(args.comment_pages),
        "--output",
        str(output),
    ]
    py = find_python(root, args.python)

    launcher = textwrap.dedent(
        f"""
        import os
        import runpy
        import sys
        from pathlib import Path

        root = Path({json.dumps(str(root))})
        sys.path.insert(0, str(root))
        os.chdir(root)

        import config

        config.COOKIES = os.environ.get({json.dumps(args.cookie_env)}, "")
        config.CITIES = {json.dumps(cities, ensure_ascii=False)}
        sys.argv = {json.dumps(main_args, ensure_ascii=False)}
        runpy.run_path(str(root / "main.py"), run_name="__main__")
        """
    )

    if args.dry_run:
        return emit(
            {
                "ok": True,
                "dry_run": True,
                "python": py,
                "root": str(root),
                "main_args": main_args,
                "cities": cities,
                "cookie_env": args.cookie_env,
                "cookie_configured": bool(cookie),
                "output": str(output),
            }
        )

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
        handle.write(launcher)
        launcher_path = Path(handle.name)

    try:
        completed = subprocess.run([py, str(launcher_path)], cwd=str(root), env=env, check=False)
    finally:
        try:
            launcher_path.unlink()
        except OSError:
            pass

    return emit(
        {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "root": str(root),
            "output": str(output),
            "output_exists": output.exists(),
            "next": "Run normalize-csv on the output file if output_exists is true.",
        },
        0 if completed.returncode == 0 else 1,
    )


def normalize_row(row: Dict[str, str], source_file: Path, index: int) -> Dict[str, Any]:
    score_raw = row.get("Score") or row.get("score") or ""
    try:
        score: int | str | None = int(float(score_raw))
    except ValueError:
        score = score_raw or None
    return {
        "source": "dianping",
        "source_file": str(source_file),
        "row_index": index,
        "city": row.get("City") or row.get("city") or "",
        "shop_name": row.get("ShopName") or row.get("shop_name") or "",
        "user_name": row.get("User") or row.get("user_name") or "",
        "score": score,
        "published_at": row.get("Time") or row.get("published_at") or "",
        "content": (row.get("Content") or row.get("content") or "").strip(),
    }


def iter_csv(path: Path) -> Iterable[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def cmd_normalize_csv(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not input_path.exists():
        return fail("input CSV does not exist", input=str(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    shops = set()
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for index, row in enumerate(iter_csv(input_path), start=1):
            item = normalize_row(row, input_path, index)
            if item["shop_name"]:
                shops.add(item["shop_name"])
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    return emit(
        {
            "ok": True,
            "input": str(input_path),
            "output": str(output_path),
            "items": count,
            "shops": len(shops),
        }
    )


def cmd_schema(_: argparse.Namespace) -> int:
    return emit(
        {
            "ok": True,
            "schema": {
                "source": "constant: dianping",
                "source_file": "absolute path of the CSV source",
                "row_index": "1-based row number from the CSV",
                "city": "Dianping city slug/name from crawler output",
                "shop_name": "merchant display name",
                "user_name": "review author display name",
                "score": "integer star score when parseable",
                "published_at": "review time string from source",
                "content": "review text",
            },
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dianping Explore wrapper CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    setup = sub.add_parser("setup-source", help="clone and optionally prepare the third-party crawler")
    setup.add_argument("--source-url", default=DEFAULT_SOURCE_URL)
    setup.add_argument("--target", default=None)
    setup.add_argument("--with-venv", action="store_true")
    setup.add_argument("--install-browser", action="store_true")
    setup.add_argument("--force", action="store_true", help="allow an existing non-ready target")
    setup.add_argument("--keep-upstream-config", action="store_true", help="do not redact upstream sample COOKIES")
    setup.set_defaults(func=cmd_setup_source)

    status = sub.add_parser("status", help="inspect local crawler readiness")
    status.add_argument("--crawler-root", default=None)
    status.add_argument("--cookie-env", default=DEFAULT_COOKIE_ENV)
    status.set_defaults(func=cmd_status)

    run_parser = sub.add_parser("run-crawler", help="run the third-party crawler through a safe launcher")
    run_parser.add_argument("--crawler-root", default=None)
    run_parser.add_argument("--python", default=None)
    run_parser.add_argument("--keyword", required=True)
    run_parser.add_argument("--cities", required=True, help='comma-separated city slugs, for example "Shanghai,Beijing"')
    run_parser.add_argument("--max-pages", type=int, default=1)
    run_parser.add_argument("--comment-pages", type=int, default=1)
    run_parser.add_argument("--output", required=True)
    run_parser.add_argument("--cookie-env", default=DEFAULT_COOKIE_ENV)
    run_parser.add_argument("--allow-empty-cookie", action="store_true")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.set_defaults(func=cmd_run_crawler)

    normalize = sub.add_parser("normalize-csv", help="convert crawler CSV output to normalized JSONL")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--output", required=True)
    normalize.set_defaults(func=cmd_normalize_csv)

    schema = sub.add_parser("schema", help="print normalized JSONL schema")
    schema.set_defaults(func=cmd_schema)
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
