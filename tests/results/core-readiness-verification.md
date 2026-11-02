# SIH 26264 - Final core intelligence readiness

Status: engineering verification completed; source publication authorized. Physical offline, independent real-data review, licence clarification and the stated missed latency objectives remain open. This is not production or model-accuracy certification.

## Source and safety

The pass starts at `2a47597` on `codex/core-intelligence`, descended from unchanged local/remote main `f73fc0e0bcb33ef1a5f0342bf9c817dca3ce6097`. Recovery branches preserve both the original main and `2a47597`. The performance/source changes are checkpointed at `c404cde`. The user subsequently authorized normal publication to main after engineering verification. This source-publication authorization does not establish physical-offline or real-data/model acceptance. The review named a nonexistent `core-intelligence-verification.md`; the actual prior baseline is `SIH_26264_CORE_INTELLIGENCE_IMPLEMENTATION_REPORT.md` and its JSON evidence.

All mutations use isolated audit, profiling, research, benchmark or restored databases and private storage. The working demonstration database remains stopped. Raw research, weights, backup archives, private files and per-run logs remain ignored. Original calibration/model files and histories are preserved.

## Corrections and measured rationale

The source trace confirms one Q2 worker, bounded 64-case import matching tasks, 32-input encoder batches, institution locks and retries. `matching_queue_ms` measures a complaint's age until matching starts, including registration and previous batch work. It is not pure broker waiting time. New telemetry separates ready/locked broker rows, pending complaints, database lock waiters and container/host resources.

A 32-case SQL probe reduced matching statements from 418 to 386 by reusing the institution already locked; neighbour queries no longer deserialize unused embeddings/descriptions. A summary probe exposed full-row DISTINCT counts including vector/text columns. Narrow ID aggregates, a union of pending-pair endpoints and consolidated pair counts preserve definitions while reducing summary queries from 11 to 8. An intermediate combined aggregate was measured and rejected because its plan was slower; its evidence is retained. Exact search, top-five bounds and thresholds are unchanged.

Sequential idle task dispatch measured p95 1,022.86 ms at poll=1 second and 233.90 ms at poll=0.2 seconds (12 successful probes each). Worker concurrency, queue/bulk limits, institution locks and 120-second timeout/300-second retry are unchanged. The idle broker now checks up to five times per second; this is a small database polling tradeoff, not extra inference workers.

## Functional acceptance

Existing six-case/group/coordination, pagination, stale and concurrent edits, retirement, CSV reconciliation and role regressions are preserved. New regressions bound summary queries, check unused neighbour payloads, distinguish unrelated cross-Bureau monitoring from a confirmed incident and test direct APIs/UI with feature gates disabled. Grouping and reviewed facts remain off in live defaults; enabled acceptance is confined to the audit environment.

| Check | Result |
| --- | --- |
| Full Django suite, enabled audit configuration | **221 passed**, 91.881 s; exit 0 |
| Full Django suite, default-disabled configuration | **221 passed**, 100.297 s; exit 0 |
| Full bundled Edge suite, enabled | **81 passed**, one intentional disabled-only skip, 11.1 min; exit 0 |
| Actual disabled-gate Edge check | **1 passed**, 6.7 s; exit 0 against actual disabled API |
| Startup/controller tests | **5 passed**, 13.027 s; exit 0 |
| Locked production build | Passed again through preparation, **8.55 s** build; earlier 38.54 s build retained |
| Migration drift / unapplied migrations | No changes detected; checks passed |
| Frozen shadow diagnostic | Completed; exit 0 |

Backend regression includes two independent source-workbook/packet checks. Default-disabled backend discovery retains explicit enabled test classes for their own contracts; the actual disabled HTTP/UI check is run separately. The enabled full browser suite intentionally skips that one disabled-only test, rather than pretending both server configurations are active simultaneously. The initial full run had 80 passing tests, one skipped and one cancellation-test race failure. The fixed 1.5-second response delay could elapse before navigation under load. It was replaced with a response-release handshake after navigation, preserving the abort, stale-data and page-error assertions. Three repeated cancellation runs passed in 39.7 seconds before the final full rerun; the original failure log/trace is retained.

## Before and after

One measurement per profile on the same approximately 16 GB Windows laptop, CPU MiniLM, Docker PostgreSQL and ten independent authorized HTTP users; other application work was kept out of the timed imports. These are not repeated controlled trials or statistically established improvements. Added queue telemetry introduces a sampling difference from the historical run.

| Measure | 1,000 before | 1,000 after | 10,000 before | 10,000 after |
| --- | ---: | ---: | ---: | ---: |
| Preview | 9.51 s | 5.75 s | 55.31 s | 59.89 s |
| Statistical report after confirmation | 13.21 s | 10.84 s | 109.76 s | 90.88 s |
| Full matching/report after confirmation | 47.52 s | **39.57 s** | 693.95 s | **595.21 s** |
| Matching execution p95 | 28.79 ms | 27.53 ms | 66.18 ms | 62.15 ms |
| Complaint-age-to-match p95 | 33.67 s | 28.19 s | 548.68 s | 475.79 s |
| Incident summary p95 | 518.20 ms | 553.90 ms | 598.40 ms | 497.25 ms |
| Ordinary read p95 | 363.60 ms | 545.15 ms | 273.20 ms | 266.58 ms |
| Registration p95 | 182.67 ms | 627.47 ms | 171.15 ms | 369.63 ms |
| Dashboard p95 | 330.82 ms | 452.45 ms | 461.13 ms | 666.89 ms |

Observed full completion improved approximately 16.7% and 14.2%; larger-workload matching stage fell from 584.26 to 504.83 seconds. These measurements support retaining the small dispatch/query changes, not claiming every operation became faster. **The 1,000-record read, registration and incident-summary p95 objectives were missed.** These remain documented performance limitations; publication of source is not a claim that all targets passed. The 10,000-record ordinary reads/registration and incident summary were below 500 ms, and both dashboards were below one second. All 1,000-row preview/statistics/two-minute completion objectives passed. A 10,000-row two-minute completion claim is not made. The 10,000-row group CSV p95 was 507 ms; not all endpoints meet 500 ms.

All rows matched and list/CSV counts reconciled. Completed exports contained exactly 1,011 and 10,011 records, including warmup and subsequent registrations. New broker telemetry observed at most one/two persisted rows and at most one ready task, despite up to 1,000/9,936 pending complaints. Most recorded waiting is serial remaining work, not thousands of ready Q2 tasks. Database lock waiters peaked at one/eight in sampled observations; sustained contention was not established by these samples.

For 10,000 records the database averaged approximately 98% Docker CPU (roughly one core), worker 50% and API 38%; sampled maxima were 141%, 110% and 95%. This supports database/exact-search work as a remaining cost and does not justify blindly increasing workers against the same institution lock. Sampled memory maxima were API 203 MiB, worker 477 MiB and database 295 MiB; whole-host used memory reached 14.2 decimal GB including unrelated applications. Samples are not guaranteed process peaks. Complete before/after CPU/memory and objective booleans are retained in the portable JSON. No approximate index or permission-sensitive cache was introduced.

These are synthetic laptop measurements, not real complaint accuracy or million-record capacity. The orchestrator now returns a failing exit code if any workload fails, rather than only recording it. Functional completion and performance objective attainment are reported separately.

## Source-grounded representations

A fresh empty research database reran the frozen 13-record/six-query authored diagnostic. Results retain relevant/missed/false case IDs, per-channel bounds, threshold abstentions, exact source passages/digests and representation costs in `core-readiness-shadow.json` and ignored raw evidence. All labels remain synthetic.

| Method | Returned | Same-incident Recall@5 | Review-worthy precision |
| --- | ---: | ---: | ---: |
| Production summary + frozen threshold | 0 | 0 | Unavailable; abstained on all six queries |
| Semantic top-20 | 36 | 0.833 | 0.222 |
| Lexical top-20 | 0 | 0 | Unavailable |
| Exact-reference top-20 | 6 | 1.0 | 1.0, by fixture construction |
| Hybrid top-five | 30 | 1.0 | 0.267 |
| Summary + selected description top-five | 30 | 0.833 | 0.233 |
| Paragraph top-five | 30 | 1.0 | 0.267 |

All six queries had six eligible references, so top-five ranking truncates one reference per query; top-20 channel limits did not truncate this tiny corpus. Broad paragraph/hybrid ranking returns 22 unrelated suggestions out of 30. Exact shared references are deliberately constructed and are not general evidence of incident identity. The production summary cutoff abstains on this adversarial source-selection fixture; that result cannot be generalized to the full application or real data.

Warm representation microprobes encoded seven unique summaries in 0.044 s, seven selected-description inputs in 0.404 s and fifteen paragraph inputs in 1.121 s. Dense float32 storage was 10,752 / 10,752 / 23,040 bytes respectively before indexes/metadata. These tiny shared-laptop microprobes are separate from end-to-end benchmark timings; deduplicated stored arrays and source provenance are retained independently. Better recall here comes with false suggestions and extra inference/storage cost. No representation or model was promoted.

Production MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, weights SHA-256 `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`, threshold `0.603080153465271` and summary-only policy remain unchanged. Optional reranker, alternative encoder and fine-tuning activation are blocked without valid independent education incident labels. Retrieval ranking and incident classification remain separate.

## ACSS handoff and external gates

The inspected source still has 14,272 nonempty support records, including 585 literal Complaint labels, not 14,272 verified incidents. The checksum-verified original was retained privately. A new convenience packet has 20 unique bounded literal Complaint narratives, ten unscored adjacent pairs, two shuffled blank reviewer files, blank adjudication and privacy/identity review. Six short/long records and 27 repeated text representations were excluded during selection. No canonical identities, family labels or model scores are invented. The internal per-record `source_text_sha256` is a normalized subject/description digest used for deduplication; exact original provenance is the checksum-verified workbook plus source row ID, retained privately.

Existing conservative masking was applied, but it found no configured-pattern matches in those selected records. This does not exclude names or contextual identifiers. **Manual privacy review is pending**, so the packet is not cleared for distribution or annotation use. Follow `docs/acss-annotation-handoff.md` before granting actual reviewers access.

The stored released publisher metadata specifies CC BY-NC 4.0, while the article reportedly describes CC BY 4.0. A fresh API attempt returned HTTP 403 and the article presented a browser challenge; neither restriction was bypassed. Historical licence inconsistency remains unresolved pending publisher clarification. Training, evaluation and redistribution clearance remain false. No request was sent to anyone. Independent incident labels remain zero; real education precision/recall is unavailable.

## Startup, recovery and offline

The original pre-change archive was restored again into `coordination_core_preservation_1648f679a0`; migrations 0016/0017 preserved all 22 original case tables by count and original-column digest. No schema changes were introduced in this optimization pass.

Actual worker restart retained one pending case and durable queue row, then completed matching in **12.88 s**. Current-state recovery restored `coordination_restore_final_b4d96afcea` with all table digests matching; private attachment downloads and model manifests/checksums verified, including 25 incident groups and 12 reviewed facts at that snapshot. The database archive SHA-256 is `fa1ebf8bc0f0ef6c8a43e6d20dbcec4dafbd55c547716e95d87578c476c93671`. These archives and private records remain ignored.

The audit controller performed clean shutdown, preparation with `npm ci` and a fresh production build, then prepared startup with pinned local assets. Existing audit data was detected and no seed fixtures were added. Disabled-gate startup and its actual browser check passed; the audit stack was then restarted with gates enabled for the full acceptance suite. This verifies preparation using existing local Docker/model assets, **not installation on a brand-new machine**. Networking was connected; no physical-offline pass is claimed.

The operator check now includes the six-case core workflow and imports, plus coordination, existing workflows and readiness tests. It enables gates only in the isolated acceptance process and refuses to continue with any physical adapter Up. Automated guard tests mock adapter state; they do not disconnect the network or establish physical-offline success.

After preparing the audit environment, the operator disconnects Wi-Fi/Ethernet, runs `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/verify-physical-offline.ps1`, waits for the saved result, then reconnects. **Physical offline remains unverified until that actual disconnected run is recorded.**

## Five-minute SIH demonstration

Use `tests/fixtures/core-intelligence/README.md` and the RB/PGRC CSVs in the audit portal. Register one fictional institution, import three complaints per Bureau and replay an upload to show idempotency. Compare original evidence and explicitly review a relationship. Create one supported six-member incident: show six complaint records, one incident group and six distinct grouped cases, plus matching coverage and reconciled list/CSV. Create coordination from the current group version, assign both Bureaus, acknowledge and finish their instructions, then record the outcome. Show unchanged independent case statuses and authoritative histories. Demonstrate correction/stale conflict/retirement separately. An unrelated complaint can still warrant cross-Bureau monitoring without being labelled the same incident.

Do not present top-five retrieval as a complete count of similar complaints. Confirmed groups require explicit review; similarity alone establishes neither identity nor incident truth.

## Evidence and publication

Run directory: `tests/results/runs/core-readiness-20261102-183639/` (ignored). Portable aggregate JSON, selected synthetic screenshots and this report are retained; historical logs are not overwritten. The feature and recovery checkpoints are retained. The user authorized fast-forward publication after engineering verification; a normal push will be hash-verified. Publication is not unconditional release sign-off: physical disconnection, human privacy/incident review, licence clarification and missed latency objectives remain explicit.

Graphify refreshed through source checkpoint `967c1a5`: 1,575 nodes, 3,983 directed edges, 115 communities and 170 represented source files. Twenty changed-source digests and unchanged supplemental CSS were verified. Health reports zero missing/dangling endpoints, duplicates or directed collapses, with 16 disclosed AST self-loops. The five portable artifacts preserve source evidence; they do not certify model accuracy or release readiness. Final evidence is preserved in the commit containing this report. Normal push verification records the exact local/remote commit in the ignored run receipt `publication.json`; the final response also identifies the verified commit. This source publication does not close the external validation gates.

Selected synthetic screenshots: `core-readiness-desktop.png` and `core-readiness-mobile.png`. The failed initial run, its trace and all later logs/exit codes remain separate in the run directory; no failure evidence was overwritten.
