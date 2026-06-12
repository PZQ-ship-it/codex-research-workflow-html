#!/usr/bin/env python3
"""Inspect and log minimal environment smoke checks for paper reproduction repos."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_NAMES = [
    "environment.yml",
    "environment.yaml",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "poetry.lock",
    "conda-lock.yml",
    "Dockerfile",
]

ENTRY_NAMES = [
    "train.py",
    "main.py",
    "eval.py",
    "evaluate.py",
    "test.py",
    "run.py",
    "demo.py",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def find_files(root: Path, names: list[str]) -> list[Path]:
    hits: list[Path] = []
    lowered = {name.lower() for name in names}
    for path in root.rglob("*"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_file() and path.name.lower() in lowered:
            hits.append(path)
    return sorted(hits)


def find_tests(root: Path) -> list[Path]:
    hits: list[Path] = []
    for path in root.rglob("*"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_file() and (path.name.startswith("test_") or path.name.endswith("_test.py")):
            hits.append(path)
    return sorted(hits[:20])


def top_level_packages(root: Path) -> list[str]:
    packages: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if child.name in {"tests", "test", "docs", "examples", "scripts", "data", "datasets"}:
            continue
        if (child / "__init__.py").exists():
            packages.append(child.name)
    return packages[:10]


def candidate_setup_commands(manifests: list[Path], repo: Path) -> list[str]:
    names = {path.name.lower(): path for path in manifests}
    commands: list[str] = []
    env_file = names.get("environment.yml") or names.get("environment.yaml")
    if env_file:
        commands.append(f"conda env create -f {shlex.quote(rel(env_file, repo))}")
    if "requirements.txt" in names:
        commands.append("python -m venv .venv-repro")
        commands.append(".venv-repro\\Scripts\\python -m pip install -r requirements.txt")
    if "pyproject.toml" in names or "setup.py" in names or "setup.cfg" in names:
        commands.append("python -m pip install -e .")
    if "dockerfile" in names:
        commands.append("docker build -t paper-repro-smoke .")
    return commands


def candidate_smoke_commands(repo: Path, entries: list[Path], tests: list[Path], packages: list[str]) -> list[str]:
    commands: list[str] = []
    for package in packages[:3]:
        commands.append(f"python -c \"import {package}; print({package}.__name__)\"")
    for entry in entries[:8]:
        entry_rel = rel(entry, repo)
        commands.append(f"python {entry_rel} --help")
    if tests:
        commands.append("python -m pytest -q")
    commands.append("python -c \"import sys, platform; print(sys.version); print(platform.platform())\"")
    return commands


def write_plan_markdown(path: Path, plan: dict) -> None:
    lines = [
        "# Environment Smoke Report",
        "",
        "## Repository",
        "",
        f"- path: `{plan['repo']}`",
        f"- created_at: `{plan['created_at']}`",
        "",
        "## Detected Manifests",
        "",
    ]
    if plan["manifests"]:
        lines.extend(f"- `{item}`" for item in plan["manifests"])
    else:
        lines.append("- none detected")
    lines.extend(["", "## Candidate Setup Commands", ""])
    if plan["candidate_setup_commands"]:
        lines.extend(f"- `{item}`" for item in plan["candidate_setup_commands"])
    else:
        lines.append("- none detected")
    lines.extend(["", "## Candidate Smoke Commands", ""])
    if plan["candidate_smoke_commands"]:
        lines.extend(f"- `{item}`" for item in plan["candidate_smoke_commands"])
    else:
        lines.append("- none detected")
    lines.extend([
        "",
        "## Executed Commands",
        "",
        "- none yet",
        "",
        "## Blockers",
        "",
        "- not assessed",
        "",
        "## Verdict",
        "",
        "- not_enough_information",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def inspect_repo(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    if not repo.exists() or not repo.is_dir():
        raise SystemExit(f"Repository path not found or not a directory: {repo}")
    output_dir = Path(args.output_dir).resolve()
    ensure_dir(output_dir)

    manifests = find_files(repo, MANIFEST_NAMES)
    entries = find_files(repo, ENTRY_NAMES)
    tests = find_tests(repo)
    packages = top_level_packages(repo)
    plan = {
        "created_at": utc_now(),
        "repo": str(repo),
        "manifests": [rel(path, repo) for path in manifests],
        "entrypoints": [rel(path, repo) for path in entries],
        "tests": [rel(path, repo) for path in tests],
        "packages": packages,
        "candidate_setup_commands": candidate_setup_commands(manifests, repo),
        "candidate_smoke_commands": candidate_smoke_commands(repo, entries, tests, packages),
        "notes": [
            "Review commands before execution.",
            "Use an isolated environment; do not install into base Python.",
            "Treat successful smoke as environment viability only.",
        ],
    }
    (output_dir / "env_smoke_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    write_plan_markdown(output_dir / "env_smoke_report.md", plan)
    print(json.dumps(plan, indent=2))
    return 0


def env_probe(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).resolve()
    ensure_dir(output_dir)
    facts = {
        "created_at": utc_now(),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cwd": os.getcwd(),
        "frameworks": {},
    }
    for module in ["torch", "tensorflow", "jax", "numpy", "pandas", "sklearn"]:
        try:
            imported = __import__(module)
            facts["frameworks"][module] = getattr(imported, "__version__", "unknown")
        except Exception as exc:
            facts["frameworks"][module] = f"unavailable: {type(exc).__name__}"
    (output_dir / "env_probe.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
    print(json.dumps(facts, indent=2))
    return 0


def run_command(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    output_dir = Path(args.output_dir).resolve()
    log_dir = output_dir / "logs"
    ensure_dir(log_dir)
    started = time.time()
    proc = subprocess.run(
        args.command,
        cwd=str(repo),
        shell=True,
        text=True,
        capture_output=True,
        timeout=args.timeout,
    )
    duration = round(time.time() - started, 3)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = log_dir / f"command_{stamp}"
    base.with_suffix(".stdout.txt").write_text(proc.stdout or "", encoding="utf-8", errors="replace")
    base.with_suffix(".stderr.txt").write_text(proc.stderr or "", encoding="utf-8", errors="replace")
    record = {
        "created_at": utc_now(),
        "repo": str(repo),
        "command": args.command,
        "timeout": args.timeout,
        "duration_seconds": duration,
        "exit_code": proc.returncode,
        "stdout": str(base.with_suffix(".stdout.txt")),
        "stderr": str(base.with_suffix(".stderr.txt")),
    }
    base.with_suffix(".json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command_name", required=True)

    inspect_p = sub.add_parser("inspect", help="Inspect a repo and create env smoke plan artifacts.")
    inspect_p.add_argument("--repo", required=True)
    inspect_p.add_argument("--output-dir", required=True)
    inspect_p.set_defaults(func=inspect_repo)

    env_p = sub.add_parser("env", help="Capture current interpreter and common ML framework availability.")
    env_p.add_argument("--output-dir", required=True)
    env_p.set_defaults(func=env_probe)

    run_p = sub.add_parser("run", help="Run one explicit small smoke command with logs.")
    run_p.add_argument("--repo", required=True)
    run_p.add_argument("--output-dir", required=True)
    run_p.add_argument("--command", required=True)
    run_p.add_argument("--timeout", type=int, default=60)
    run_p.set_defaults(func=run_command)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except subprocess.TimeoutExpired as exc:
        print(f"command timed out after {exc.timeout} seconds", file=sys.stderr)
        return 124


if __name__ == "__main__":
    raise SystemExit(main())
