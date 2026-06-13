# Source Routing

Use this reference before selecting a crawler, API, or enrichment source for conference/workshop intelligence.

## Priority Order

1. Official venue or proceedings source.
2. Public OpenReview data when the venue exposes the needed fields.
3. Maintained structured public datasets such as `ai-workshop-tracker`.
4. Open metadata enrichment such as Crossref, OpenAlex, Semantic Scholar, DBLP, or DOI pages.
5. Third-party trackers, lists, and crawlers used only as discovery seeds.

Never let a third-party tracker overrule an official venue page or official proceedings record.

## Workshop Ecosystem

Primary route:

- `Yeping-Hu/ai-workshop-tracker`: workshop editions, deadlines, topic tags, official website links, OpenReview venue discovery, and accepted-paper caches for OpenReview-hosted workshops.
- Official workshop pages under `neurips.cc`, `icml.cc`, `iclr.cc`, `cvpr.thecvf.com`, `thecvf.com`, or conference-hosted sites.
- OpenReview group/invitation pages for workshop submissions and accepted-paper lists when public.

Use `ai-workshop-tracker` first for cross-conference workshop inventories because it already normalizes conference/year/topic/deadline fields. Cross-check official pages before reporting policy, final deadlines, or accepted-paper counts.

Useful source hints:

- `https://github.com/Yeping-Hu/ai-workshop-tracker`
- `https://neurips.cc/virtual/<YEAR>/events/workshop`
- `https://icml.cc/virtual/<YEAR>/events/workshop`
- `https://iclr.cc/virtual/<YEAR>/events/workshop`
- `https://openreview.net/group?id=<VENUE>`

## OpenReview Venues

Use OpenReview for:

- public submissions;
- public decisions;
- public review and rating fields;
- accepted-paper lists exposed through venue groups/invitations;
- workshop venue discovery;
- public discussion and revision metadata.

Use public pages first for small tasks. Use `openreview-py` when you need venue/group queries, pagination, or batch capture. Some older venues use legacy API formats and some current venues hide reviews or decisions until a release date; record visibility blockers instead of trying to bypass access controls.

Typical public group patterns:

- `ICLR.cc/<YEAR>/Conference`
- `NeurIPS.cc/<YEAR>/Conference`
- `ICML.cc/<YEAR>/Conference`
- workshop-specific OpenReview group IDs discovered from official pages or `ai-workshop-tracker`.

## Official Proceedings

Use the following primary lanes for accepted papers:

- NeurIPS: `https://papers.nips.cc/` and official `neurips.cc` pages.
- ICML, AISTATS, COLT, many workshops: PMLR at `https://proceedings.mlr.press/`.
- ACL, EMNLP, NAACL, COLING: ACL Anthology at `https://aclanthology.org/` or the `acl-org/acl-anthology` metadata package.
- CVPR, ICCV, ECCV, WACV: CVF Open Access at `https://openaccess.thecvf.com/`, plus official program pages for oral/spotlight/session metadata.
- AAAI/IJCAI/KDD/WWW/SIGIR: official venue pages first; supplement with DOI, ACM DL, AAAI proceedings, IJCAI proceedings, OpenAlex, Crossref, DBLP, or Semantic Scholar metadata.

## CFP, Policy, Awards, Oral, Spotlight

Use official venue pages as the canonical source for:

- call for papers;
- review and rebuttal policy;
- ethics, responsible AI, data, compute, reproducibility, or reviewer guidance;
- award lists;
- oral/spotlight/poster labels;
- schedule and program changes.

Third-party pages such as Paper Copilot, best-paper GitHub lists, deadline trackers, and lab/news posts are discovery-only until each claim is verified against an official venue page.

## Deadline and CFP Trackers

Use these as secondary sources:

- `ai-workshop-tracker` for workshop deadlines;
- HLR/deadline-style conference trackers;
- `khairulislam/ML-conferences`;
- `PLNech/cfp-please`;
- conference acceptance-rate repos for historical context only.

These trackers are useful for monitoring and source discovery but should not be treated as authoritative when the official conference page is available.

## Optional Crawlers

Use broad crawlers only when the official route is insufficient and the user accepts the limitations:

- OpenReview crawlers for venue-specific batch exports.
- CVF static-page crawlers for CVPR/ICCV/ECCV accepted papers.
- NeurIPS accepted-paper enrichment scripts for arXiv/Semantic Scholar matching.
- Legacy Selenium crawlers only as fallback because browser, driver, proxy, and page-layout dependencies are fragile.

## Source Priority Labels

- `primary`: official venue/proceedings/API page, official OpenReview public visibility, or maintained official metadata repository.
- `secondary`: reputable public enrichment or structured community tracker.
- `archive`: historical data that may no longer update.
- `fallback`: brittle crawler, search snippet, mirrored page, or source used only to discover canonical URLs.
