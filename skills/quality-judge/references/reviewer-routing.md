# Reviewer Routing

## Structural lane

Own hard requirements: factual support, safety constraints, required files,
schema validity, reproducibility evidence, and explicit user constraints. It
returns findings and fixes, not a holistic quality score.

## Quality lane

Own task-specific soft dimensions: intent fit, decision usefulness, coherence,
evidence quality, usability, and finishedness. It must not duplicate every
structural check or override structural failures.

## AND gate and escalation

```text
structural_pass AND quality_pass AND calibration_pass -> accepted
structural_fail OR quality_fail -> blocked
reviewer disagreement OR low confidence OR high-stakes task -> needs_human
```

Use distinct prompts and separate evidence records. Different models improve
independence but are not mandatory; if both lanes use the same model, record
`independence: prompt_only` and use a stricter confidence policy.

The parent agent owns routing, artifact hashes, deterministic gate execution,
iteration limits, and final reporting. Reviewer lanes remain read-only.
