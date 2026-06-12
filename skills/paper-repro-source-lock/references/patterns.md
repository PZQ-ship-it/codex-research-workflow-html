# Paper Reproduction Source Locking Patterns

Use this reference when multiple papers, repos, forks, datasets, models, or benchmark sources could plausibly be used.

## Source Priority

1. Official venue/proceedings, OpenReview, arXiv, DOI, publisher, or author project page.
2. Repository linked directly by paper, authors, venue, or official project page.
3. Stable repository reference: commit SHA, tag, release, archive hash, Zenodo DOI.
4. Official model/data/benchmark host with version or revision: Hugging Face revision, Kaggle version, OpenML ID/task, Zenodo DOI, dataset card, model card, container digest.
5. Maintained third-party implementation or aggregator, marked `secondary`.
6. Search result snippets, blog posts, mirrors, or forks, marked `discovery` or `fallback` only.

## Lock Fields

- `kind`: paper, code, dataset, model, checkpoint, benchmark, evaluator, container, config, docs.
- `priority`: primary, secondary, archive, fallback.
- `url`: canonical URL.
- `locked_ref`: version, commit, tag, release, DOI, dataset version, HF revision, Docker digest, checksum.
- `license`: exact license or "unknown".
- `access`: public, gated, private, paid, unavailable.
- `auth_required`: boolean plus provider name.
- `used_by_experiments`: claim-map experiment ids.
- `fetched_at`: ISO date/time.
- `notes`: mismatch, uncertainty, or usage constraints.

## Provenance Checks

- Prefer stable identifiers over floating `main` branches.
- If only a branch exists, record the observed commit SHA.
- For Hugging Face, record model/dataset id and revision when possible.
- For Kaggle/OpenML, record dataset/task id and version.
- For Zenodo or archival releases, record DOI and version.
- For Docker, record image tag and digest when available.
- For datasets and models, record license and terms because a technically downloadable asset may still be unsuitable for reproduction or redistribution.

## Auth and Secret Handling

- Record the need for GitHub/HF/Kaggle/OpenML/OpenReview auth without storing tokens.
- Use visible assisted setup through `$external-api-onboarding` when auth is required.
- Do not place `.env`, cookies, signed URLs, access tokens, or private dataset paths in manifests.

## Source Notes

- ACM Artifact Review and Badging policy: https://www.acm.org/publications/policies/artifact-review-and-badging-current
- Papers with Code releasing research code: https://github.com/paperswithcode/releasing-research-code
- Data provenance audit framing: https://www.cs.cmu.edu/~sherryw/assets/pubs/2023-data-provenance.pdf
- ReproAgent artifact-chain pattern: https://github.com/hqygtr-prog/repro-agent
- paper-replay search result pattern: https://github.com/bettyguo/paper-replay
