---
name: quality-judge
description: "Run calibrated, human-anchored quality gates for complex task artifacts. Use when Codex must judge overall quality beyond checklist completeness, compare an artifact with a human reference, require independent structural and quality reviewers to both pass, iterate after revisions, or audit LLM-as-a-judge bias and score drift."
---

# Quality Judge

Use this skill as the single entry point for a quality-gated review. Keep hard
contract checks and holistic quality scoring in separate read-only reviewer
lanes, then let a deterministic gate decide acceptance.

## Non-Negotiable Contract

- Require a human-graded reference before a score can block acceptance. A
  model-generated reference is directional evidence only.
- Keep two independent lanes: a structural reviewer checks facts, safety,
  required artifacts, and explicit constraints; a quality judge scores the
  task-specific soft dimensions.
- Use an AND gate: acceptance requires both lanes to pass. A high quality score
  cannot override a structural failure.
- Keep the gate decision deterministic. The model may propose scores and
  evidence; `scripts/quality_gate.py` computes the final status.
- Keep judges read-only. Do not let a judge edit the artifact, call external
  APIs, browse, or see secrets, credentials, or hidden generator identity.
- Do not expose hidden chain-of-thought. Require compact evidence, a failure
  explanation, a confidence value, and a concrete next action.

## Modes

Choose one mode before acting:

1. **setup**: create a run directory from the templates, define 3-6
   task-specific dimensions, record human reference scores, and set the gate
   policy.
2. **evaluate**: collect an evidence bundle, run the structural and quality
   reviewer lanes independently, then run the deterministic gate.
3. **re-evaluate**: reuse content-hash-identical evidence and re-run only
   changed artifacts, rubric versions, references, or judge versions.
4. **audit**: test position swaps, verbosity injections, style rewrites,
   self-preference, repeated-trial variance, and reference drift.

## Workflow

### 1. Scope the quality target

Identify the user goal, artifact, task contract, non-goals, and the 3-6 quality
dimensions that matter for this task. Do not use a universal quality rubric.
Define critical dimensions and a minimum floor for each. Read
`references/gate-contract.md` for the input/output shape.

### 2. Prepare the human anchor

Use a real human-scored reference artifact or reference set. Store the rubric
version, grader count, score scale, rationale, and date. One reference is
allowed for a provisional smoke test; use at least 3-5 clear cases and two
independent graders before trusting a blocking gate. Read
`references/calibration-and-bias.md`.

### 3. Run independent reviewer lanes

Give both lanes the same task contract and artifact evidence, but separate
their prompts and outputs:

- **Structural reviewer**: return `pass`, `critical_failures`, evidence
  locations, and executable fixes. It must check hard requirements first.
- **Quality judge**: score each task-specific dimension, compare against the
  human anchor, and return evidence, counterexample, confidence, calibration
  status, and revision actions. Score only after writing compact evidence.

If native subagents are available, use separate read-only reviewer threads.
Record model, prompt hash, rubric hash, and evidence hash for each lane. If the
same model is used twice, label independence as prompt-level only and lower
confidence for high-stakes decisions.

### 4. Run the deterministic gate

Use the bundled script; do not make the parent agent infer acceptance from
prose:

```powershell
python <skill-dir>\scripts\quality_gate.py init --out <run-dir>
python <skill-dir>\scripts\quality_gate.py validate --run-dir <run-dir>
python <skill-dir>\scripts\quality_gate.py gate --run-dir <run-dir> --out <run-dir>\gate-result.json
```

The default policy requires a human anchor, calibrated judge, confidence above
the configured floor, critical dimensions above their floor, and candidate
quality at least `reference + margin`. Change the comparison mode only in the
versioned policy file.

### 5. Route the result

- `accepted`: both reviewers pass and every configured gate passes.
- `blocked`: a hard failure, score shortfall, calibration drift, or low
  confidence requires revision.
- `needs_human`: the evidence is ambiguous, reviewers disagree, or the task is
  high stakes. Do not silently convert this to pass or fail.

After a blocked result, revise the artifact, preserve the previous result, and
re-run the same rubric. Stop when the score improvement plateaus, a critical
dimension remains below floor, or the configured iteration budget is reached.

## Output Contract

Every run must leave:

- `gate-config.json`: versioned policy and thresholds;
- `human-reference.json`: human anchor metadata and dimension scores;
- `structural-result.json`: structural reviewer result;
- `quality-result.json`: quality judge result;
- `gate-result.json`: deterministic status, reasons, score comparison, and
  hashes;
- optional `audit-results.json`: bias and repeated-trial checks.

Do not claim success from a missing file, a self-reported pass, or a score
without a human reference. Keep raw private artifacts outside the skill bundle
and redact secrets before building an evidence bundle.

## References

- `references/gate-contract.md`: JSON contracts, comparison modes, and status
  semantics.
- `references/judge-prompt.md`: compact evidence-first quality judge prompt.
- `references/calibration-and-bias.md`: human anchoring, leniency, agreement,
  permutation, verbosity, and self-preference checks.
- `references/reviewer-routing.md`: independent lane routing and AND-gate
  escalation rules.
- `assets/templates/`: starter JSON files for a new run.
