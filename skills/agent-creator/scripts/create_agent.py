#!/usr/bin/env python3
"""Create and validate Codex native custom agent TOML files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


REQUIRED = ("name", "description", "developer_instructions")


def snake_case(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    value = re.sub(r"_+", "_", value).strip("_").lower()
    if not value:
        raise ValueError("name normalizes to an empty value")
    if value[0].isdigit():
        value = f"agent_{value}"
    return value


def kebab_case(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", value.strip())
    value = re.sub(r"-+", "-", value).strip("-").lower()
    if not value:
        raise ValueError("filename normalizes to an empty value")
    if value[0].isdigit():
        value = f"agent-{value}"
    return value


def toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def toml_multiline(value: str) -> str:
    value = value.replace('"""', '\\"\\"\\"').rstrip() + "\n"
    return f'"""\n{value}"""'


def read_text_arg(value: str | None, path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8-sig")
    if value:
        return value
    raise ValueError("provide --instructions or --instructions-file")


def build_toml(args: argparse.Namespace) -> str:
    name = snake_case(args.name)
    lines = [
        f"name = {toml_string(name)}",
        f"description = {toml_string(args.description.strip())}",
    ]
    if args.model:
        lines.append(f"model = {toml_string(args.model.strip())}")
    if args.reasoning_effort:
        lines.append(f"model_reasoning_effort = {toml_string(args.reasoning_effort.strip())}")
    if args.sandbox_mode:
        lines.append(f"sandbox_mode = {toml_string(args.sandbox_mode.strip())}")
    if args.nickname:
        nicknames = ", ".join(toml_string(n.strip()) for n in args.nickname if n.strip())
        lines.append(f"nickname_candidates = [{nicknames}]")
    lines.append(f"developer_instructions = {toml_multiline(read_text_arg(args.instructions, args.instructions_file))}")
    return "\n".join(lines) + "\n"


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"{path}: TOML parse failed: {exc}"]
    for field in REQUIRED:
        if not isinstance(data.get(field), str) or not data.get(field, "").strip():
            errors.append(f"{path}: missing or empty {field}")
    name = data.get("name", "")
    if isinstance(name, str) and name:
        normalized = snake_case(name)
        if name != normalized:
            errors.append(f"{path}: name should be snake_case: {normalized}")
    if "sandbox_mode" in data and data["sandbox_mode"] not in {"read-only", "workspace-write", "danger-full-access"}:
        errors.append(f"{path}: unsupported sandbox_mode {data['sandbox_mode']!r}")
    return errors


def iter_toml_targets(target: Path) -> list[Path]:
    if target.is_dir():
        return sorted(target.glob("*.toml"))
    return [target]


def cmd_create(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = args.filename or f"{kebab_case(args.name)}.toml"
    if not filename.endswith(".toml"):
        filename += ".toml"
    output_path = output_dir / filename
    output_path.write_text(build_toml(args), encoding="utf-8")
    errors = validate_file(output_path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(output_path)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    targets: list[Path] = []
    for raw in args.targets:
        targets.extend(iter_toml_targets(Path(raw)))
    if not targets:
        print("No TOML files found.", file=sys.stderr)
        return 1
    all_errors: list[str] = []
    for target in targets:
        errors = validate_file(target)
        if errors:
            all_errors.extend(errors)
        else:
            data = tomllib.loads(target.read_text(encoding="utf-8"))
            print(f"OK {target} name={data['name']}")
    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a native custom agent TOML")
    create.add_argument("--name", required=True, help="agent name; normalized to snake_case")
    create.add_argument("--description", required=True, help="routing description")
    create.add_argument("--instructions", help="developer instructions text")
    create.add_argument("--instructions-file", help="file containing developer instructions")
    create.add_argument("--output-dir", required=True, help="target agents directory")
    create.add_argument("--filename", help="optional TOML filename")
    create.add_argument("--nickname", action="append", help="optional nickname candidate; repeatable")
    create.add_argument("--model", help="optional model override")
    create.add_argument("--reasoning-effort", choices=["low", "medium", "high", "xhigh"], help="optional reasoning effort")
    create.add_argument("--sandbox-mode", choices=["read-only", "workspace-write", "danger-full-access"], help="optional sandbox mode")
    create.set_defaults(func=cmd_create)

    validate = sub.add_parser("validate", help="validate one TOML file or a directory of TOML files")
    validate.add_argument("targets", nargs="+")
    validate.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
