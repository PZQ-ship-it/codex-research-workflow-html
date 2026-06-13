# Skill Eval Checklist

Use this checklist before trusting a new or modified Codex skill.

## Static Contract

- `SKILL.md` exists and has YAML frontmatter with only `name` and `description` unless a known validator accepts more.
- `name` matches the folder name and uses lowercase letters, digits, and hyphens.
- `description` states both what the skill does and when it should trigger.
- No TODO scaffold text remains.
- `agents/openai.yaml`, when present, has a 25-64 character `short_description`.
- `agents/openai.yaml` `default_prompt` mentions the literal `$skill-name`.
- Scripts are runnable from the documented working directory.
- References are linked from `SKILL.md` and loaded only when needed.
- No secret-looking values, cookies, bearer tokens, or auth headers appear in committed files.

## Trigger Coverage

- Direct invocation: user explicitly names `$skill-name`.
- Implicit invocation: user describes the exact target task without naming the skill.
- Noisy realistic prompt: user includes surrounding project context.
- Negative control: adjacent task that should not invoke the skill.
- Conflict control: prompt mentions two plausible skills and should route predictably.

## Execution Coverage

- The skill runs in a clean scratch workspace.
- The skill works with the least permissions needed.
- Required commands are actually run, not only stated.
- Long-running commands have bounded timeouts or clear stop rules.
- Failures preserve useful intermediate artifacts.
- The final answer cites evidence paths, commands, or screenshots as appropriate.

## Optimization Signals

- False negative trigger: improve the `description` with clearer trigger words.
- False positive trigger: add negative boundaries to the `description`.
- Repeated skipped step: make the step a required workflow gate or script.
- Repeated fragile code: move deterministic logic into `scripts/`.
- Repeated missing context: add a focused `references/` file and mention when to read it.
- External provider friction: route setup through `$external-api-onboarding`.

## Done

- `quick_validate.py` passes.
- `skill_eval_harness.py static-check` passes.
- At least one positive and one negative eval case were run or explicitly deferred.
- Any external API/MCP dependency has a private storage path, setup route, and smoke-test status.
- The final report names residual risk instead of implying total certainty.
