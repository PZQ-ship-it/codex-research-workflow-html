# Reviewer Routing

## Entry triage

Run this triage before the reference selector or either reviewer lane:

- **No reviewer**: routine completion, simple analysis, narrow low-risk edits,
  dependency/config/skill updates, ordinary commit/push, or work covered by
  deterministic checks. Return to normal verification.
- **Structural only**: use one read-only structural reviewer when an
  independent hard-contract, safety, schema, migration, or reproducibility
  check is justified. Do not invoke this dual-review skill.
- **Dual review**: continue only for an explicit formal review/acceptance
  request or a documented high-risk decision where holistic quality matters
  and deterministic checks are insufficient.

Record the qualifying reason, artifact, decision, and rubric before dual
review. Mere completion wording is never a qualifying reason.

## Reference selector

Run before reviewers only when `reference-mode` returns `retrieve_required`.
The selector may use approved public search tools. Give it the frozen task
fingerprint and candidate hash, not candidate content. It writes the complete
candidate ledger, frozen snapshots, provenance, comparability decisions, and
reference set. It does not judge the candidate. After selection, run the
example audit, admit only task-traceable soft-quality rubric changes, refreeze
the rubric, then rescore every selected reference.

If retrieval fails or finds no eligible reference, record that state and
continue to both reviewer lanes.

## Structural lane

Own hard requirements: facts, safety, required artifacts, schema validity,
source access, reference provenance, hash consistency, reproducibility, and
explicit user constraints. Return findings and fixes, not a holistic score.

## Quality lane

Own task-specific soft dimensions: intent fit, judgment and tradeoffs,
coherence, evidence synthesis, usability, and finishedness. Use anchors to
interpret the scale and compare only with the challenge frontier. Never score
hard structural checks. Return a noticed hard issue as `structural_concerns`.
In reference-free diagnostic mode, still score and produce revision actions.
Never browse or alter reference selection.

Do not reveal either lane's verdict to the other until both outputs are frozen.

## Routing

```text
human reference + structural pass + quality pass + calibration pass
  -> accepted

retrieved verified frontier + all-frontier comparison pass
  -> provisional_outperforms_retrieved

retrieved verified frontier + stable comparison shortfall
  -> provisional_shortfall

absolute quality floor shortfall
  -> provisional_shortfall

monotonic anchors + no eligible challenge frontier
  -> anchored_diagnostic

missing/ineligible reference OR order/confidence/evidence conflict
  -> needs_human

structural failure OR failed formal human gate
  -> blocked
```

Use distinct prompts and evidence records. Same-model lanes are only
`prompt_only` independent. The parent agent owns search routing, hashes,
deterministic gate execution, iteration limits, and final reporting. Reviewers
remain read-only.
