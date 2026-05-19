# Review Dimensions

Use this checklist selectively. Do not mechanically include every item in the report; choose the dimensions that match the paper.

## Contribution and Problem Framing

- Check whether the paper defines a real problem, not just a technology application.
- Identify the mismatch between the title, abstract, contribution list, and actual work.
- Ask whether the problem has a clear failure mode, stakeholder, constraint, and success criterion.
- Check whether novelty is a new formulation, method, system architecture, dataset, evaluation design, deployment insight, or synthesis.
- Look for overclaimed novelty when prior work already covers the same setting.

## Related Work and Positioning

- Verify that the paper compares against the right families of prior work, not only convenient papers.
- Check whether related work is synthesized into a gap, or listed as a catalog.
- Identify missing baselines implied by the problem framing.
- For application papers, check whether domain practice and constraints are cited, not just technical literature.

## Theory, Formalization, and Algorithms

- Check definitions for consistency across sections, notation tables, formulas, pseudocode, and experiments.
- Test formulas at boundary cases, extreme values, equalities, and discontinuities.
- Check monotonicity, units, normalization ranges, and whether signs/directions match the intended interpretation.
- Verify whether named theories are actually implemented. If not, suggest "inspired by", "heuristic", or a lower-claim name.
- Check whether optimization objectives match evaluation metrics.
- Check whether approximations are clearly stated and empirically justified.
- Check whether constraints are hard constraints, soft penalties, or post-hoc filters; mismatches here often cause correctness risks.

## System and Engineering Work

- Evaluate whether the architecture has clear module boundaries, data flow, state management, failure handling, and auditability.
- Distinguish real implementation from prompt-only demonstration or conceptual architecture.
- Check whether high-risk facts come from deterministic sources rather than generated text when accuracy matters.
- Look for security, privacy, logging, fallback behavior, reproducibility, and maintainability concerns.
- For AI-agent systems, check tool boundaries, state transitions, hallucination controls, and whether the model can alter facts it should only explain.

## Data and Experimental Design

- Check dataset source, coverage, cleaning, annotation protocol, leakage risk, and train/test separation.
- Ask whether the evaluation task matches the paper's central claim.
- Check whether baselines represent credible alternatives and whether ablations isolate the claimed mechanism.
- Inspect metrics for alignment with the objective; add process/safety metrics when the process itself matters.
- Look for small mean differences without confidence intervals, significance tests, or per-case analysis.
- Check external validity: simulated users, synthetic data, single dataset, single institution, single language, or narrow time window.
- Check whether negative results and limitations are acknowledged honestly.

## Statistics and Evidence Strength

- Prefer paired tests when comparing systems on the same cases.
- Consider confidence intervals, bootstrap, paired t-test, Wilcoxon signed-rank test, McNemar test, effect size, and power when appropriate.
- Flag averages that hide subgroup failure, heavy tails, or safety-critical outliers.
- Ask whether qualitative examples are cherry-picked or tied to systematic categories.

## Human, HCI, and User-Study Claims

- Separate mechanism validation from real user acceptance.
- Check participant count, recruitment, task realism, protocol, consent, measures, and analysis.
- For simulated users or LLM judges, state what they validate and what they cannot validate.
- Look for interaction burden, leading language, user trust, explanation quality, and accessibility concerns.

## Writing, Structure, and Presentation

- Check whether concepts are introduced before being used.
- Suggest a running example when the paper has many interacting modules.
- Reduce slogan-like terminology; define each term once, then use concrete actions.
- Check whether figures, tables, algorithms, captions, and references are self-contained.
- Check whether the conclusion follows from evidence rather than restating ambition.

## Ethics, Safety, and Compliance

- For high-stakes domains, check harm modes, human oversight, fact verification, bias, privacy, and escalation boundaries.
- For medical, legal, financial, education, hiring, or public-policy work, ask whether the paper distinguishes decision support from autonomous decision-making.
- Check whether data use complies with consent, licensing, and anonymization expectations.

## Defense and Reviewer Readiness

- Turn each central weakness into a likely oral defense or reviewer question.
- Draft answer directions that are honest: acknowledge limitations, narrow claims, cite evidence, and explain planned revisions.
- Prioritize fixes that remove easy objections before adding new features.
