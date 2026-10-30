# AICTE upgrade verification — 30 October 2026

Implemented private CSV/XLSX import, preview and column mapping, resumable registration, separate aggregate summaries, asynchronous CSV export, print reports, refreshed analytics and versioned model staging. The portal runs at http://127.0.0.1:5173 using bundled frontend assets. AICTE branding remains a clearly labelled SIH prototype.

## Measured 1,000-row Excel journey

Actual XLSX upload, 30 fictional institutions, ten authenticated sessions (nine readers plus importer), local Docker API/worker/PostgreSQL on Windows. Intel i5-13450HX, approximately 16 GB RAM, RTX 3050 A 4 GB; inference uses CPU. All 1,000 rows imported and matched without failures. Times below are observations, not guarantees.

| Measure | Observed | Initial target |
|---|---:|---:|
| Upload and validated preview | 3.58 s | <10 s |
| Statistics ready after confirmation | 6.57 s | <30 s |
| Matching and factual report after confirmation | 37.99 s | <120 s |
| Concurrent case-read p95 | 166 ms | <500 ms |
| Concurrent dashboard p95 | 132 ms | <1,000 ms |

Actual audit timestamps separate stage delays: initial queue 0.79 s; registration 5.04 s; matching queue 0.19 s; matching stage 31.56 s. Frontend dashboard refresh is five seconds; active imports poll every two seconds, pause in hidden tabs and stop continuous polling at terminal states.

Source: `import-benchmark-complaints-1000-distributed.json`. Container memory is sampled in that report; it excludes WSL/OS overhead and is not an exact peak. Earlier measurements are retained: the original queue interleaved matching with registration and took about 160 seconds for statistics. A concentrated 1,000-row XLSX run took 92.6 seconds for matching/report under concurrent training/browser activity, and read p95 missed its target at 1.18 seconds. Dedicated dashboard-cache isolation subsequently removed shared throttle-cache contention. Do not discard the slower runs when sizing a deployment.

A separate 1,000-row monthly-summary CSV run measured 1.23 seconds for preview and 17.84 seconds after confirmation for the final report. Summary-only data skips matching. Snapshots show one date at a time and never inflate complaint totals.

## Larger read/search tests

An isolated disposable database was created and removed by `scripts/benchmark_scale.py`. Each case below used ten concurrent thread-local PostgreSQL connections. These are in-process Django measurements, not HTTP timings. Unit embeddings, one bureau, and absent overlap/history/attachment rows make this a read/search scaling test only. It does not establish 100,000-row import performance or million-record production capacity.

| Records / distribution | Cold dashboard | Cached dashboard p95 | Case-read p95 | Exact vector search p95 |
|---|---:|---:|---:|---:|
| 10,000 / distributed | 96 ms | 43 ms | 55 ms | 36 ms |
| 10,000 / concentrated | 121 ms | 40 ms | 38 ms | 36 ms |
| 100,000 / distributed | 745 ms | 32 ms | 36 ms | 33 ms |
| 100,000 / concentrated | 1,059 ms | 50 ms | 55 ms | 468 ms |

Before aggregate consolidation and coordinator/auditor caching, 100,000-record dashboard p95 was 7.1–8.2 seconds. Bureau officers are deliberately uncached and always use their current scope. Dashboard invalidation uses a dedicated database cache and cannot reset request-throttle history. Exact institution-filtered pgvector search remains in place; no approximate-index recall tradeoff was introduced.

Sources: `scale.json`, `scale-before-aggregation.json` and `hardware.json`. The one-million-record/server milestone remains untested.

## Collected data and completed training

- PAWS-Wiki Labeled Final: 49,401 train, 8,000 validation and 8,000 test pairs, downloaded from the publisher's Hugging Face mirror after the original Google archive returned 403. Checksums and publisher licence are preserved. Partitions remain separate. Token-length audit disables padding/truncation; no pairs exceed the 256-wordpiece limit.
- Indian government complaint tweets: publisher SQL payload checksum-verified; 3,700 annotated English tweets, 23 duplicate texts, no missing text. Parsed as data without SQL execution. Direct user/coordinate/ID columns are excluded from the derived file and handles, emails, URLs and phone-like numbers are replaced. Contextual names may remain; manual privacy review is pending. Classification labels are not incident-pair labels, so these records are excluded from pair training.
- Synthetic education corpus: 1,800 descriptions, 1,440 authored pairs and 360 incident families. Whole allegation templates stay within one split: 220 training, 60 validation, 40 calibration and 40 test families. The pair-review worksheet is in ignored `data/research/education_pair_review.csv`; independent human review remains pending.
- DARPG: authorized-access lead only; no restricted grievance records collected. No public AICTE complaint-text corpus has been verified.

See `source-register.json` for provenance, fields, licence, access, missing/duplicate counts and privacy limits. Raw research files, uploads and weights stay out of Git and Graphify.

CPU training completed in 1,929 seconds (32.2 minutes), including pilot, auxiliary experiment, validation, calibration and testing. Installed PyTorch was CPU-only despite the available GPU; no GPU-training claim is made. Peak native training working set was about 1.05 GB; GPU allocation was zero. Settings: MiniLM 384 dimensions, ContrastiveLoss, batch 8, accumulation 4, learning rate 2e-5, at most three epochs, seed 26264. PAWS auxiliary training used a bounded 1,024-pair training sample.

Checkpoint and variant selection used validation F1, with ties resolved by the fixed order domain then PAWS-domain. Thresholds used separate calibration data. Only the frozen selected candidate and baseline were evaluated on the new held-out test; the unselected auxiliary variant has validation results only.

| New held-out synthetic test | Precision | Recall | F1 | Same-incident Recall@5 |
|---|---:|---:|---:|---:|
| Unchanged MiniLM, newly calibrated | 100% | 66.7% | 80.0% | 70.0% |
| Selected domain candidate | 100% | 69.2% | 81.8% | 12.5% |

**Candidate rejected; existing model and threshold remain active.** The 90% retrieval gate failed substantially, despite the F1 gain. The harder synthetic benchmark also shows the baseline fails that retrieval target; neither score validates real AICTE use. Original-benchmark regression reproduced the baseline F1 94.6%, and measured candidate F1 92.5%, reinforcing the decision to retain the baseline.

Artifacts: `training.json`, `training-regression.json`, `training-memory.json`; best local candidate checkpoints are under the experiment path recorded in `training.json`. Model-release tooling stages separate vectors and preserves baseline rollback vectors, requires approval/backfill before activation, changes active revision/vectors atomically and preserves reviewed evidence. No candidate was activated.

## Verification and operational limits

- 39 backend tests pass: registration replay/rollback, bureau isolation, mutable permission changes for imports/summaries/exports, file validation, cache/throttle separation, durable import checkpoints, summary-date handling, optimistic conflicts, matching/review preservation, and model activation/rollback gates.
- Six Edge browser tests pass against bundled assets: original case workflow, coordination, bureau restrictions, mobile containment, spreadsheet preview/import/report/export and snapshot selection. External browser requests are blocked. Container inference has `HF_HUB_OFFLINE=1` and reads local weights; the laptop's network adapter was not physically disabled.
- TypeScript/Vite production build, Django system checks, Python compilation and dependency consistency pass. Research parser/redaction and split-leakage self-checks pass.
- A real worker stop/start recovered two complaints confirmed while stopped; both imported and matched in 14.7 seconds after restart. Unit tests separately recover from a committed 250-row checkpoint without duplicating cases.
- Backup `backups/upgrade-20261030.dump` restored into a separate database. That snapshot contained 4,543 complaints, 13 imports and 1,002 summary rows. Subsequent explicitly labelled benchmark/browser records remain in the working database. Restore did not overwrite the working database.
- CSV/XLSX is limited to 10,000 rows and 20 MB per file, one sheet at a time. Summary report tables preview 100 rows; CSV includes all selected rows. Original complaint text is immutable, source conflicts require review, and a transferred case can make an officer's entire import unavailable.
- Graphify outputs are development aids. Source code and tests are authoritative; extracted/inferred relationships and graph health are reported separately.

Not checked: real AICTE accuracy, independently reviewed labels, official workflow compliance, full 100,000-row ingestion, a million-record server or public deployment. Synthetic data, cached coordinator responses and small local tests must not be presented as production guarantees.
