# SIH 26264 — Final technical readiness report

Implementation and technically executable verification are complete on `codex/final-readiness`. **The tested fictional demonstration works; real-world matching acceptance and physical offline sign-off remain externally blocked.** Main is unchanged and no publication was performed.

## Provenance and protection

Starting feature source: `2db3af4135e6ada9774c9acdc47d506cda39fb9f` (B1.5), preserving B1 `eace867b153fe143fa6a8e17d6457b15eea77c5a`. Local and remote main were `55f3804819b3d453fdaa07c8e4e25cb5442618a3`. Recovery branch: `checkpoint/pre-final-readiness-2db3af4`. Integration checkpoints: `9210a8b`, `1d6937b` and `99c40a9`. Final verified source/configuration commit: **`4847a33765a59026ff7f29e81b864516b643914e`**. The following handoff commit contains only reports/screenshots/source-map artifacts; its hash is returned in the delivery response and local `handoff.json` to avoid a self-referencing report hash.

Fresh evidence is isolated under [this run](runs/final-20261101-205207/). Historical reports and graph backups were retained. PostgreSQL audit project `sih-readiness-115600` uses independent database/private volumes, API 8001, frontend 5174 and read-only models. Working database `sih` was only read for backup/restore comparison and remains at schema 0012; new migrations were applied only to isolated databases. Benchmark datasets use fresh `coordination_scale_*` databases, with separate private volumes for each HTTP run. No genuine research corpus was imported into an application database.

## Phase completion

| Phase | Result |
|---|---|
| 0 — Preserve/isolate | Recovery branch, protected hashes, working backup, independent audit/benchmark storage; no working data mutation |
| 1 — B1/B1.5 | Preserved and freshly regression-tested; frozen public probe rerun |
| 2 — Authentic data | Official access retry, authentic NYC reuse, private annotation packets and authorized-intake/recall protocol complete; real reviewers/permissions remain external |
| 3 — B2 | Bounded disabled shadow experiment, SQL plans and synthetic comparisons complete; production expansion not activated |
| 4 — C | Current briefs, reviewed spans and manual groups implemented/tested; independent controls default off |
| 5 — Optional MCP | Intentionally absent pending approved per-user identity/handling policy; no UTCP |
| 6 — Integration | Registry lookup, payload guards, monitoring/permission/history preservation and measured optimizations complete |
| 7 — Regression | 197 Django, 73 full Edge, 4 controller checks; additional default-mode and focused checks pass |
| 8 — Performance | Four fresh HTTP workloads, dispersed/concentrated scale tests, encoder timings and export reconciliation complete |
| 9 — Recovery/operation | Working and current-audit restore, worker restart, fresh-only seeding and connected cold startup complete; physical disconnection pending |
| 10 — Handoff | Design/lifecycle/demo/recovery documentation, source graph and consolidated safe evidence complete; feature branch only |

## Implemented corrections and intelligence

- Preserved B1 evidence/provenance, unknown states, immutable decision snapshots, human relationship decisions, optimistic conflicts, exact production top-five retrieval and existing workflow/security contracts.
- Added disabled shadow semantic20/FTS20/reference20 discovery, bounded union at 60, genuine optional cosine, separate lexical/RRF rank, source provenance, truncation statistics and PostgreSQL EXPLAIN ANALYZE/BUFFERS. Synthetic fixtures roll back; no runtime suggestions are created.
- Added current authorized case briefs and server-paginated case history. The collapsed UI refreshes only while open; allegations remain explicitly unverified claims. Officers receive only their permitted responsibilities and no relationship/group status or counts.
- Added reviewed incident-date/reference/remedy proposals with exact Unicode source spans, SHA-256, immutable evidence, explicit coordinator review, compensating corrections, versions and authoritative CaseAction history.
- Added explicit institution-bound incident groups with protected active/inactive memberships, version conflicts and before/after audit snapshots. Support must be a reviewed same-incident relationship; changing support flags review without changing members. No merging or automatic status/ownership/deadline/acknowledgment changes occur.
- Added complete-registry search to complaint registration, preserving the existing bounded lookup response. Search clears obsolete selection. Improved new forms using existing government-theme classes.
- Bounded relationship serialization now reuses one serializer over the page; movement totals use one conditional aggregate. Permission boundaries and response contracts remain intact.
- Preparation seeds only empty designated databases. Startup checks current worker initialization in addition to API readiness and pinned local assets. Test failures propagate; shutdown still preserves volumes and stops only owned services/processes.

`ENABLE_REVIEWED_FACTS` and `ENABLE_INCIDENT_GROUPS` default off independently. They were enabled only for isolated feature verification. Shadow expansion remains disabled with no activation path from its evaluator. MCP remains absent: no approved per-user identity/credential/revocation/third-party data-handling integration exists. UTCP and model training were not implemented.

## Schema and rollback

0014 adds `ReviewedFact`, `IncidentGroup`, `IncidentMembership`, protected foreign keys, source-span/review-state constraints and unique submission/member identities. 0015 adds database guards for immutable fact evidence, exact source/digest agreement, one-institution group membership, protected group/member deletion and grouped-case canonical identity. Existing append-only CaseAction/AuditEvent and `bureau_at_action` insertion protections remain intact. Legacy unknown Bureau snapshots are not backfilled.

Prefer disabling the feature controls and rolling forward. Reversing 0015 removes its guards; reversing 0014 drops new intelligence tables and would lose their data. Preserve a verified backup before any schema reversal. Tests restore the current migration leaf after historical migration checks.

## Frozen model and authentic-data evidence

Revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; threshold `0.603080153465271`; 384-dimensional local MiniLM, CPU by default.

| Protected input | SHA-256 |
|---|---|
| Weights | `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db` |
| Calibration | `ec0e112d0dbef30765c2f9d3ae000617288c95ee159eec33ebb09741c6eb14b0` |
| Model manifest | `7c179898bb2acdb955a0c2ed63bdd230f806d7262c77fd5e4a7803cae0cd35ad` |
| Synthetic regression corpus | `69f634af01869e7e98d2e95ca050ae795a893865d8415ae4cf1a68084fa37bab` |
| Reused NYC corpus | `0d61c51304d3c1e6ec1cf7101f95f81459fa775fefad96d4ad8eafba91ae5201` |

The [official CFPB API and export](https://www.consumerfinance.gov/data-research/consumer-complaints/) were legitimately retried and still returned HTTP 403 from this environment. OIA reuse permission is unresolved; no OIA corpus was collected. [An unsent permission request and institutional intake protocol](../../docs/research-permission-and-intake.md) are prepared. Authorized Indian institutional narratives and independently established incident relationships have not been supplied.

A fresh frozen-model probe reused the authentic 500-record NYC snapshot without database access: 25 queries, 421 references, 446 encoded representations, 28 suggestions across 10 queries. Zero real human judgments exist; review-worthy precision, same-incident recall, true FPR, agreement and confidence intervals are **unavailable**. The 28-pair independently shuffled, score-blinded reviewer packets and blank adjudication sheet remain private. The known-positive validator/protocol separates recall ground truth from suggestion annotation and rejects missing permission/independence evidence. It cannot certify that people actually reviewed records.

NYC inputs are structured service descriptors, not original education allegations. Fresh CPU cold construction/import time was 6.673 s (excluding preflight checksum/interpreter startup); warm encoding of 446 representations took 1.451 s. In-memory exact retrieval p95 was 0.331 ms; this is not PostgreSQL or HTTP latency. No cross-dataset accuracy is pooled. [Fresh aggregate evidence](runs/final-20261101-205207/public-frozen-summary.json).

The synthetic B2 held-out comparison used 60 queries: unchanged baseline returned 162 suggestions with 54 judged, 90% known-positive query hit rate at five; fixed shadow union returned 300 with 60 judged and 100% synthetic query hit rate. Bounded candidate recall was 100% on those known synthetic positives. Overall precision remains unavailable for both because returned-pair labels are incomplete. The reference channel returned none because fixture record IDs are unique. Calibration and test partitions stayed separate; no policy was selected from the held-out results. This diagnostic does not establish real-world improvement or authorize activation. [Full diagnostic](runs/final-20261101-205207/shadow-final.json).

## Regression and recovery evidence

| Check | Fresh result / evidence |
|---|---|
| Django complete regression | 197 passed, 70.582 s — [log](runs/final-20261101-205207/backend-signoff.log) |
| Edge/Playwright complete regression | 73 passed, 3.6 minutes — [log](runs/final-20261101-205207/browser-delivery.log) |
| New brief/fact/group/search and workbook checks | 7 passed — [log](runs/final-20261101-205207/browser-final-focused.log) |
| Fresh-stack bounded-lookup fixture | 1 passed — [log](runs/final-20261101-205207/browser-fresh-fixture.log); initial page intercepted, subsequent search uses real API |
| Production build | Passed, Vite 10.34 s, JS `index-BAw5BN96.js` — [log](runs/final-20261101-205207/build-signoff.log) |
| Migrations | Applied 0014/0015 on isolated stack; no model drift detected |
| Current audit recovery | Every case-table rowset and migration history matched; private files/model and authorized attachment downloads verified; restored facts and groups preserved — [evidence](runs/final-20261101-205207/final-restore.json) |
| Preserved working recovery | Fresh captured working dump restored in audit DB service; source rows unchanged, additive migrations/read endpoints/files/model verified — [evidence](runs/final-20261101-205207/working-restore.json) |
| Real worker restart | Two queued rows survived stop/start and completed import/matching in 8.280 s — [evidence](runs/final-20261101-205207/worker-recovery/import-queue-recovery.json) |
| Controller unit checks | Four passed, including exited worker refusal — [log](runs/final-20261101-205207/startup-final.log) |
| Prepared default-mode startup | 13.948 s; API/worker initialization/assets verified, controls off, Wi-Fi up — [evidence](runs/final-20261101-205207/controller-demo.json) |
| Default-mode browser regression | 14 passed, 41.1 s — [log](runs/final-20261101-205207/browser-default.log) |
| Group conflict/reload/mobile | Five focused intelligence tests passed, including a real concurrent group correction — [log](runs/final-20261101-205207/browser-conflict-verified.log) |
| Fresh-only seeding | Fresh designated database: 504 fully matched cases, 31 institutions, 730 actions; repeat unchanged — [fresh](runs/final-20261101-205207/seed-fresh.log), [repeat](runs/final-20261101-205207/seed-repeat.log) |

Two earlier browser runs exposed test setup faults (GET logout and assuming the bounded institution lookup contained every institution); these were corrected without weakening workflow/security assertions. The new brief's unstable validator also caused a request loop during initial testing and was fixed before final verification. The final controller also redirects per-port standard input: an earlier native wrapper retained the Vite child lifetime and did not give a usable cold-start measurement. That initial log is retained; the successful default-mode measurement above is authoritative. All earlier logs are preserved rather than overwritten. No physical offline success is inferred from these results.

## Measured performance

Hardware: Intel i5-13450HX, 10 cores/16 logical processors; Windows 11; Docker Desktop PostgreSQL runtime has 16 CPUs and about 7.61 GiB RAM. RTX 3050 A has 4,094 MiB VRAM but matching ran on CPU with two Torch threads. Measurements concern this shared laptop, not a production server or a million records.

The isolated in-process workload uses ten distinct users/connections, 1,000/10,000 synthetic cases, 100 distributed institutions or one concentrated institution, histories, relationship review and consumed streamed exports. After batching/aggregation, dashboard p95 was 358/427/618/333 ms and ordinary read p95 94/115/108/87 ms (1k distributed, 1k concentrated, 10k distributed, 10k concentrated). Relationship p95 improved in these runs from 1,527/2,059/1,436/5,850 ms to 370/992/454/482 ms. These small samples are diagnostic, with synthetic unit-vector SQL search; HTTP/model inference are measured separately. Ten simultaneous full streamed 10k exports remained seconds-long. [Before](runs/final-20261101-205207/scale.json), [after](runs/final-20261101-205207/scale-optimized.json).

Fresh HTTP workloads use separate empty databases/private volumes, 30 fictional institutions, one explicitly recorded warmup case, pinned CPU inference and an empty initial queue. Nine distinct users continuously read while the tenth imports; a separate ten-user ordinary read/create burst follows. Preview is measured for the importer before continuous readers begin at confirmation. Final case totals include the warmup and ten post-import registrations; import reports count only imported rows. Asynchronous export row counts are reconciled. Resource monitors and queue/stage timings are retained. The four runs completed without failed imported/matching rows or raised HTTP errors. Matching-stage measurements use the real frozen encoder and exact SQL policy, not synthetic unit vectors.

| Workload | Upload/preview | Statistics after confirmation | Matching/report after confirmation | Ordinary read/create p95 | Dashboard p95 |
|---|---:|---:|---:|---:|---:|
| 1,000 XLSX, dispersed | 7.93 s | 13.24 s | 45.11 s | 278 / 299 ms | 360 ms |
| 1,000 XLSX, one institution | 7.67 s | 13.26 s | 49.65 s | 296 / 324 ms | 359 ms |
| 10,000 CSV, dispersed | 59.94 s | 123.45 s | 457.71 s | 240 / 298 ms | 501 ms |
| 10,000 CSV, one institution | 52.05 s | 89.97 s | 625.24 s | 226 / 280 ms | 452 ms |

Both 1k conditions met the stated preview/statistics/two-minute completion objectives in these runs. Upload plus confirmation-to-final-report was about 53–57 seconds for 1k and 8.6–11.3 minutes for 10k; these are observations, not promises. UI refresh remains 5 seconds while visible, with import polling every 2 seconds. During imports the nine readers made 348–4,589 reads per endpoint per workload; dashboard p95 was 158–426 ms and case reads p95 130–184 ms.

Asynchronous exports reconciled exactly to 1,011/10,011 rows (warmup + imported rows + ten registration checks), completed in 0.59–2.76 s, and downloaded in 0.03–0.17 s. Sampled worker memory peaked at 470–479 MiB; API at about 98–202 MiB and DB at about 502–593 MiB. Sampling can miss brief peaks; host/GPU totals include unrelated activity. The encoder ran on CPU throughout.

Standalone warm encoding with batches of 32 took 5.625 s for 1k and 53.927 s for 10k (178–185 summaries/s); cold import/construction was 6.256 s, peak process RSS about 579 MiB. Inputs averaged 30.3 wordpieces, maximum 33; longer summaries/large attachments are not covered by these performance figures. Standalone encoding excludes broker/SQL/HTTP; it must not be confused with complete import time.

For the shadow fixture corpus, PostgreSQL EXPLAIN ANALYZE execution p95 was 0.573 ms semantic and 1.039 ms lexical over 100 queries each, using existing institution/Bureau indexes. These tiny-corpus SQL figures are distinct from the in-memory public probe and real 10k application workloads. A separate instrumented diagnostic reduced dashboard SQL statements from 49 to 41 and relationship serializer calls from 222,346 to 73,475; its wall-clock timings are not acceptance measurements.

The portable [aggregate summary](final-technical-readiness-summary.json) contains exact stage/queue timings, resource observations, export counts, model hashes and before/after measurements; raw workload evidence remains under the ignored run directory. The stored case `matching_queue_ms` is creation-to-match-start, including pipeline/batch waiting, not pure broker delay. Import audit queue timings are recorded separately. No 100k/million-record, maximum-input or production accuracy/capacity claim is made.

## Requirements-to-test traceability

| SIH responsibility | Authoritative implementation / verification |
|---|---|
| Canonical institution registry and all-time history | `institutions.py`; `test_institutions.py`; `institutions.spec.ts` (pagination beyond 20, immutable PID, edits, scope and conflicts) |
| Independent Bureau intake and conflict handling | `source_intake.py`, `imports.py`; source-intake/import tests, provided six/1,000-row workbook browser tests |
| Current ownership, deadlines and accountability | `api.py`, `tasks.py`; workflow/readiness/phase2 tests, direct SQL `bureau_at_action`, stale updates, obsolete reminders |
| Human relationship decisions and preserved evidence | `relationships.py`, `evidence.py`; `test_evidence.py`, comparison/stale-review browser regressions |
| Explicit cross-Bureau agreement and acknowledgment | `coordination_workflow.py`; coordinator/officer/auditor multi-Bureau browser journey and assignment-validity tests |
| Accurate dashboard, drills, reports and exports | `analytics.py`, `exports.py`; analytics/dashboard/readiness/movement/export reconciliation tests |
| Source-grounded intelligence and privacy | `test_intelligence.py`: exact spans, SQL guards, optimistic/conflicting reviews, group support/membership history, officer metadata/CSV isolation; `intelligence-final.spec.ts` |
| Research integrity | `test_public_evaluation.py`, `test_recall.py`; no fabricated labels, frozen-model checksum and absent-ground-truth handling |
| Reproducible operations | Startup controller checks, independent recovery scripts and worker restart proof; physical procedure remains external |

## Demonstration, remaining gates and handoff

Follow [the five-minute fictional demo and fallback paths](../../docs/technical-design.md#five-minute-fictional-demonstration): independent Bureau imports → institution profile → cross-Bureau notice → evidence/review → explicit coordination → officer acknowledgment → case action/history → dashboard/report. `START-HERE.md`, README and the design document explain the existing architecture, lifecycle, permissions and local operation.

Physical offline action still required: after disconnecting Wi-Fi and Ethernet, run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-physical-offline.ps1`, retain its result directory, then reconnect. The script never disconnects networking automatically and refuses to claim a pass while physical adapters are active.

Externally blocked: OIA permission, CFPB access, authorized institutional data, independent annotations/known positives, physical disconnection and optional MCP identity approval. No certified AICTE workflow/SLA, real-world matching accuracy or million-record capacity is claimed. All four protected model/calibration/corpus hashes match their preflight values. The retained Apache-2.0 model licence and exact asset hashes are recorded in the aggregate summary. Local and remote main were rechecked at `55f3804819b3d453fdaa07c8e4e25cb5442618a3`; no merge, push or force-push occurred.

| Severity | Remaining issue |
|---|---|
| Critical | No confirmed functional defect remains in the exercised workflows; this is not a production certification |
| Major | Genuine education/Indian-institution matching accuracy and official workflow compliance remain unvalidated |
| Minor / measured limits | Heavy 10k synchronous streams take seconds; a small-sample 1k relationship-list burst reached about 992 ms. Use the existing asynchronous export path. Maximum-length inputs, 100k and million-record operation were not measured |
| Minor / tooling | Graphify has 15 disclosed AST self-call edges; verify callers in source where ambiguous |
| Externally blocked | Publisher access/permission, authorized private data, two real reviewers/independent recall ground truth, physical offline operation and optional MCP identity approval |

Graphify final output contains **1,405 nodes, 3,559 directed edges and 101 communities**, scanning 148 permitted files with 146 represented. It reports zero changed/deleted permitted files, zero dangling endpoints and no directed collapses. Data, secrets, weights, backups, dependencies, uploads and result contents were excluded; historical graph outputs remain backed up. [Graph report](../../graphify-out/GRAPH_REPORT.md). Source and tests remain authoritative.

Selected screenshots contain only fictional fixtures: [home](final-home-desktop.png), [case brief/review](final-case-intelligence-brief.png), [incident groups on mobile](final-incident-groups-mobile.png). Normal demonstration mode leaves both experimental controls off; explicit activation is available through standard/audit Compose for review. Do not merge or push main as part of this assignment.


## Files and interfaces

New endpoints: `GET /api/cases/{id}/brief`, `GET /api/cases/{id}/history`, `GET/POST /api/cases/{id}/facts`, `POST /api/cases/{id}/facts/{fact_id}/review`, `GET/POST /api/incident-groups`, `PATCH /api/incident-groups/{id}`. Session adds read-only feature controls. Existing institution lookup, case operations, matching policy and export contracts are preserved; group actions are filtered before officer history/count/export serialization.

Verified source changes before report/map artifacts: **39 files, 1,779 insertions and 41 deletions**. New/modified source files:

- `.env.example`
- `README.md`
- `START-HERE.md`
- `backend/cases/access.py`
- `backend/cases/analytics.py`
- `backend/cases/api.py`
- `backend/cases/institutions.py`
- `backend/cases/intelligence.py`
- `backend/cases/management/commands/benchmark_encoder.py`
- `backend/cases/management/commands/benchmark_scale.py`
- `backend/cases/management/commands/seed_if_empty.py`
- `backend/cases/management/commands/shadow_matching.py`
- `backend/cases/migrations/0014_case_intelligence.py`
- `backend/cases/migrations/0015_intelligence_protection.py`
- `backend/cases/models.py`
- `backend/cases/relationships.py`
- `backend/cases/shadow.py`
- `backend/cases/urls.py`
- `backend/config/settings.py`
- `compose.audit.yaml`
- `compose.yaml`
- `docs/research-permission-and-intake.md`
- `docs/technical-design.md`
- `frontend/src/api.ts`
- `frontend/src/institutions.tsx`
- `frontend/src/intelligence.tsx`
- `frontend/src/main.tsx`
- `scripts/benchmark_import.py`
- `scripts/run_final_benchmarks.py`
- `scripts/start.ps1`
- `scripts/verify_final_restore.py`
- `scripts/verify_readiness_restore.py`
- `tests/backend/test_intelligence.py`
- `tests/backend/test_readiness.py`
- `tests/backend/test_recall.py`
- `tests/browser/intelligence-final.spec.ts`
- `tests/browser/starter.spec.ts`
- `tests/operations/test_startup.py`
- `tests/research/recall.py`

The following handoff artifact commit adds this report, the aggregate summary, three fictional screenshots and the refreshed five portable Graphify outputs. Raw logs, private corpora/annotations, backups, uploads, binaries and dependencies remain ignored.
