# AICTE SIH 26264 — Case Intelligence 2.0 implementation plan

Prepared: 1 November 2026. Status: proposed implementation backlog; no application changes made in this planning pass.

## 1. Outcome and verified starting point

An official should be able to search an institution, inspect its authorized case history, compare potentially related cases, understand the evidence, and record an accountable coordination decision. Complaints remain independent records. Semantic similarity assists review; it never establishes a duplicate incident by itself.

The attached proposal is design input. This plan reconciles it with the actual source rather than treating its descriptions of missing features as established facts.

Local `main` is clean at `da32e1ad2eefc98da3250d4ce79a88a29e9c313f`, already published to GitHub in the preceding task. The corrective baseline was `996b2ff`; it is not the current development baseline. Start implementation from a newly verified current HEAD, preserve recovery artifacts, and create `codex/case-intelligence` before editing application code.

Existing saved verification records show 148 backend tests, 53 browser tests, three Windows operational checks and a successful production build. Those checks were not rerun for this plan. Physical disconnected startup remains unverified. The recorded 1,000-row result was 52.50 seconds under its documented conditions; it is not a guarantee for the proposed changes. The 10,000-row diagnostic included a reminder timeout and other interference and is not a clean throughput benchmark.

Keep React, Django/DRF, PostgreSQL/pgvector, Q2, session authentication, private attachments and the government orange/white/green theme. Keep the active MiniLM revision and calibrated threshold unchanged. No retraining, automatic merging, external assistant upload or replacement backend is part of the initial delivery.

## 2. Requirement-to-code audit

| Requirement | Existing implementation | Action |
| --- | --- | --- |
| Canonical institutions and complete profiles | `models.py`, `institutions.py`, `institutions.tsx`; immutable Permanent ID, scoped profiles, paginated cases/history | Reuse; improve contextual navigation only |
| Case workflows and accountability | `api.py`, coordination/escalation modules; optimistic versions and append-only CaseAction | Reuse; preserve current mutations and historical Bureau snapshots |
| Side-by-side relationship review | `PairReview` in `main.tsx` already shows two complaints and human review controls | Modify layout and evidence presentation; do not rebuild |
| Manual relationships | `relationships.py`, `relationships.tsx`; ordered unique pairs, audited decisions for both cases | Reuse |
| Source deduplication and conflicts | `imports.py`, source intake endpoints and UI | Reuse source identity/fingerprint rules |
| Matching | `matching.py`; same-institution exact vector search, top five above threshold, pending suggestions refreshed | Add evaluated evidence and retrieval policy separately |
| Structured case briefs/facts | Current complaint fields exist; no reviewed extraction model | Implement incrementally, source-grounded |
| Reviewed incident groups | Pair relationships and operational coordination records exist; no incident group entity | Implement later; keep these concepts distinct |
| MCP | No installed adapter or identity integration found | Separate, opt-in read-only milestone |
| UTCP | No independent Bureau service contracts or integration found | Defer until an actual integration requires it |

The source/document graph was consulted for relationships; source files remain authoritative. In particular, attachment checksums, applicant identities and transaction identifiers are not currently structured comparison fields. The UI must show them as unavailable rather than fabricate evidence.

## 3. Milestone A — simpler official workspace

This is the first release: navigation and review usability, with no schema migration and no matching-policy change.

### Navigation

Use five primary destinations; preserve every existing route and bookmark.

| Destination | Route and content | Role behavior |
| --- | --- | --- |
| Home | `/`; retain operational homepage, filters and exact drill-downs | Existing officer home preserved; management scope labels retained |
| Institutions | `/institutions`; registry and existing profile tabs | All authorized users; coordinator edits only |
| My Work | New `/work` hub linking cases, deadlines, reviews, coordination instructions and escalations | Officers see current Bureau work and their instructions; management sees permitted coordination work; auditors read-only |
| Data Imports | `/imports`; ordinary imports, source intake and older conflict history as secondary navigation | Existing server permissions retained |
| Reports | `/reports`; analytics, exports, movements and cross-Bureau activity as secondary navigation | Existing authorized scopes retained |

Do not label Bureau-wide results "My assigned cases": the shared case filter does not currently implement current-user assignment filtering. Initially use "Cases in my Bureau". Add an assignment filter only as an explicitly tested endpoint enhancement if personal queues are required.

Keep registration, manual relationships, source-upload history, coordination workspace, escalation and movement pages reachable through visible contextual links. Update breadcrumbs and active navigation for nested routes. Never hide a feature without providing its replacement route. Institution profiles retain all-time authorized statistics regardless of management receipt-date filters.

### Review screen

Improve the existing `PairReview` rather than create a second decision workflow. Align institution, source system/reference, category, incident date, receipt date, Bureau and status in two readable columns. Keep original summaries and descriptions; wrap long text. Show missing dates as "Not recorded". Retain existing case links for assignment, next actions, history and attachments; do not invent attachment contents or extract text in this milestone.

Separate four things visually: model cosine similarity, recorded metadata, factual differences, and the officer's decision. A different year is a review cue, not an automatic unrelated decision. Same institution alone is not incident evidence. Use explicit same-incident / related-issue / unrelated choices and a required reason. For new pending reviews, require deliberate selection instead of preselecting same incident. Preserve existing decisions, stale-edit drafts, HTTP 409 handling and auditor read-only behavior.

Mobile stacks the same labeled comparison panels. Keyboard order, headings, labels, focus restoration after a conflict, loading/error/empty states and large text must remain usable. No cross-Bureau relationship text, counts or attachment metadata is delivered to officers.

**Gate A:** All old workflows remain reachable; review decisions and histories are unchanged semantically; dedicated desktop/mobile and role tests pass against bundled assets.

## 4. Milestone B — explainable matching, evaluated before activation

### Evidence contract before ranking changes

Extend existing `OverlapCandidate.evidence` with a versioned schema, preserving old evidence rendering. Keep `score` as actual MiniLM cosine and `model_revision` as the encoder revision. Add a separate matching-policy revision, discovery methods, evidence source and comparison status. Do not turn lexical ranking or metadata into an invented confidence percentage.

| Signal | Meaning and limit |
| --- | --- |
| Source system plus source reference and fingerprint | Exact re-upload versus changed-source conflict, using existing intake semantics |
| Equal references from different systems | Review evidence only; not the same source identity |
| MiniLM cosine | Similarity of original allegation summaries, not incident probability |
| Lexical rank | Shared language/reference discovery, separate from cosine |
| Incident dates/categories/remedies | Recorded agreement, difference or unknown; no hard exclusion by date/category |
| Reviewed extracted fact | Later milestone; includes source and review state |
| Attachment checksum | Optional later same-bytes evidence; does not establish the same incident |

Use statuses such as `agrees`, `differs`, `unknown` and `unverified`; show provenance. A conflicting allegation is not a verified contradiction. Never infer applicant identity from a name match or missing field. Correct `shared_reference` handling consistently in semantic and manual paths so empty values are not affirmative evidence, and distinguish shared text from shared source identity.

Record the evidence/policy revision seen at decision time in the existing transactional CaseAction for each complaint. Preserve reviewed decisions and their supporting snapshot when matching reruns. Avoid a parallel audit store. Existing legacy reviews remain valid and clearly labeled as lacking a newer evidence snapshot.

### Candidate discovery

Keep canonical institution as the mandatory retrieval boundary, including closed cases. Start in shadow evaluation with a bounded union of existing semantic results, lexical results and explicit-reference results. Provisional experiment budgets: semantic top 20 plus lexical top 20 plus at most 20 reference results, deduplicated to at most 60 comparisons per query. Measure recall before adopting these limits; display at most five ranked review suggestions initially. Common references can exceed the cap and must be reported in evaluation.

Use PostgreSQL 17 full-text search and a GIN index where measurements justify it. PostgreSQL's `ts_rank_cd` is cover-density ranking, not BM25 or a probability ([PostgreSQL documentation](https://www.postgresql.org/docs/17/textsearch-controls.html)). No Elasticsearch, new vector database or global all-pairs comparison is needed.

For lexical-discovered pairs, compute genuine cosine when embeddings are ready; never fabricate a score of zero or misuse manual origin. Extending automated origins/nullable-score constraints requires an explicit migration and serializer update if the current origin semantics cannot represent the chosen policy. Keep discovery provenance in evidence. A lexical candidate below the existing semantic threshold must be labeled as lexical-discovered, not as having passed that threshold.

The frozen semantic-only production path remains available. Candidate ordering, lexical cutoffs and evidence rules are selected using calibration data, versioned separately from the model, then tested once on held-out data. Do not silently activate broader retrieval or overwrite the active threshold.

### Evaluation and data

First make `evaluate_matching.py` output-only by default: it currently writes `backend/calibration.json`. An experiment must write to an ignored run directory and never modify production calibration implicitly.

Reuse the current synthetic corpus as a regression dataset. Add separately reviewed domain examples, difficult negatives, missing/conflicting fields, shared generic references, long text and large institutions. Split by incident family and near-duplicate text. Keep query complaints distinct from reference complaints and document corpus eligibility. Preserve the three relationship labels; define review-worthy positives separately from same-incident retrieval metrics.

Compare unchanged production retrieval, lexical-only retrieval and the bounded union. Report suggestion precision, relationship confusion matrix, same-incident Recall@5, candidate recall, coverage, abstentions, sample counts and uncertainty. Calibrate only on the calibration split. Proposed activation targets remain at least 85% review-worthy precision and 90% same-incident Recall@5, without regression against baseline; they are unmeasured objectives. Synthetic/public-paraphrase results cannot establish real AICTE accuracy. If independently reviewed domain data is unavailable, keep the candidate experimental and disclose the limitation.

**Gate B:** Offline evaluation and shadow runs pass; pending-pair reruns are idempotent; reviewed evidence/decisions survive; current source duplicate behavior and role isolation pass. No production activation solely because a demonstration looks convincing.

## 5. Milestone C — source-grounded briefs and incident organization

Deliver a deterministic brief first, composed from existing case fields, latest authorized actions and current coordination state. Label allegations as allegations. Dates, status, assignment and next actions must come from current authoritative records, not a cached generated paragraph. No LLM dependency is required.

Then introduce a small reviewed fact model only for facts needed by comparison: explicit incident date/reference and requested remedy initially. Each proposed fact contains case, type, normalized value, original source field, exact span/quote, source digest, extractor revision, review state, reviewer and optimistic version. Missing or ambiguous text stays unknown. Corrections append reviewed evidence; the original allegation remains immutable. Officers may propose facts only for currently authorized cases; coordinators accept/reject them; auditors cannot mutate. Every review creates an existing CaseAction, with appropriate restricted-detail redaction.

Introduce manual incident groups only after fact/review contracts stabilize. A group belongs to one canonical institution and has protected membership, reason, actor and version. A complaint may contain multiple incidents, so membership is not automatically exclusive. Use unique group/case membership and transactional validation that cases belong to the group's institution; enforce critical cross-table invariants in PostgreSQL as well as the API. Retire membership through an audited operation rather than deleting historical evidence.

Groups do not merge cases, change deadlines, acknowledge coordination or dispose complaints. Related-issue links do not imply same-incident membership. Do not construct groups automatically by transitive closure of pair decisions. Changing a supporting relationship must flag the group for review, not silently remove cases or leave an invalid confirmation unnoticed.

Coordinator/auditor group views are sufficient initially; officers receive no group identifiers, membership counts or hidden relationship detail. Extend `ActionReadSerializer` redaction deliberately: it currently recognizes `overlap_review` and `coordination_` action kinds, so an arbitrary new group action could otherwise leak data.

Use additive migrations after existing `0013`; allocate final numbers at implementation. Preserve original rows and append-only triggers. New foreign keys protect records from cascaded deletion. Reuse the institution-first transaction lock order already used by matching/manual/review operations, then acquire pair/group and sorted case locks consistently. Test concurrent reviews, transfer and group changes rather than introducing conflicting lock orders.

**Gate C:** Every extracted value has inspectable source evidence; corrections and membership changes are audited; stale versions return 409; officers cannot recover restricted information through histories, counts, exports or notifications.

## 6. Milestone D — optional read-only MCP

MCP is an integration interface, not a matching improvement. Keep Django APIs as the permission authority. Add one optional local adapter using a pinned, supported official Python SDK, selected at implementation time; the SDK currently documents v2, so do not copy an old framework API without checking compatibility ([official SDK](https://github.com/modelcontextprotocol/python-sdk)).

Start with local stdio only, disabled by default. Bind each process to one real official using an explicitly configured, protected upstream Django session credential. Do not accept `user_id`, Bureau or role as identity claims from tool arguments; never use a shared administrator credential. Read requests go through the same localhost DRF endpoints, so current membership and ownership are recalculated on every call. Expired/revoked sessions fail closed. Credential setup/logout/revocation must be documented and tested before enabling the adapter.

The MCP authorization specification distinguishes HTTP authorization from environment credentials for stdio ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). This local design is not remote OAuth. If remote HTTP access is requested, stop at a separate OAuth identity/audience/resource design gate. Never forward an arbitrary client bearer token as upstream authentication; follow the protocol's security guidance ([security](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)).

| Tool | Existing source / addition | Scope |
| --- | --- | --- |
| `search_institutions` | Paginated registry | Current authorized registry scope |
| `search_cases` | Shared case filters | Current authorized cases only |
| `get_case_brief` | New deterministic brief endpoint | Authorized case; redacted related information |
| `find_related_cases` | Existing overlap query scoped to case | Coordinator/auditor only initially |
| `get_case_history` | New paginated case-action read endpoint | Reuse current action serializer/redaction |
| `get_coordination_status` | Existing records/requests | Management records; officers only their authorized instructions |

Validate schemas, cap pages/output, use explicit continuation links, and allow only fixed upstream paths and a configured loopback origin. No arbitrary URL, SQL, filesystem, download, export or mutation tools. Read-only annotations aid clients but do not enforce security. Log access through minimal AuditEvent metadata, not fabricated case actions; exclude credentials and complaint bodies from logs.

Treat complaint text as untrusted data, including instructions embedded in it. Using a local adapter does not guarantee a local assistant: clients may send responses to a cloud provider. Enable first with synthetic data; real complaint access requires an approved client/data-handling policy and explicit operator configuration.

UTCP stays deferred until there are actual independent Bureau services, native API/authentication contracts and an interoperability test case. Its manual describes discovery and native calls; it does not provide grievance understanding or replace permission enforcement ([official RFC](https://www.utcp.io/about/RFC)). No UTCP gateway or SDK is needed now.

**Gate D:** Six bounded read tools work with real per-user sessions; revocation/membership changes take effect; unauthorized case/relationship/history access fails; malformed tool calls and prompt injection cannot trigger writes.

## 7. File-by-file execution backlog

All paths below are repository-relative. Files marked new are proposed, not present implementations. Add focused modules only where needed; reuse existing serializers and workflow operations.

| Phase | Files and required changes | Tests/callers/config to cover |
| --- | --- | --- |
| A: navigation | `frontend/src/main.tsx`: Shell, breadcrumbs, route `/work`; new `frontend/src/my-work.tsx` as a small link/filter hub | Existing browser specs asserting exact navigation text; direct URLs and browser Back |
| A: contextual navigation | `institutions.tsx`, `imports.tsx`, `source-intake.tsx`, `management.tsx`, `coordination-workflow.tsx` | Older imports/conflicts, movements, escalation and review remain discoverable |
| A: comparison | `main.tsx` existing PairReview, `api.ts`, `style.css`; extract component only if it reduces actual duplication | `workflow.spec.ts`, `phase2.spec.ts`, new `case-intelligence.spec.ts`, mobile and keyboard checks |
| B: evidence and review | `backend/cases/matching.py`, `relationships.py`, `api.py`, `serializers.py`; reuse existing evidence JSON before adding columns | `tests/backend/test_workflow.py`, `test_phase2.py`, `test_source_intake.py`; evidence snapshot and 409 regressions |
| B: retrieval/schema | `models.py`, additive migration, `matching.py`; built-in PostgreSQL full-text search and bounded queries | New `tests/backend/test_case_intelligence.py`; SQL plans, concurrency, reruns, origin constraints |
| B: evaluation | `management/commands/evaluate_matching.py`, separate documented fixture manifest and ignored per-run outputs | Guard against active calibration writes; family leakage, missing evidence and retrieval-limit tests |
| C: briefs/facts/groups | New focused `backend/cases/case_intelligence.py`; `models.py`, migrations, `serializers.py`, `urls.py`, action redaction in existing serializer | API permission, provenance, source span, append-only audit, concurrency, protected deletion and group consistency tests |
| C: UI | `api.ts`, existing case detail in `main.tsx`, `institutions.tsx`, `relationships.tsx` | Brief/fact review, institution coordination links, evidence unknown/error states; no frontend history store |
| C: reports | `exports.py`, relationship export in `relationships.py`, relevant institution/report views | Export escaping, evidence/policy revision columns, matching list/report counts and restricted fields |
| D: MCP | New `backend/cases/mcp_adapter.py`; narrow additions in `urls.py` for brief/history; `backend/requirements.txt` and `requirements.lock` only at this phase | New `tests/backend/test_mcp_adapter.py`; optional SDK environment, session expiry, no arbitrary paths/writes |
| D: configuration/docs | `backend/config/settings.py` only if configuration is actually required; `.env.example`/`.gitignore` and startup docs | No credentials in Git or graph; do not start MCP with the ordinary demo automatically |
| E: verification | Existing `compose.audit.yaml`, `frontend/playwright.config.ts`, `scripts/benchmark.py`, `benchmark_import.py`, recovery/offline scripts | Reuse isolated URLs/database/storage, existing fixtures and per-run evidence layout |
| E: handoff | `START-HERE.md`, `README.md`, `tests/README.md`, readiness report and Graphify source/document map | Correct user journey, limitations, rollback, operator instructions; retain historical results |

Before editing any listed file, inspect its current callers/tests and verify its name against the then-current tree. Do not add dependencies for built-in PostgreSQL ranking, hashing or deterministic briefs. MCP remains the only planned protocol dependency, and only in its gated phase.

## 8. API and migration compatibility

Preserve `/api/institutions` lookup response, registry pagination, all existing case/action/import/coordination routes and `disposed` database status. The UI continues to label it Closed. Keep optimistic versions and submission UUID behavior.

Initial A uses current contracts only. B adds backward-compatible evidence fields and, if needed, an authorized paginated `/api/cases/{id}/related` read endpoint; officer requests are denied. C adds `/api/cases/{id}/brief`, paginated `/api/cases/{id}/history`, narrowly scoped fact proposal/review endpoints and incident-group endpoints. Fix exact DTOs and error contracts before frontend work. Existing action history remains authoritative.

Separate schema additions, bounded data backfills and policy activation. Do not rewrite original allegations, old decisions or historical Bureau snapshots. Optional attachment hashing uses private authorized storage, records content checksum only and resumes in bounded batches; file-byte equality is never incident equality. Defer OCR, generic entity extraction and attachment interpretation.

## 9. Verification and delivery gates

1. Preserve source checkpoint and current ignored data/model/graph recovery artifacts. Configure independent test database, storage, API/frontend ports and read-only model assets. Confirm test settings before any fixtures or imports.
2. For each milestone run focused tests, then all discovered Django tests, production build and full Edge/Playwright suite against bundled assets. Update actual navigation assertions, not weaken workflow expectations. Add tests rather than claiming earlier 53 tests cover new screens.
3. Exercise coordinator, auditor and officer journeys. Include membership changes after login, transfer ownership, stale review/edit conflicts, pagination beyond 20, direct URL/API access, reports/exports, attachments and action redaction. Check zero versus malformed data, keyboard access and mobile layout.
4. Reconcile filtered dashboard/list/export results and all-time institution history. Rehearse registration -> institution -> comparison -> human decision -> coordination -> transfer -> audit. A relationship decision alone must not change ownership, deadlines or status.
5. Benchmark 1,000 and 10,000 synthetic records with ten independent users, realistic text and both dispersed/skewed institutions. Measure queue delay, candidate volume, DB plans, p95 reads/creation/dashboard, import completion, RAM and errors. Targets remain p95 reads/creation <500 ms, dashboard <1 s and warm 1,000-row completion <2 min; optimize measured failures before adding caches/index types.
6. Restore database/private files into a separate destination, verify pinned model checksums and worker restart/idempotency. Repeat physically disconnected cold startup with operator assistance and record evidence. Blocking external requests alone is not that test; do not disconnect the user's network without a recoverable procedure.
7. Refresh Graphify after source changes, exclude private data/uploads/models/secrets and preserve extracted versus inferred distinctions. Store verification artifacts in ignored per-run directories, with a concise tracked result/traceability report. Do not replace historical evidence.
8. Inspect the exact diff and recoverable feature checkpoint. Publish normally only after that milestone's agreed gates pass and publication is authorized. Never force-push; verify local/remote hashes. The previous publication's physical-offline waiver is not an offline certification for future code.

Rollback A restores source only. Rollback B selects the previous matching policy without deleting reviewed pairs/actions. C migrations remain additive; disable new writes/features rather than delete facts, groups or audit records. D is disabled by stopping the optional adapter and revoking its session; core application operation remains independent.

## 10. Order, effort and decisions

Implement A first; then B evidence and non-mutating evaluation; then evaluated discovery; then C deterministic briefs, reviewed facts and manual groups; then optional D; finish E. Security and regression gates apply continuously, not only at the end.

Indicative single-contributor effort: A 2-3 working days; B 3-5 days excluding independent domain labeling; C 4-6 days; D 2-4 days after identity setup is accepted; integrated verification 2-3 days plus operator-assisted checks. These are planning estimates, not performance or delivery guarantees. Real-data access/review is an external dependency with no promised completion date.

The first implementation checkpoint should contain only simpler navigation, contextual links, improved existing PairReview and their browser tests. No model changes, new data entities or protocol installation are needed to deliver that improvement.

Unresolved evidence: official AICTE workflow compliance, independently reviewed real complaint accuracy and physical offline startup. None should be claimed complete from synthetic tests or this planning audit.
