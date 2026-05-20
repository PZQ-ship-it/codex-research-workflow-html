# Survey Reading Workflow

Use this reference for survey, review, tutorial, or position papers whose main value is organizing a field. The output should function as a readable compressed version of the survey, not a reading guide. A reader should understand the field organization, branch content, representative methods, datasets, metrics, limitations, and future directions from the HTML itself.

## Coverage Standard

Before writing, create a coverage ledger for the survey:

- every top-level section;
- every taxonomy branch and major sub-branch;
- every comparison table;
- every dataset/metric section;
- every challenge, limitation, and future-direction section.

For each item, decide `full`, `condensed`, `figure/table only`, or `omitted`. In the HTML, include the ledger or a short "Coverage" note when helpful. Omit only boilerplate, repetitive examples, references, acknowledgements, or details that do not affect comprehension. Page numbers should support provenance, not replace explanation.

## Minimum Detail For Each Taxonomy Branch

For each major branch, include:

- what the branch is trying to solve;
- why it matters in the paper's field;
- the main technical families or paradigms;
- representative methods, systems, or papers named by the survey;
- datasets, metrics, or evaluation conventions if applicable;
- strengths and limitations;
- open problems or future directions;
- connection back to the survey's central thesis.

Avoid one-line branch cards unless the paper itself only gives a one-line mention. For major branches, write enough prose that the reader does not need to open the original PDF to know what the branch contains.

## Taxonomy GPS Standard

For survey/review papers, the `Taxonomy GPS` is an interpretive section, not a figure placeholder. It must help the reader build a structured mental model before entering branch details.

Include:

- the survey's organizing principle: what axis or argument decides the top-level grouping;
- the article flow: how the introduction says the paper will move through the field, and why that order matters;
- hierarchy: which nodes are top-level areas, sub-branches, examples, datasets, metrics, or applications;
- parallel relationships: which branches are alternatives or sibling topics under the same criterion;
- upstream/downstream relationships: which parts are foundations, which are capabilities built on them, which are applications, and which are evaluation or transfer layers;
- cross-cutting relationships: datasets, metrics, simulators, robot forms, constraints, or models that connect multiple branches;
- paper-specific interpretation: why this taxonomy supports the paper's thesis, not just a generic field map.

Use the taxonomy figure as evidence, then explain it in prose and, when useful, a table such as:

| Relationship | Nodes | Meaning For The Reader |
| --- | --- | --- |
| Foundation -> capability | simulators / robots -> perception / interaction | The first group defines the body and environment constraints for the later tasks. |
| Parallel branches | EQA and grasping under interaction | They are sibling interaction tasks, not a prerequisite chain. |
| Cross-cutting layer | datasets / metrics / sim-to-real | These evaluate or transfer capabilities across branches. |

If the figure suggests a relationship that the article text does not explicitly state, label it as an inference. Do not over-interpret decorative layout or arrows.

## Stage 1: System Initialization

Goal: grasp the whole paper and build the classification tree.

Read:

- title and abstract: define the boundary, what the paper discusses, and what it excludes;
- introduction, especially the latter half: extract contributions and article organization;
- taxonomy section: identify the paper's core classification tree;
- taxonomy/overview figure caption and surrounding paragraphs: extract the logic behind the figure, not only its labels.

Output:

- `Scope Boundary`: one paragraph on in-scope and out-of-scope topics;
- `Contributions`: bullet list grounded in the paper's own claims;
- `Taxonomy GPS`: a tree/table that mirrors the paper's taxonomy plus a prose explanation of its logic, including organizing principle, hierarchy, parallel groups, upstream/downstream relations, cross-cutting axes, and connection to the paper's thesis;
- include the taxonomy figure if available, with page and caption.
- `Coverage Ledger`: major sections and branches with coverage depth.

## Stage 2: Modular Scanning

Goal: understand each branch's position, advantages, weaknesses, and evaluation conventions.

Read:

- opening and closing paragraphs of each major taxonomy branch;
- comparison tables;
- datasets and evaluation metrics;
- repeated references that appear across branches.

Output:

- branch deep sections with core idea, representative methods, strengths, weaknesses, datasets, metrics, key papers, and branch-specific open problems;
- comparison table explanations, not just an index: summarize what each table compares and the main takeaways or dimensions;
- `Field Game Rules`: datasets, tasks, metrics, common baselines, and how to interpret them;
- `Foundational Reading List`: repeatedly cited papers or methods with why each is foundational.

## Stage 3: Breakthrough Search

Goal: find promising research directions.

Read:

- challenges;
- future directions;
- limitations;
- open problems repeated across branches.

Output:

- unsolved problems grouped by branch;
- practical entry points for a new project;
- risky or saturated directions;
- needed resources such as data, compute, evaluation, and implementation effort.

## Required Survey HTML Shape

Use section names that make the artifact self-contained:

- `Paper In One Page`: thesis, scope, contributions, and who should read it;
- `Taxonomy GPS`: full taxonomy tree plus explanation of the survey's structural logic, not just how to use it;
- `Branch Deep Dives`: one subsection per major branch with the minimum branch detail above;
- `Comparison Tables Explained`: curated table images or reconstructed tables plus interpretation;
- `Datasets, Metrics, And Benchmarks`: consolidated evaluation conventions;
- `Representative Papers And Systems`: names grouped by branch and why they matter;
- `What The Survey Concludes`: challenges, future directions, and research entry points;
- `Coverage And Manual Checks`: what was omitted or uncertain.

It is acceptable to keep a brief `Reading Map`, but it must not replace `Branch Deep Dives` or other substantive sections.

## Stage 4: Branch Deepening

Use this when the user asks for detailed explanation of selected branches after reading the first HTML.

For each requested branch:

- restate its place in the taxonomy;
- explain the core intuition in plain language;
- list representative models or papers;
- compare strengths and weaknesses;
- connect to datasets, metrics, and evaluation protocol;
- include relevant figures or tables again when useful;
- end with open problems and what to read next.

The first HTML should already be enough for a reader to understand each major branch at survey level. Stage 4 adds depth, examples, and project planning detail; it should not be required to fill missing first-pass content.
