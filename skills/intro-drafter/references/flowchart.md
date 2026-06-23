# The six-paragraph Introduction flowchart

## Table of contents

1. Chain of reasoning
2. Paragraph 1: Background and Motivation
3. Paragraph 2: Limitations of existing work
4. Paragraph 3: Problem essence and Our Goal
5. Paragraph 4: Key challenges
6. Paragraph 5: Solution overview
7. Paragraph 6: Contributions
8. Pitfalls at each stage

## 1. Chain of reasoning

```
Background + Running Example
   -> Limitations (at most 3)
      -> Problem Essence + Our Goal
         -> Key Challenges (at most 3)
            -> Solution Overview (one module per challenge)
               -> Contributions (3 to 4, each mapped to a section)
```

Every arrow must hold. If any arrow breaks, the Introduction reads as
a list of disjointed claims rather than a single argument. Reviewers
notice this and score down.

## 2. Paragraph 1: Background and Motivation

### Purpose

Introduce the research object, motivate why the problem matters in
the real world, and ground the rest of the paper in a concrete
running example.

### Sentence roles

- S1: Open with the task or research object, not the technique.
- S2: Name the real-world setting where the problem matters.
- S3: Introduce a specific running example, ideally tied to Figure 1.
- S4: Point to three to five recent applications, deployments, or
  empirical signals as importance evidence.
- S5: Bridge from the example to why current approaches must be
  examined.
- Avoid final prose; describe what each sentence must do and which
  input it should use.

### Common failures

- Opening with a technique ("we introduce X for Y").
- Generic motivation ("deep learning is important").
- No running example; the paper never becomes tangible.

## 3. Paragraph 2: Limitations of existing work

### Purpose

Identify what prior work does not address, in at most three
limitations.

### Sentence roles

- S1: Transition from the motivated task to the relevant prior-work
  families.
- S2-S4: Assign one sentence slot per limitation. Each slot must name
  the prior work family or capability and the missing property.
- S5: Bridge the limitations to the problem essence or hard
  constraints if the connection would otherwise be implicit.
- Two limitations is acceptable; do not pad to three artificially.

### Common failures

- Vague limitations ("existing work is insufficient").
- Too many limitations; after three, the paper loses focus.
- Limitations that have nothing to do with the challenges in
  Paragraph 4; the reader cannot see why they were raised.

## 4. Paragraph 3: Problem essence and Our Goal

### Purpose

Characterise the problem's intrinsic properties and hard constraints,
then state the research goal or key idea.

### Sentence roles

- S1: Characterise the intrinsic problem property or setting boundary.
- S2: Name the hard constraints: scale, dynamicity, heterogeneity,
  end-to-end latency, correctness, consistency, or similar.
- S3: Allocate the goal or research-question slot. For a Technique
  Paper this is a short bridge; for a New Problem / Setting Paper it
  carries the main contribution.
- S4: Connect the goal to the key idea or to why the setting is worth
  formalising.
- Technique papers normally need 2 to 4 sentence slots here; New
  Problem / Setting papers normally need 4 to 7.

### Common failures

- Skipping hard constraints; Paragraph 4 challenges then have no
  grounding.
- Stating the goal as a list of sub-goals; reviewers lose focus.
- For New Problem papers, underweighting this paragraph as if it
  were a Technique Paper.

## 5. Paragraph 4: Key challenges

### Purpose

Enumerate the two or three obstacles that prevent a naive extension
of prior work from solving the problem.

### Sentence roles

- S1: Set up why the goal is non-trivial.
- S2-S4: Assign one sentence slot per challenge. Each slot must name
  the obstacle and explain why a naive extension of prior work fails.
- S5: If useful, synthesise the design requirements implied by the
  challenges.
- Challenges address the limitations from Paragraph 2 or the hard
  constraints from Paragraph 3.
- Common challenge categories:
  - Search-space explosion.
  - Efficiency or latency ceilings.
  - End-to-end closed-loop difficulty.
  - Theoretical or engineering conflict.
- At most three challenges. Four or more signals scope issues.

### Common failures

- Vague challenge statements ("it is hard").
- Challenges that do not map to modules in Paragraph 5.
- Pre-announcing solutions inside challenge statements.

## 6. Paragraph 5: Solution overview

### Purpose

Present the paper's methodology at a high level, with a one-to-one
mapping between the challenges in Paragraph 4 and the modules or
components introduced here.

### Sentence roles

- S1: Name the solution framework and its high-level principle.
- S2-S4: Assign one sentence slot per challenge-to-module mapping.
  Each slot names the module, the challenge it addresses, and the
  methodology section pointer.
- S5: Reuse the running example or forecast a case study so the
  Introduction loop closes.
- If a module addresses two challenges, make that mapping explicit.

### Common failures

- Over-detail that belongs in Section 3 (Methodology).
- No explicit mapping; reviewers must infer which module handles
  which challenge.
- Module count mismatches challenge count without explanation.

## 7. Paragraph 6: Contributions

### Purpose

Summarise the paper's contributions in three or four numbered bullets,
each mapped to a section or set of sections.

### Sentence roles

- Canonical structure:
  - C1: Problem definition or problem-setting contribution (if the
    paper is a New Problem / Setting Paper).
  - C2: System or framework design, or a specific methodological
    innovation.
  - C3: One or two key technical contributions (specific algorithms,
    theoretical results, or data structures).
  - C4: Comprehensive experimental evaluation with specific
    highlights (not vague claims).
- Each contribution cites a section: "(Section 3.2)" or "(Sections
  4-5)".
- No single contribution is a vague phrase like "extensive
  experiments".
- Output each contribution as a bullet-level plan: what the final
  bullet must name, what evidence or result it must include, and which
  section should deliver it.

### Common failures

- Vague phrases as contributions.
- Contributions that the paper does not actually deliver.
- More than four contributions; focus erodes.

## 8. Pitfalls at each stage

- **Stage 1 pitfall**: running example is an abstraction (graph, LLM,
  system); not tangible enough.
- **Stage 2 pitfall**: limitations list is longer than three or
  padded.
- **Stage 3 pitfall**: goal is unclear; reader cannot say in one
  sentence what the paper tries to do.
- **Stage 4 pitfall**: more challenges than modules, or challenges
  invented to justify modules rather than derived from the problem.
- **Stage 5 pitfall**: module names do not appear in Paragraph 6's
  contributions, so the reader loses track.
- **Stage 6 pitfall**: contributions include items the paper does not
  deliver; in major revisions, reviewers quote these.
