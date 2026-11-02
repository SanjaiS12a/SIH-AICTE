# AICTE Operational Workflow Completion - verification

Baseline: `557b9793414528fd66f7ed2612309f9d17a02f6b`. Implementation checkpoint: `99f77af14686605e38ac1c37117bd83d34c5056e`. Recovery branch: `codex/recovery-pre-operational-557b979`. Final publication receipt is saved in the ignored per-run evidence directory after a normal push.

## Delivered workflow

Authenticated Help explains canonical institutions, structured categories, summary similarity, human-reviewed relationships, independent case outcomes and accountable coordination. It downloads the existing fictional RB/PGRC fixtures without maintaining another copy. Five primary navigation sections remain unchanged. The guide distinguishes previous measured timings from refresh and from external integration; it makes no allegation-truth or real-world accuracy claim.

The isolated `-Audit -Demo` controller invocation enables reviewed facts and incident groups, exposes a read-only session indicator, restores temporary environment variables and preserves existing metadata, volumes and records. Normal deployment flags remain disabled. Preparation and offline startup are separate operations. Preparation refuses dependency mutation while another workspace Vite process owns installed files; stopping a preview checks workspace ownership and process creation time.

Categories add Other and Needs categorization. Missing/blank complaint values use the latter; unknown source labels need explicit mapping. Summary category requirements are unchanged. Server options supply labels. Coordinator category corrections use existing case versions and authoritative history without regenerating embeddings.

The existing source-conflict endpoint supports coordinator-only approval of selected source status/disposal, category, classification and deadline values. Server comparisons identify blocked fields and retained differences. Original allegations, identities, source references, receipt, Bureau and assignment remain protected. Closing validates evidence against the original case receipt and clears next actions. Reopening requires explicit confirmation. One institution-first locked transaction increments the case version, resolves the row and appends action/audit evidence. Siblings, incident groups and coordination outcomes remain independent. HTTP 409 preserves the frontend draft until explicit reload.

Exactly repeated reviewed source snapshots are recognized through batched append-only evidence; they do not overwrite later official actions or reapply matching. Original submission fingerprints remain unchanged. The UI says Reviewed - selected changes applied rather than fully synchronized.

## Traceability and completed checks

| Requirement | Evidence |
|---|---|
| Blank/unknown/mapped/Other category; correction and stale versions | `tests/backend/test_operational.py`; browser operational scenario |
| Coordinator-only approval, selected fields, blocked fields, disposal dates | Same backend module; source-intake role regressions |
| Closure/reopening and unchanged siblings | Backend tests; six-case browser scenario |
| Concurrent approvals, exact retry and repeated upload | Backend concurrent test, replay checks and import benchmarks |
| Original allegations/fingerprint, relationships and append-only history | Backend assertions and browser final case/group checks |
| Dashboard/list/export reconciliation | Existing full browser suite plus new six-case summary checks |
| Demo isolation, environment restoration, preparation guard | `tests/operations/test_startup.py` |
| Keyboard/mobile and draft recovery | Operational browser tests and existing accessibility suite |

All discovered backend tests passed: **230 / 230**, 72.816 seconds, with demo intelligence enabled. A separate normal-default run passed **230 / 230**, 80.266 seconds. Startup-controller checks passed **10 / 10**, 13.118 seconds. The four dedicated operational browser tests passed in 26.2 seconds before the final complete-suite run. Production preparation/build passed in 28.53 seconds. Full browser and performance results are appended below when complete.

Migration `0018_operational_intake` adds ImportJob.category_mapping with an empty default and updates category choices. No data backfill or destructive operation is included. A restored-copy check preserved all original columns and row digests across **22 pre-existing case tables**; migration checks run against the isolated audit stack. The verification helper now discovers original columns instead of assuming a fixed list of added fields.

## Evidence and test environment

Raw evidence is ignored under `tests/results/runs/operational-20261102-222329`; `tests/results/logs/operational-run.json` identifies it. Logs retain initial failures and subsequent verified reruns. Synthetic fixtures and curated results are separate from raw data, private uploads, backups and model files.

All regression and benchmark API mutations use port 8001/5174 and independent audit or ephemeral benchmark databases. The ordinary portal was observed running during verification; its previews were briefly paused for dependency preparation and restored using the existing controller after a read-only migration readiness check. Its records were not reset or seeded by the test suite. Background ordinary services and other laptop activity can affect timings.

The legacy source-history test now supplies a genuinely new source snapshot: a previously reviewed exact snapshot is intentionally acknowledged by the new behavior. Assertions on role isolation and pagination remain intact. An initial dependency installation encountered locked esbuild files; verified preview ownership checks and the controller guard resolved it. Initial test harness/fixture mistakes and a transient browser resource error remain in raw logs; they were corrected or rerun sequentially, not hidden by weaker product assertions.

Graphify was refreshed at source checkpoint `99f77af`: 176 source files, 1,640 nodes, 4,235 edges, 123 communities. No missing/dangling endpoints or exact duplicate edges were reported. Source and tests remain authoritative; extracted/inferred edges are development aids.

## Demonstration

1. Start the prepared isolated demo and open Help. Download its fictional fixtures; register the canonical demo institution if absent.
2. Import three RB and three PGRC complaints. Correct a missing category as coordinator.
3. Inspect a matching suggestion and record the relationship with a reason. Review all six into one incident; reconcile six complaints, one group and six members.
4. Create a coordination record, designate two Bureau participants, acknowledge and complete their responsibilities. Cases remain independently open.
5. Submit a changed source snapshot proposing closure of one case. Inspect the server comparison, acknowledge retained originals and approve status only. Show one closed and five open cases, unchanged six-member group and chronological actions. A stale draft conflicts and requires reload.
6. Replay that exact source snapshot; no duplicate case action or rematching occurs. Inspect unrelated cross-Bureau monitoring separately from confirmed incident findings.

The controlled request comparison contains **two authored independent requests versus one recorded simulated shared request**, two designated participants and two completed acknowledgments. It is a scenario count, not measured AICTE staff productivity savings.

## Limits

No model, threshold, training, automatic ownership routing or allegation-truth assessment changed. Independent real-world incident accuracy, privacy/licence clearance and physically disconnected cold-start verification remain unestablished. Local integration tests and prepared startup do not prove physical offline readiness, million-record capacity or legally authoritative workflow compliance.

## Measured performance

Ten independent authenticated users, CPU MiniLM on the Windows laptop (about 16 GB RAM, RTX 3050 A 4 GB present; model unchanged). The benchmark isolates database/storage but shares host CPU/memory with the ordinary portal and desktop. These are single-run comparisons, not a statistically established code slowdown.

| Workload | Preview | Statistics after confirmation | Matching/report after confirmation | Previous matching/report | Change | Duplicate preview / confirm |
|---|---:|---:|---:|---:|---:|---:|
| 1,000 distributed XLSX rows | 7.42 s | 10.13 s | 40.41 s | 39.57 s | +2.1% | 9.09 / 1.15 s |
| 10,000 concentrated CSV rows | 67.59 s | 96.12 s | 614.65 s | 595.21 s | +3.3% | 73.01 / 1.21 s |

Both imports completed every embedding, reconciled report totals and exported all resulting records. Separate replay with ten users left case/matching signatures unchanged. Replay preview still parses and validates every row; confirmation skips duplicates. These paths are not an instant full-file deduplication service.

| Ordinary HTTP p95, ten users | 1,000 | 10,000 | Objective |
|---|---:|---:|---:|
| Filtered reads | 491.8 ms | 197.3 ms | <500 ms |
| Registration | 444.7 ms | 243.4 ms | <500 ms |
| Dashboard | 295.8 ms | 415.7 ms | <1,000 ms |

All ordinary objectives passed; 1,000-row warm completion remained below two minutes. During import, read/dashboard p95 were 166.2/225.8 ms and 176.6/372.4 ms respectively. The 10,000-row job is not claimed to meet the two-minute 1,000-row target.

The measured 10,000 pipeline spent 95.15 seconds registering and 517.68 seconds matching; matching queue-delay p95 was 489.12 seconds because one worker drains the batch. Warm per-case execution p95 was 26.03 ms / 62.84 ms for the two workloads. The added replay is timed separately and does not explain first-import completion. Shared-host variation, additional category validation and source-acknowledgment lookup remain contributors; these single runs do not isolate causal attribution. No new per-row acknowledgment query was introduced. The small differences do not breach the stated objectives or justify speculative architecture/index changes.

## Final browser and migration gate

The complete bundled Microsoft Edge suite passed **85 tests in 5.5 minutes**, with its one disabled-only test intentionally skipped in the enabled run. That test separately passed **1 / 1 in 3.2 seconds** against actual disabled server gates; the isolated demo flags were then restored. Thus every discovered browser test was exercised in its intended environment. Production assets were used, with one worker and no overlapping benchmark/browser run. Migration drift and pending migration checks both returned success.

Curated synthetic evidence: [mobile guide](operational-guide-mobile.png), [selected source approval](operational-source-approval.png), [completed coordination](operational-coordination-closed.png), and [controlled scenario counts](controlled-coordination.json). Screenshots preserve the real rendered result; original conflict-validation history can retain a technical error representation even after a row is reviewed. This is cosmetic historical text, not an unresolved approval or replaced source record.

## Recovery and publication readiness

Independent current-schema recovery passed: **24 tables** matched their source rowset checksums, private-file checksums and authorized attachment download matched, restored dashboard/registry/relationships/coordination/incident/history reads succeeded, and the local 384-dimensional model loaded at pinned revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. The audit source remained unchanged and the worker was restored. The first attempt stopped on Windows cp1252 decoding of subprocess output; the complete rerun with `$env:PYTHONUTF8='1'` passed. Both logs and separate backup attempts remain preserved. This verifies restoration, not physical disconnection.

Source and evidence were reviewed for publication; environments, private files, database dumps, datasets, weights, dependencies and rotating Graphify backups remain ignored. The final normal push and exact local/remote commit receipt are recorded after publication under this run's ignored `publication.json`. Recovery branches remain available. Physical-offline verification and independent real-world accuracy are explicitly outside the completed evidence.
