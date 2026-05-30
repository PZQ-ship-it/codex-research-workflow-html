# Agent Collaboration Standard v0.1

Applies to reusable agent specs used by workflow skills.

## 1. Leader And Lane Model

- The workflow skill is the leader.
- Each agent is a lane with one bounded responsibility.
- The leader owns integration, conflict resolution, final validation, and user-facing conclusions.
- An agent result is evidence for the leader, not automatic completion of the whole workflow.

## 2. Lane Types

Use one of these lane types in every agent spec:

| Lane Type | Meaning | Typical write scope |
|---|---|---|
| `explorer` | Reads sources and returns analysis or recommendations | usually none, or one analysis file |
| `worker` | Produces or transforms concrete artifacts | explicit output files only |
| `reviewer` | Checks consistency, risks, quality, or regressions | review report only |
| `hybrid` | Reads, decides, and writes a bounded handoff artifact | explicit handoff files only |

## 3. Ownership Boundaries

Every agent spec must state:

- Allowed read scope.
- Allowed write scope.
- Files it must not edit.
- Whether it may update upstream artifacts.
- Whether it may ask the user, and under what conditions.

Multiple agents must not write the same file unless the leader explicitly serializes them.

## 4. Handoff Contract

Every agent output should include:

- Inputs consumed.
- Files produced.
- Decisions made.
- Evidence or source basis.
- Assumptions and defaults.
- Open questions.
- Downstream risks.
- Recommended next phase.

## 5. Parallelism Rules

Safe to run in parallel only when:

- The lanes have disjoint write scopes.
- Each lane has all required upstream inputs.
- The leader can continue useful local work while lanes run.

Sequential by default:

- Intent alignment before fact extraction.
- Fact extraction before storyboard.
- Storyboard before final asset audit.
- Asset audit before PPTX automation.
- PPTX draft before Figma polish.

Potentially parallel after inputs are stable:

- Template feasibility analysis and early fact extraction.
- Preliminary asset inventory and storyboard refinement.
- Figma candidate-page selection and PPTX render validation.
- QA generation and speaker-script drafting after storyboard freeze.

## 6. Integration Rules

The leader must:

- Inspect agent outputs before handing them downstream.
- Resolve contradictions against source files and the production brief.
- Run the smallest meaningful verification for generated artifacts.
- Record residual risks instead of hiding uncertainty.

## 7. Final Reporting

When reporting completion, include:

- What the leader integrated.
- What each agent produced.
- Which files changed.
- What was verified.
- What remains uncertain or manual.

