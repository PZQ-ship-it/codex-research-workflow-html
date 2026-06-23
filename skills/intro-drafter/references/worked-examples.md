# Worked Introduction outlines

## Table of contents

1. How to read these examples
2. Example A: Alpha-SQL (ICML 2025), Technique
3. Example B: AFlow (ICLR 2025), Technique with cross-domain framing
4. Example C: LEAD (VLDB 2026), New Problem/Setting
5. What the examples teach

## 1. How to read these examples

Each example below reverse-engineers a published Introduction into
the six-paragraph, sentence-level outline this skill produces. The
plans are faithful to the published papers, but they intentionally
avoid reusable final prose. Sources are
`handbook/06_Case_Studies/6.1`, `6.2`, and
`6.3`.

The purpose is to show the level of sentence-planning detail this
skill should produce when given similar inputs.

## 2. Example A: Alpha-SQL (ICML 2025), Technique

### Type positioning

Technique Paper. Text-to-SQL is a long-established problem with
active benchmarks (Spider, BIRD). The contribution is a method:
MCTS-based inference-time search.

Paragraph 3 is a one-sentence bridge.

### Outline

1. **Background and Motivation**.
   - S1: Establish production Text-to-SQL as the task.
   - S2: Introduce a retail-database multi-table aggregation as the
     running example.
   - S3: Use the example to surface complex JOIN reasoning.
   - S4: Motivate why open-source LLM-based SQL generation matters.
2. **Limitations of existing work**:
   - S1: Transition from task importance to current open-source
     methods.
   - S2: L1 slot: single-pass generation fails on complex JOIN
     reasoning.
   - S3: L2 slot: fine-tuning is expensive and does not generalise
     across schemas.
   - S4: Do not invent L3; bridge to why inference-time search is
     needed.
3. **Problem essence and Goal**.
   - S1: State the hard constraint: deployable on open-source LLMs
     without fine-tuning.
   - S2: Allocate a brief goal slot for improving complex-query SQL
     generation under that constraint.
4. **Key challenges**:
   - S1: Set up why inference-time search is non-trivial.
   - S2: Ch1 slot: decision-space explosion when enumerating SQL
     candidates.
   - S3: Ch2 slot: reward modelling without a trained critic.
5. **Solution overview**.
   - S1: Name Alpha-SQL and its MCTS-guided inference principle.
   - S2: Map structured search to Ch1.
   - S3: Map execution-feedback reward signals to Ch2.
   - S4: Reconnect the method to the retail-query running example.
6. **Contributions**:
   1. C1 plan: Name MCTS-based inference search for Text-to-SQL and
      cite Section 3.
   2. C2 plan: Name self-supervised reward design from execution
      feedback and cite Section 4.
   3. C3 plan: Name BIRD and Spider, include the main accuracy-gain
      evidence over open-source baselines, and cite Section 5.

## 3. Example B: AFlow (ICLR 2025), Technique with cross-domain framing

### Type positioning

Technique Paper, framed to emphasise Broader-dimension cross-domain
transplantation (operator search for agent workflows, borrowed from
neural architecture search).

Paragraph 3 bridges briefly; the Key Idea weight is in Paragraph 4
and 5.

### Outline

1. **Background and Motivation**.
   - S1: Establish LLM agents for code generation as the task.
   - S2: Introduce a HumanEval workflow as the running example.
   - S3: Use operator mis-composition in the example to make the
     failure concrete.
2. **Limitations of existing work**:
   - S1: Transition to current workflow-design approaches.
   - S2: L1 slot: prompt-engineering alone yields brittle workflows.
   - S3: L2 slot: single-agent architectures miss operator
     composition.
   - S4: L3 slot: hand-designed workflows fail to generalise across
     task families.
3. **Problem essence and Goal**.
   - S1: State the hard constraint: workflow design should generalise
     to unseen operators.
   - S2: Allocate a brief goal slot for automated workflow design in
     code-generation agents.
4. **Key challenges**:
   - S1: Explain why workflow automation is a search problem.
   - S2: Ch1 slot: combinatorial operator-graph search space.
   - S3: Ch2 slot: discrete and sparse workflow evaluation signal.
5. **Solution overview**.
   - S1: Name AFlow and the operator-graph-search principle.
   - S2: Map graph search, borrowed from NAS, to Ch1.
   - S3: Map code-execution reward to Ch2.
   - S4: Reconnect to the HumanEval running example.
6. **Contributions**:
   1. C1 plan: State the operator-graph-search formulation and cite
      Section 2.
   2. C2 plan: Name the AFlow algorithm and execution-feedback search,
      citing Section 3.
   3. C3 plan: Name HumanEval, MBPP, adjacent benchmarks, comparison
      families, and consistent-gain evidence, citing Section 4.

## 4. Example C: LEAD (VLDB 2026), New Problem/Setting

### Type positioning

New Problem/Setting Paper. Paragraph 3 is load-bearing: the
contribution is the new setting "iterative data selection without
additional inference".

### Outline

1. **Background and Motivation**.
   - S1: Establish LLM instruction tuning and data quality as the
     task context.
   - S2: Introduce a 50k-sample instruction corpus as the running
     example.
   - S3: Use iterative selection in the example to show the
     quality-cost tension.
2. **Limitations of existing work**:
   - S1: Transition to data-selection methods.
   - S2: L1 slot: non-iterative selection does not adapt to model
     evolution.
   - S3: L2 slot: iterative methods require full-dataset inference in
     every round.
3. **Problem essence and Goal**.
   - S1: State the hard constraint: no additional inference budget
     beyond the fine-tuning loop.
   - S2: Allocate a load-bearing research-question slot about
     preserving iterative-selection benefits without repeated
     inference.
   - S3: Add the key-idea slot: use training loss already computed in
     fine-tuning as a zero-overhead utility signal.
4. **Key challenges**:
   - S1: Explain why reusing training loss is not automatically
     reliable.
   - S2: Ch1 slot: extracting utility from noisy loss trajectories.
   - S3: Ch2 slot: integrating selection without disturbing
     convergence.
5. **Solution overview**.
   - S1: Name LEAD and its inline selection principle.
   - S2: Map Instance-level Dynamic Uncertainty to Ch1.
   - S3: Map deferred selection to Ch2.
   - S4: Reconnect to the 50k-sample running example and cost
     constraint.
6. **Contributions**:
   1. C1 plan: Name the new setting, iterative data selection without
      additional inference, and cite Section 2.
   2. C2 plan: Name Instance-level Dynamic Uncertainty, theoretical
      analysis, and cite Sections 3 and 4.
   3. C3 plan: Name LEAD framework design and cite Section 3.
   4. C4 plan: Name instruction-tuning benchmarks, matched-or-better
      quality, order-of-magnitude cost reduction, and cite Section 5.

## 5. What the examples teach

- Alpha-SQL shows a tight Technique Paper: three contributions, two
  limitations, two challenges. Focus wins.
- AFlow shows a Technique Paper with cross-domain framing: three
  contributions, three limitations, two challenges. The Broader-
  dimension framing earns the ICLR slot without changing type.
- LEAD shows a New Problem Paper: Paragraph 3 is load-bearing; the
  contributions include the problem setting itself as C1; the
  framework and method are C2-C4.
- All three have a one-to-one mapping between challenges and
  modules; none has more than three challenges. None has vague
  phrases as contributions.
- None reuses prior work in C1 without crediting prior limitations
  in Paragraph 2.
