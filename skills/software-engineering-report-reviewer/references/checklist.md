# Software Engineering Report Review Checklist

Use this checklist when a report needs systematic review against software engineering report norms.

## Expected Chapter Roles

| Section | Expected Content | Common Mistake |
|---|---|---|
| Background / Introduction | Problem context, motivation, scope, contribution overview | Starts with implementation details too early |
| Problem Definition / Objectives | Problem statement, RQs, goals, constraints, success criteria | RQs appear only in design or experiment sections |
| Requirements Analysis | Functional requirements, non-functional requirements, actors, use cases, data requirements | Confuses requirements with features already implemented |
| Overall Design / Architecture | System architecture, module decomposition, data flow, interface relationships, design rationale | Describes code files instead of design |
| Detailed Design | Module responsibilities, algorithms, data structures, interface contracts, workflows, pseudocode | Repeats requirements or jumps into code listings |
| Implementation | Technology stack, source organization, key classes/functions, API endpoints, concrete integration, runtime configuration | Uses vague design language without concrete engineering evidence |
| Testing / Evaluation | Test plan, cases, metrics, environment, datasets, baselines, results, analysis | Lists screenshots without explaining verification |
| Discussion | Limitations, threats to validity, engineering tradeoffs, possible improvements | Overclaims without evidence |
| Conclusion | Summarizes problem, solution, results, contribution, future work | Introduces new technical content |

## Structural Checks

- Does every RQ appear before the design/evaluation that answers it?
- Are requirements stated before the design that satisfies them?
- Is the architecture introduced before individual modules?
- Are design decisions separated from implementation details?
- Are tests and experiments tied to requirements or RQs?
- Are figures introduced before or immediately around their use?
- Are chapter titles aligned with their actual content?

## Design Section Checks

Design sections should contain:

- Architecture diagram or textual architecture.
- Module responsibility table.
- Module interaction, workflow, or sequence diagram.
- Data model and key entities.
- Interface contracts or input/output definitions.
- Algorithm/pipeline design and rationale.
- Constraints, assumptions, and tradeoffs.

Design sections should avoid:

- Long code listings.
- Package installation commands.
- File-by-file implementation narration.
- Test result tables unless used only to justify a design choice.

## Implementation Section Checks

Implementation sections should contain:

- Technology stack and version-sensitive dependencies when relevant.
- Source-code organization and module mapping.
- Concrete API, UI, database, or pipeline realization.
- Key engineering mechanisms: scheduling, persistence, state management, error handling, logging, caching, security, deployment.
- Screenshots or runtime examples when they prove the built system works.

Implementation sections should avoid:

- Repeating background motivation.
- Re-stating requirements without showing realization.
- Claiming algorithm novelty without evidence.
- Putting evaluation conclusions before tests are described.

## Traceability Matrix

For substantive reviews, build or request a compact matrix:

| RQ / Requirement | Design Support | Implementation Evidence | Test / Evaluation Evidence | Gap |
|---|---|---|---|---|
| RQ1 or FR-1 | Architecture/module/algorithm | File/API/component | Case/metric/result | Missing or weak link |

## Severity Guide

- High: Section order blocks comprehension, RQs/requirements are misplaced, design and implementation are badly mixed, or claims lack evidence.
- Medium: Missing traceability, weak rationale, unclear diagrams, incomplete module/API descriptions.
- Low: Wording polish, small title mismatch, inconsistent terminology that does not change meaning.

## Minimal Patch Strategy

1. Move misplaced RQs/problem statements first.
2. Rename or split sections whose content role is wrong.
3. Separate design paragraphs from implementation paragraphs.
4. Add a traceability table if RQs, modules, and evaluations are hard to follow.
5. Only then polish language and figure captions.
