---
name: software-engineering-report-reviewer
description: Review software engineering reports, graduation project reports, course design reports, and LaTeX/PDF/Markdown drafts for software-engineering document norms. Use when checking whether requirements, problem definition, RQs, architecture, module design, detailed design, implementation, testing, experiments, figures, traceability, and evidence are placed in the right sections and meet common software engineering report expectations.
---

# Software Engineering Report Reviewer

## Purpose

Review a software engineering report as a standards-aware document reviewer. Focus on whether the report is organized like a software engineering artifact, not only whether the prose sounds polished.

Use this skill for:

- Graduation thesis/project reports with a software system, prototype, algorithm pipeline, or engineering implementation.
- Course design reports with requirements, design, implementation, testing, and deployment sections.
- Patch planning for comments such as "RQs should move to problem definition" or "design and implementation are mixed".
- Final checks before LaTeX/PDF review when the main risk is structure and evidence, not page layout.

## Review Workflow

1. Identify the report type and expected bar.
   - Undergraduate graduation project: emphasize complete engineering chain, clear contribution, and advisor/reviewer readability.
   - Software engineering course report: emphasize standard lifecycle artifacts and traceability.
   - Research-oriented system paper: preserve research questions and evaluation logic, but still separate design from implementation.

2. Build a document map before judging.
   - List current sections and their apparent role.
   - Mark sections as problem definition, requirements, design, implementation, testing/evaluation, results, discussion, or appendix.
   - If files are split across LaTeX chapters, inspect the local file structure and nearby included files before giving relocation advice.

3. Check lifecycle order.
   - Problem/background before requirements.
   - Requirements/RQs before design.
   - Architecture and design before implementation.
   - Testing/evaluation after implementation or after the evaluated method is defined.
   - Conclusions after results and discussion.

4. Audit content placement.
   - RQs belong in problem definition, research objective, or requirements/evaluation setup, not buried inside system design.
   - Requirements describe what the system must do and quality constraints.
   - Design explains planned structure, decomposition, interfaces, data, algorithms, workflows, and design decisions.
   - Implementation explains the actual code, frameworks, files, modules, APIs, configuration, and runtime behavior.
   - Testing/evaluation explains verification methods, datasets/cases, metrics, results, and analysis.

5. Trace claims across the report.
   - Every RQ should map to a requirement, design/implementation support, and evaluation evidence.
   - Every major module should have a requirement or problem motivation.
   - Every important result should have a method, metric, and source.
   - Flag orphan modules, unsupported claims, stale terminology, and unexplained figures.

6. Produce findings first.
   - Start with the highest-impact structural or evidence problems.
   - Give concrete section/file references when available.
   - Say what to move, merge, split, shorten, or rewrite.
   - Separate required fixes from polish.

## Design vs Implementation Rule

Use this practical boundary:

- Design answers "what structure and decisions make the system possible?"
- Implementation answers "what code and concrete engineering work made the system run?"

Classify as design:

- Architecture, layers, module decomposition, responsibilities.
- Data model, database schema as a planned model, key entities, ER diagrams.
- Interface contracts, inputs/outputs, API design, state transition, sequence diagrams.
- Algorithm or pipeline design, scoring formulas, pseudocode, strategy choices.
- Design rationale and tradeoffs.

Classify as implementation:

- Source-code organization, concrete classes/functions/files.
- Actual frameworks, libraries, endpoints, components, SQL/ORM code, migrations.
- Runtime configuration, deployment commands, dependency versions.
- Error handling, logging, caching, threading, job scheduling as actually coded.
- Screenshots or concrete behavior of the built system.

When a paragraph mixes both, recommend splitting it into "design decision" and "implementation realization".

## Output Format

Prefer this structure unless the user asks for direct edits:

1. Review scope and assumption.
2. High-priority findings.
3. Section relocation plan.
4. Design/implementation boundary fixes.
5. Traceability gaps.
6. Suggested minimal patch order.

Keep feedback actionable. For each finding, include:

- Problem.
- Why it matters for software engineering report norms.
- Concrete fix.
- Target section or file if known.

## References

Read `references/checklist.md` when the task needs a detailed checklist, scoring rubric, or a table of expected section contents.
