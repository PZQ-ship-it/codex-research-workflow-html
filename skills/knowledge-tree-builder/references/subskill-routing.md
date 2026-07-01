# Sub-skill Routing

Use this reference when coordinating specialized skills.

Do not copy sub-skill workflows into this skill. Route each phase to the right
skill, then normalize the result into the knowledge-tree artifact contract.

## Routing Table

| Phase | Use | Expected output |
|---|---|---|
| Purpose and scope unclear | `codex-deep-interview` | scope, non-goals, operation profile, acceptance criteria |
| Branch structure or phased expansion needed | `codex-consensus-plan` | branch trunk, maturity target, phase plan, validation plan |
| Need current web or paper sources | `anysearch`, `research-lit`, `semantic-scholar`, `arxiv`, `paper-review-source-intel` | source candidates with public URLs/citations |
| Paper to reusable evidence card | `paper-to-research-card` if available | `cards/research/<id>.md` content |
| Named concept/module normalization | domain taxonomy skill if available | `cards/modules/` or `cards/concepts/` content |
| Research hook to testable matrix | `research-idea-to-experiment-matrix` if available | `cards/experiments/<id>.md` |
| Matrix/protocol readiness review | `research-experiment-design-reviewer` | risks, blockers, review-ready or not |
| Execute edits through verification | `codex-completion-loop` | implemented changes plus evidence |

For corpus-to-tree work with many papers, first align the operation profile and
target maturity gate before naming a full production pipeline. If the user's
purpose is unclear, start with `codex-deep-interview`. If the branch trunk or
phase plan is unclear, use `codex-consensus-plan`. Do not imply every optional
sub-skill must run; separate required next phase from later optional phases.

## Integration Contract

When a sub-skill returns work, normalize it into:

- source IDs used;
- primary branch owner;
- artifact path;
- source-stated facts;
- Codex-inferred links;
- `needs-check` items;
- validation impact;
- next gate.

## Fallback Rule

If a named sub-skill is missing, continue with the closest local method and say
which fallback was used. Do not invent that a sub-skill ran.
