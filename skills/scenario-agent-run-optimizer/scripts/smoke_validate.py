#!/usr/bin/env python3
from pathlib import Path
import re
import sys


REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/agent-xray-notes.md",
    "references/diagnostic-rubric.md",
    "references/logging-schema.md",
    "scripts/scenario_agent_run_optimizer_hook.ps1",
]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    missing = [item for item in REQUIRED if not (root / item).exists()]
    if missing:
        print("missing=" + ",".join(missing))
        return 1

    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if not re.search(r"^name:\s*scenario-agent-run-optimizer\s*$", skill, re.M):
        print("missing or wrong skill name")
        return 1
    if "description:" not in skill:
        print("missing description")
        return 1
    if "Agent-Xray" not in skill or "Output Shape" not in skill:
        print("missing core workflow references")
        return 1

    hook = (root / "scripts/scenario_agent_run_optimizer_hook.ps1").read_text(encoding="utf-8")
    if "hookSpecificOutput" not in hook or "$scenario-agent-run-optimizer" not in hook:
        print("hook output missing advisory")
        return 1

    print("scenario-agent-run-optimizer smoke validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
