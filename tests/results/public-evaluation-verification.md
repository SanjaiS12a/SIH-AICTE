# B1.5 — Public-data evaluation: results, source gates and remaining work

Date: 1 November 2026 (Asia/Calcutta). **Partial milestone: research tooling and the government-workflow probe are implemented; education/narrative evaluation and independent human annotation remain blocked/pending.** No real-world matching accuracy is established.

## Starting state and preservation

Started from verified B1 feature checkpoint `eace867b153fe143fa6a8e17d6457b15eea77c5a`. Local and remote main were `55f3804819b3d453fdaa07c8e4e25cb5442618a3`; B1 was not merged or published. New branch: `codex/case-intelligence-b15`; recovery: `checkpoint/pre-case-intelligence-b15-eace867`.

No changes to React, Django APIs/models, production matching, decisions, snapshots, model assets, calibration, dependency locks or migrations. No authentic records were loaded into either application database. Local research commands do not import Django or use SQL. Existing full regressions create their own test database in the isolated audit stack. No main merge/push was performed.

## Source and usage register

| Source | Verified basis / intended use | Actual collection |
| --- | --- | --- |
| [OIA higher-education summaries](https://www.oiahe.org.uk/resources-and-publications/case-summaries/) | Public [anonymization/publication policy](https://www.oiahe.org.uk/media/nl0nxlte/publication-of-case-summaries-and-public-interest-cases.pdf) found; no clear corpus-reuse grant verified. User explicitly answered to keep collection pending | **0**, pending permission. No case-summary corpus collected or encoded |
| [CFPB public complaints](https://www.consumerfinance.gov/data-research/consumer-complaints/) | Publisher expressly allows public complaint data use/analysis; its [general legal notice](https://www.consumerfinance.gov/privacy/website-privacy-policy/) distinguishes agency-created information from third-party copyright. Intended local narrative robustness only | **0**. Official API returned HTTP 403; bulk ZIP probe also returned 403. Deprecated source probe returned 404 through native Windows HTTP. No access controls bypassed or unverified mirrors substituted |
| [NYC 311, dataset erm2-nwe9](https://data.cityofnewyork.us/d/erm2-nwe9) | Public Open Data [policy](https://a860-gpp.nyc.gov/downloads/5712m8144?locale=en), agency attribution and [NYC.gov terms](https://www.nyc.gov/main/terms-of-use). Informational data; no accuracy warranty assumed | **500** minimal-field records. Provider metadata identified the current dataset as 2020 to Present |
| Authorized institution corpus | Would require genuine institution identity, permitted processing and independent incident matches | **Unavailable**; not supplied or invented |

The first 1,000-row NYC date-filtered query timed out. Its partial workspace/log was retained; the collector was corrected to record timeouts without losing other source statuses. A new bounded 500-row convenience snapshot was collected without a date filter/order. It is not a representative sample, and fresh online queries may change; local response/corpus checksums define this version.

Final source response SHA256: `e0c19f325d41999176dedc01d48f7bd8327c1df3c48a056b582c291a45e432cc`. Combined normalized corpus: `0d61c51304d3c1e6ec1cf7101f95f81459fa775fefad96d4ad8eafba91ae5201`. ETag, Last-Modified, collection time, exact query, usage conditions and normalization checksums are retained in the local manifest; a safe manifest and aggregate summary are in [public-evaluation-summary.json](public-evaluation-summary.json).

## Corpus and privacy

Only request ID, category, descriptor, agency, status and created/closed timestamps were requested from NYC. No address, coordinate, contact or resolution-narrative columns were requested. Model text is a documented category/descriptor representation; it is **not an original citizen narrative**. Agency is a genuine recorded entity, not a fabricated AICTE institution or Bureau. Publication/incident dates remain unknown where not provided; receipt dates are not silently relabeled.

Raw selected data, original source IDs, source references, scored candidates and annotation CSVs remain under ignored `data/research/b15-20261101-200651/corpus-final/`. Its new parent has explicit current-user Windows ACLs without inherited permissions. The isolated API container copy is in a new root-owned mode-0700 temporary directory; read-only model assets are reused. Privileged local administrators/daemon operators are not excluded by this claim.

No raw complaint text, source record IDs, reviewer notes or completed annotations were staged for Git. The committed JSON includes source metadata, checksums and aggregates only. No source examples were cleared for redistribution. Minimal-field collection and regex support are not a certification of anonymity; manual re-identification review remains pending.

## Measured government-workflow/representation probe

Frozen model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Threshold: `0.603080153465271`. CPU/local-files-only, no training or selection. This adapter applies nearest-five cosine plus the frozen threshold within genuinely recorded agency identity. It is a **transfer/workflow diagnostic**, not production same-institution pgvector retrieval.

| Measure | Result / denominator |
| --- | --- |
| Source/eligible records | **500 / 500**; no >256-wordpiece exclusions |
| Exact normalized representation groups | **122** |
| Query records / references | **25 / 421**, disjoint; duplicate representations do not cross sides |
| Encoded records | **446**; 54 duplicate query representations held out, not counted as independent queries |
| Returned suggestions | **28**, across **10/25** queries |
| Queries with no eligible same-agency references | **1/25** |
| Threshold abstentions with eligible references | **14/24 = 58.33%** |
| Overall no-suggestion rate | **15/25 = 60%**, including the no-reference query |
| Usable/adjudicated judgments | **0 / 0**; all 28 suggestions remain unjudged |
| Suggestion label coverage | **0/28 = 0%** |
| Review-worthy Precision@5 | **Unavailable** — no independent usable judgments |
| Same-incident Recall@5 | **Unavailable** — no independently established relevant incident references |
| False-positive rate / category error rates | **Unavailable** — no independent negative population or relationship labels |
| Uncertainty intervals | **Unavailable** — no empirical judgment numerator/denominator; future complete labels support query-cluster bootstrap |
| Unavailable embeddings | **0**; malformed/zero/nonfinite encoder outputs fail rather than fabricate metrics |

Near-duplicate and actual incident-family independence remain unknown. There is no calibration/training split in this frozen unlabelled diagnostic. Exact-text grouping prevents a trivial self/duplicate representation probe but cannot prove incident independence. The original B1 family-separated synthetic benchmark is preserved separately.

### Workflow data quality

Statuses: **477 Closed, 21 In Progress, 2 Open**, totaling 500; all source keys unique. No invalid parsed dates or closed-before-created timestamps were found. **Seven Closed records lack a closed timestamp; one non-Closed record has a closed timestamp.** No reason for these source inconsistencies is inferred.

There are 471 nonnegative recorded creation-to-closed timestamp intervals, averaging **12.193 days**, including the non-Closed record with such a timestamp. This describes published fields and clock values, not verified service resolution time or AICTE deadline compliance. No overdue counts, AICTE deadlines, assignments or Bureau transfers were invented.

### Timing

Final verified run: dependency imports plus first model construction **8.625 seconds** (excludes interpreter startup and preflight checksums); one synthetic non-corpus warm-up **0.0493 seconds**; warm embedding of 446 representations **1.104 seconds**. In-memory exact retrieval total **2.868 ms**, query p95 **0.337 ms**. PostgreSQL latency and end-to-end import/queue time are unavailable in this standalone probe. These are diagnostics under the documented laptop/audit environment, not general performance promises.

## Comparison with B1 synthetic evidence

| Area | B1 synthetic regression | Current authentic-data work |
| --- | --- | --- |
| Data | 362 eligible authored synthetic records | 500 real structured NYC service requests; no OIA/CFPB text acquired |
| Scope | Synthetic canonical institutions | Actual agency identity only; not AICTE institution validation |
| Queries | 60 labeled same-incident queries | 25 unlabelled structured-representation queries |
| Same-incident Recall@5 | 54/60 = 90%, synthetic only | Unavailable |
| Judgment coverage among returned suggestions | 54/162 = 33.33% | 0/28 = 0% |
| Overall suggestion precision | Unavailable, 108 unjudged | Unavailable, 28 unjudged |
| What is established | Frozen-policy reproducibility and synthetic behavior | Public-source handling, private preparation, no invented identities, unlabelled workflow diagnostics |

No numerical accuracy comparison across these domains is valid yet. Adding real but unlabelled records does not close B1's label-coverage limitation. Neither the 85% precision nor 90% real same-incident recall objective is established. B2 activation/training is not justified by these results.

## Annotation and safe error analysis

`annotations-handoff/` contains two independently shuffled, score/rank-free reviewer CSVs and a blank adjudication CSV for the 28 returned pairs. Source IDs and source links support local review. Header-only tracked templates live in `tests/fixtures/annotation/`; [the protocol](../../docs/public-evaluation-protocol.md) defines independence, required evidence, uncertainty and third-reviewer disagreement resolution.

No human labels were invented. Error analysis is currently limited to source data quality, representation duplication, scope coverage and abstention. Repeated public request categories do not prove the same incident. There are no adjudicated false positives, hard negatives or missed incidents to publish. Any later report must distinguish insufficient evidence from unrelated and obtain independently known positives before estimating recall.

## Implementation and verification

| File / check | Scope / actual result |
| --- | --- |
| `tests/research/public_corpus.py` | Bounded collection, source manifests/checksums, minimal fields, redaction provenance, preserved source blockers |
| `tests/research/public_evaluation.py` | Standalone offline probe, explicit transfer scopes, disjoint text groups, token limits, blind files, independent adjudication validation and metric availability |
| `tests/backend/test_public_evaluation.py` | 13 tests: source/usage validation, forbidden invented identities, duplicate source IDs, query/reference separation, missing labels, independent reviewers, denominators, no evaluation HTTP, immutable input, formula escaping and tokenizer exclusions |
| Full backend regression | **177 passed**, final full run 62.445 seconds, exit 0; final standalone research tests also **13 passed** in 0.183 seconds after strengthening malformed-manifest handling |
| Production build | Passed, exit 0; 5,183 modules, 36.09-second Vite build; unchanged application assets |
| Browser suite | Not rerun: no frontend/API/application source changes. B1's 68 passes are historical, not claimed as new results |
| Production model/schema/source | `git diff eace867 -- backend frontend` empty; no model promotion or production migrations |

Private run metadata: `tests/results/logs/public-evaluation-run.json`; ignored logs/exit codes: `tests/results/runs/b15-20261101-200651/`. Earlier timeout, collection snapshots and evaluation runs are preserved. Final measurements come from `evaluation-verified`; annotation handoff adds original source identifiers from the same immutable candidate result without re-encoding or changing scores. Raw collection, normalization manifests, scores and annotation files are all ignored by Git; only explicitly selected safe aggregate evidence is tracked.

[Reproducible collection, evaluation and annotation commands](../../docs/public-evaluation-protocol.md). Authentic data and private annotations stay out of Git. Graphify was refreshed from the feature working tree: **1,221 nodes, 3,380 edges, 89 communities**; diagnostics show zero unverified code nodes, dangling endpoints or exact duplicate edges, with 14 self-loops retained. Directed edges and source/provenance distinctions remain; code extraction uses no LLM, and fallback community names use hubs. The commit label names parent `eace867` before this checkpoint. Source/tests remain authoritative.

The commit containing this report on `codex/case-intelligence-b15` is the recoverable research-tooling checkpoint, also retained as `checkpoint/public-evaluation-tooling-verified`; the final delivery message records its exact hash. This is not a completed education/narrative accuracy milestone. Local/remote main remain at `55f3804`.

## Remaining gates

1. OIA: permission reference; user requested collection remain pending.
2. CFPB: restore official public export/API access or obtain a permitted official export with provenance/checksum. HTTP 403 is a source-access blocker, not evidence that the data was evaluated.
3. Independent review: complete both blind review files and adjudication; aim for 100% usable labels or report remaining uncertainty explicitly.
4. Institution track: obtain authorized records, genuine canonical identity and independently established incident matches before any AICTE accuracy claim.

The feature commit is a recoverable tooling/government-probe checkpoint, not certification of B1.5 narrative or institution matching. No main merge/push is authorized here. Training, lexical activation, incident groups, OCR, MCP/UTCP, physical offline startup and production-scale readiness were not part of this work.
