# SIH 26264 — Core intelligence implementation and verification

Verification date: 2 November 2026. Baseline local/remote main: `f73fc0e0bcb33ef1a5f0342bf9c817dca3ce6097`. Work is preserved on `codex/core-intelligence`; recovery branch `codex/recovery-pre-core-f73fc0e` is retained. **No merge or publication to main is authorized by this milestone.** Source checkpoints: `4818945` and `f6d8071`; the final documentation/checkpoint commit follows this report.

## Delivered behavior

An official can inspect semantic suggestions, record a relationship, explicitly group reviewed complaints, see reconciled institution/report counts, and open accountable cross-Bureau coordination from a versioned group snapshot. Complaints retain their own ownership, deadlines, statuses and histories. No automatic merging, disposal or transitive grouping occurs.

New summary APIs: `/api/incident-summary`, `/api/incident-summary/records` and `/api/incident-summary.csv`. Existing filters, current membership permissions, session authentication and exports are reused. Group detail/history, lifecycle correction and coordination creation extend the existing APIs. Coordinator/auditor counts are unavailable to Bureau officers in the backend as well as the UI.

Twelve metrics distinguish complaints, pending pairs, distinct suggested cases, reviewed same-incident/related pairs, confirmed groups, distinct grouped/ungrouped complaints and four matching states. Both pair endpoints must be in scope. A confirmed group must be active, not awaiting review and have valid supporting evidence when specified. Overlapping groups never double-count complaints. Institution profiles remain all-time; management Reports use selected receipt filters. The older pair-review preview explicitly labels its different either-endpoint scope. Stored top-five candidates are not an exhaustive similarity census.

The existing feature gates remain **off by default**. They were enabled only on the isolated audit stack for this acceptance run. Production MiniLM revision, summary-only representation and threshold remain unchanged. New literal fact kinds retain exact source spans rather than generating assertions.

## Requirement-to-test traceability

Primary tests: `tests/backend/test_core_incidents.py` and `tests/browser/core-intelligence.spec.ts`; existing intelligence, coordination, import, dashboard and security suites were retained.

| Scenario | Evidence |
| --- | --- |
| Six independent complaints, one reviewed incident | Six-case backend fixture and real registration/review/group browser journey |
| Multiple Bureaus, current independent ownership | RB/PGRC browser acknowledgments and completion; unchanged case lifecycle assertion |
| Pair totals differ from unique complaints | Distinct-count and overlapping-group backend tests |
| No inferred transitivity from A–B and B–C | Explicit chain regression rejects automatic A–C/group creation |
| Correct all-time versus receipt-filtered statistics | Receipt cohort test, Overview scope labels and scoped CSV checks |
| Group membership correction and retirement | Backend lifecycle/history test and UI correction/retirement journey |
| Stale group editing | HTTP 409 tests; browser retains conflicting draft |
| Concurrent corrections | Two concurrent requests produce one success and one conflict |
| Invalidated supporting review | Group excluded from confirmed counts without deleting membership |
| Missing/failed vectors are not zero findings | Matching partition test and UI coverage display |
| Every metric reconciles to list and CSV | All metric list/export backend checks and ten-user HTTP benchmark |
| Formula-safe export | Formula text escaping regression |
| Pagination beyond 20 | Group/history backend and browser page-two tests |
| No per-row query growth | Twenty-two-group fixed query budget regression |
| Officer isolation | Group/count/filter/export denial; existing scoped workflow regressions |
| Auditor read-only | API mutation denial and role-aware browser controls |
| Versioned coordination source | Exact member set/group version checks and immutable SQL snapshot test |
| Literal evidence provenance | Source-span/digest and unknown-year regression |
| Repeatable supplied imports | Both published CSV fixtures import and replay as six records |
| Invalid payload/mobile behavior | Missing arrays, hostile metric key and mobile containment browser tests |

## Database compatibility and recovery

Additive migration `0016_core_incident_counts` adds group lifecycle fields/index/constraint and nullable protected coordination group/version snapshots. `0017_core_evidence_protection` extends the original source-evidence trigger for the new literal kinds and protects coordination snapshots at insertion and update. Existing append-only protections remain in place. No working database migration was applied during this verification.

An independent restoration of the pre-change audit dump followed by both migrations preserved **22 original case tables**, comparing original-column row counts and digests. A separate current-state restore verified all table checksums, private attachment downloads and model files, including 21 incident groups and 11 reviewed facts in that snapshot. The working demo database was not accessed and remained stopped.

Actual worker recovery: registration persisted one queue row while the audit worker was stopped; restart completed matching in **10.37 seconds**. Prepared startup succeeded with services/models available locally. This was an online test, **not a physically disconnected test**.

## Test and build results

| Check | Result |
| --- | --- |
| Complete Django regression suite, final run | **218 passed**, 70.432 seconds |
| Complete bundled Edge suite | **81 passed**, 5.7 minutes |
| Final affected Edge regressions after final UI changes | **17 passed**, 2.2 minutes |
| Windows controller operation tests | **4 passed**, 7.984 seconds |
| React TypeScript/production build | Passed, 31.90 seconds |
| Migration drift | No changes detected |
| ACSS workbook audit unit check | Passed; also included in final Django discovery |

Raw per-run logs remain ignored in `tests/results/runs/core-intelligence-20261102-171138/`: `backend-release.log`, `browser-full.log`, `browser-final-focused.log`, `build-final.log`, `migration-preservation.json`, `final-restore.json` and `worker-recovery.json`. Historical runs were not overwritten. Portable aggregates accompany this report in `core-intelligence-verification.json`, `core-retrieval-diagnostic.json` and `core-acss-source-audit.json`. Generated artifacts describe the run; source tests remain authoritative.

## Measured performance

Local Windows laptop, approximately 16 GB RAM; RTX 3050 A 4 GB present, **CPU inference** with two threads. PostgreSQL/pgvector and one Q2 worker ran in Docker. Each workload used a fresh synthetic database and ten independent HTTP users/sessions. These are measured prototype results, not production promises.

| Measure | 1,000 distributed records | 10,000 concentrated records |
| --- | ---: | ---: |
| Preview validation | 9.51 s | 55.31 s |
| Statistical charts/report available after confirmation | 13.21 s | 109.76 s |
| All matching/final report after confirmation | **47.52 s** | **693.95 s** |
| Ordinary filtered read p95 | 363.60 ms | 273.20 ms |
| Registration p95 | 182.67 ms | 171.15 ms |
| Dashboard p95 | 330.82 ms | 461.13 ms |
| New incident summary p95 | 518.20 ms | 598.40 ms |
| Matching execution p95 | 28.79 ms | 66.18 ms |
| Queue delay p95 | 33.67 s | 548.68 s |
| Asynchronous export preparation | 1.11 s | 3.26 s |

The one-thousand-row preview, charts and two-minute completion targets passed. Ten-thousand-row processing took approximately **11 minutes 34 seconds** after confirmation; no two-minute claim is made at that size. Queue wait dominates the larger workload. All imported rows completed; no lifecycle changes occurred in incident-count reconciliation. Exports exactly matched 1,011/10,011 cases including warm-up and subsequent registrations.

During imports, 345/4,994 reads and the same number of dashboard requests completed per workload. Their p95 read times were 185/189 ms and dashboards 317/381 ms. Some new list/CSV requests exceeded 500 ms under concurrent load, so **not every endpoint meets 500 ms**. Observed sampled maxima: API 100/202 MiB, worker 462/477 MiB, database 382/423 MiB. Whole-host memory reached approximately 14.9/15.2 decimal GB including unrelated applications; samples are not guaranteed process peaks. Million-record readiness is unproven.

## Retrieval experiment and real-source intake

The frozen experiment uses 13 authored synthetic records, six queries and labels fixed before scoring. Separate arrays compare summary, selected literal description, paragraph, lexical, reference and hybrid retrieval. Exact source offsets/digests are preserved; production vectors are untouched. Cold model load was 6.25 seconds and encoding 22 unique passages took 1.34 seconds.

Production-threshold summary retrieval abstained on this deliberately difficult fixture. Paragraph/hybrid top-five reached synthetic Recall@5 1.0 but review-worthy precision was only 0.267. Exact references scored well by fixture construction. These results demonstrate representation sensitivity, **not general accuracy or a model promotion case**. No new model, reranker, threshold or training was activated.

The public [ACSS source](https://doi.org/10.7910/DVN/EITGBB) was downloaded through its official API into an ignored restricted directory and checksum-verified. Its 14,272 nonempty support records include 585 literal Complaint labels; they are not 14,272 reviewed incident pairs. Potential identifiers, repeated narratives, formulas, unverified institution mapping and the current **CC BY-NC 4.0** metadata require review. The article describes a different licence, recorded explicitly in the source register. No raw data is published, imported into application cases, scored or trained. See `docs/research-permission-and-intake.md` for the intake and independent review gates.

There is still **no independent real-world same-incident ground truth**. Real education precision/recall remains unavailable. OIA collection remains pending permission. Synthetic tests do not establish official workflow compliance or real complaint accuracy.

## Five-minute demonstration

Use `tests/fixtures/core-intelligence/README.md`, `six-case-rb.csv` and `six-case-pgrc.csv` in the isolated audit portal. Register fictional Permanent ID `CORE-DEMO-001`, import three complaints per Bureau, and demonstrate repeat-import reconciliation. Review a genuine suggestion against original evidence; explicitly group six complaints. Overview should show **six complaints, one confirmed group, six distinct grouped complaints**. Open coordination from that group, assign both Bureau participants, acknowledge and complete their work, then record an outcome. All six complaints remain independently registered. Inspect history and reconciled CSV; show a changed-year hard negative separately without silently changing the six-case example.

Screenshots: `core-intelligence-desktop.png` and `core-intelligence-mobile.png` contain synthetic records only. The manual group editor retains its visible 2–20-member prototype limit; case lists and histories are independently server-paginated.

## Remaining release gates

Physical disconnection and cold startup were **not performed**. An operator must complete that check before claiming offline readiness. Independent education incident annotation, privacy/licence review and larger-scale testing also remain open. Feature defaults stay disabled outside the audit stack. This branch is a recoverable implementation checkpoint, not an unconditional release sign-off; main remains unchanged.
