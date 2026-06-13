#!/usr/bin/env python3
"""Small utilities for evaluating Codex skills without external dependencies."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|bearer)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{20,}"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], List[str]]:
    lines = text.splitlines()
    issues: List[str] = []
    if not lines or lines[0].strip() != "---":
        return {}, ["SKILL.md must start with YAML frontmatter"]
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}, ["SKILL.md frontmatter is not closed with ---"]
    data: Dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            issues.append(f"Unparseable frontmatter line: {raw}")
            continue
        key, value = raw.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data, issues


def parse_simple_yaml_lines(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not path.exists():
        return result
    for raw in read_text(path).splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        result[key.strip()] = value.strip().strip("\"'")
    return result


def static_check(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    skill_md = skill_dir / "SKILL.md"
    errors: List[str] = []
    warnings: List[str] = []

    if not skill_md.exists():
        errors.append("SKILL.md missing")
        return print_result({"ok": False, "errors": errors, "warnings": warnings})

    text = read_text(skill_md)
    frontmatter, fm_issues = parse_frontmatter(text)
    errors.extend(fm_issues)

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if not name:
        errors.append("frontmatter.name missing")
    if not description:
        errors.append("frontmatter.description missing")
    if name and name != skill_dir.name:
        warnings.append(f"frontmatter.name '{name}' differs from folder '{skill_dir.name}'")
    if name and not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        errors.append("frontmatter.name must use lowercase letters, digits, and hyphens")
    if description and len(description) < 80:
        warnings.append("description may be too short for reliable implicit triggering")
    if "TODO" in text or "[TODO" in text:
        errors.append("TODO scaffold text remains")
    if SECRET_RE.search(text):
        errors.append("secret-looking value found in SKILL.md")

    for child in skill_dir.rglob("*"):
        if child.is_file() and child.name.lower() not in {".env", "cookies.json"}:
            try:
                child_text = read_text(child)
            except UnicodeDecodeError:
                continue
            if SECRET_RE.search(child_text):
                errors.append(f"secret-looking value found in {child.relative_to(skill_dir)}")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists():
        data = parse_simple_yaml_lines(openai_yaml)
        short = data.get("short_description", "")
        default_prompt = data.get("default_prompt", "")
        if short and not (25 <= len(short) <= 64):
            errors.append("agents/openai.yaml short_description must be 25-64 characters")
        if name and default_prompt and f"${name}" not in default_prompt:
            errors.append("agents/openai.yaml default_prompt must include literal $skill-name")
        if "TODO" in read_text(openai_yaml):
            errors.append("TODO scaffold text remains in agents/openai.yaml")

    result = {
        "ok": not errors,
        "skill_dir": str(skill_dir),
        "name": name,
        "errors": errors,
        "warnings": warnings,
    }
    return print_result(result)


def init_eval(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "artifacts").mkdir(exist_ok=True)

    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        frontmatter, _ = parse_frontmatter(read_text(skill_md))
        name = frontmatter.get("name", name)

    prompts_path = out_dir / "prompts.csv"
    if not prompts_path.exists():
        with prompts_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "should_trigger", "prompt", "expected_artifacts", "notes"])
            writer.writerow(["direct-01", "true", f"Use ${name} to evaluate this skill folder.", "", "Direct invocation"])
            writer.writerow(["implicit-01", "true", "Evaluate whether this Codex skill triggers correctly and follows its workflow.", "", "Implicit target scenario"])
            writer.writerow(["negative-01", "false", "Polish the prose in this Markdown note without changing workflow behavior.", "", "Adjacent non-skill task"])

    schema_path = out_dir / "style-rubric.schema.json"
    if not schema_path.exists():
        schema = {
            "type": "object",
            "properties": {
                "overall_pass": {"type": "boolean"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "checks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "pass": {"type": "boolean"},
                            "notes": {"type": "string"},
                        },
                        "required": ["id", "pass", "notes"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["overall_pass", "score", "checks"],
            "additionalProperties": False,
        }
        schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

    return print_result(
        {
            "ok": True,
            "skill": name,
            "out_dir": str(out_dir),
            "files": [str(prompts_path), str(schema_path), str(out_dir / "artifacts")],
        }
    )


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as fh:
        for line_no, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                yield {"type": "parse_error", "line": line_no, "error": str(exc)}
                continue
            if isinstance(value, dict):
                yield value


def extract_commands(event: Dict[str, Any]) -> List[str]:
    commands: List[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            item_type = str(value.get("type", ""))
            command = value.get("command") or value.get("cmd")
            if isinstance(command, str) and (item_type in {"command_execution", "exec_command", ""}):
                commands.append(command)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(event)
    return commands


def summarize_trace(args: argparse.Namespace) -> int:
    trace_path = Path(args.trace).resolve()
    workspace = Path(args.workspace).resolve() if args.workspace else Path.cwd()
    events = list(iter_jsonl(trace_path))
    commands: List[str] = []
    parse_errors = [e for e in events if e.get("type") == "parse_error"]
    usage: Dict[str, Any] = {}

    for event in events:
        commands.extend(extract_commands(event))
        if isinstance(event.get("usage"), dict):
            usage.update(event["usage"])
        if isinstance(event.get("item"), dict) and isinstance(event["item"].get("usage"), dict):
            usage.update(event["item"]["usage"])

    checks: List[Dict[str, Any]] = []
    ok = True

    for required in args.require_command:
        passed = any(required in command for command in commands)
        checks.append({"id": f"require-command:{required}", "pass": passed})
        ok = ok and passed

    for required_file in args.require_file:
        path = Path(required_file)
        if not path.is_absolute():
            path = workspace / path
        passed = path.exists()
        checks.append({"id": f"require-file:{required_file}", "pass": passed})
        ok = ok and passed

    if args.max_commands is not None:
        passed = len(commands) <= args.max_commands
        checks.append({"id": "max-commands", "pass": passed, "value": len(commands), "limit": args.max_commands})
        ok = ok and passed

    if parse_errors:
        ok = False
        checks.append({"id": "jsonl-parse", "pass": False, "errors": parse_errors[:5]})

    result = {
        "ok": ok,
        "trace": str(trace_path),
        "event_count": len(events),
        "command_count": len(commands),
        "commands": commands,
        "usage": usage,
        "checks": checks,
    }
    return print_result(result)


def print_result(result: Dict[str, Any]) -> int:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Codex skill structure and run traces.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_static = sub.add_parser("static-check", help="Check a skill folder for common structural issues.")
    p_static.add_argument("skill_dir")
    p_static.set_defaults(func=static_check)

    p_init = sub.add_parser("init-eval", help="Create a starter eval pack for a skill.")
    p_init.add_argument("--skill-dir", required=True)
    p_init.add_argument("--out-dir", required=True)
    p_init.set_defaults(func=init_eval)

    p_trace = sub.add_parser("summarize-trace", help="Summarize a codex exec --json JSONL trace.")
    p_trace.add_argument("trace")
    p_trace.add_argument("--workspace")
    p_trace.add_argument("--require-command", action="append", default=[])
    p_trace.add_argument("--require-file", action="append", default=[])
    p_trace.add_argument("--max-commands", type=int)
    p_trace.set_defaults(func=summarize_trace)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
