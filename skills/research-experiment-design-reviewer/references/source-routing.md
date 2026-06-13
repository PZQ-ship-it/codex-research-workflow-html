# Source Routing

Use this reference before external search. Search only when local files do not settle a methodological or current-fact question.

## Prefer These Sources

- Venue and paper checklists: NeurIPS, ICML, ICLR, ACL, AAAI, CHI, KDD, SIGIR, SIGMOD, VLDB, USENIX, or the user's target venue.
- Reproducibility guidance: Machine Learning Reproducibility Checklist, Papers with Code code-completeness guidance, journal ML checklists, artifact evaluation rules.
- Official benchmark sources: benchmark website, official repository, dataset card, model card, leaderboard docs, evaluator repository, or paper appendix.
- Primary papers: original method, dataset, benchmark, metric, or statistical procedure papers.
- Official library docs: training framework defaults, metric implementations, random seed behavior, distributed training caveats, tokenizer/model version docs.
- Standards or regulations: IRB/human-subject guidance, privacy rules, data licenses, domain-specific reporting standards.

## Search Triggers

Use `$anysearch` for:

- "Is this baseline current enough?"
- "What does the target venue require for reproducibility or ethics?"
- "What benchmark version or split should be used?"
- "Is this metric standard for this task?"
- "What reporting checklist applies to this domain?"
- "Does this dataset/model license permit the proposed use?"
- "What are accepted statistical practices for this design?"

## Citation Discipline

- Cite sources only when they materially affect a finding.
- Prefer direct links to official pages, papers, repos, PDFs, or docs.
- Mark search-derived advice as external evidence, not local project fact.
- If sources disagree, report the disagreement and recommend a conservative design gate.

## Useful Query Patterns

- `"<benchmark name>" official evaluation protocol`
- `"<dataset name>" license model training`
- `"<venue>" reproducibility checklist`
- `"<task>" baseline "<year>"`
- `"<metric>" official implementation`
- `"<method>" ablation study baseline`
- `machine learning reproducibility checklist data leakage baseline ablation`
