# Earlier completion measurements — retained evidence

These runs preceded the accountable coordination-record correction. They are historical measurements, not fresh benchmarks of migration 0011, and were not repeated after the user froze further scale work. All records are synthetic.

| Local HTTP, 10 independent authenticated sessions | Measured p95 | Target |
|---|---:|---:|
| Filtered reads, 50 requests | 231 ms | <500 ms, passed |
| Dashboard, 50 requests | 281 ms | <1,000 ms, passed |
| Case registration, 10 requests | 570 ms | <500 ms, **missed** |

The 1,000-row XLSX complaint import measured 4.29 seconds to preview, 9.38 seconds after confirmation to statistical reporting, and 34.77 seconds after confirmation to matching/final reporting. Importer plus nine reader sessions exercised ten concurrent users; the detailed JSON retains throughput, latency and stage boundaries. These results do not guarantee the same timing with arbitrary documents, long text or queue backlog.

Separate disposable-database scale runs used 1,000, 10,000 and 100,000 rows with ten thread-local PostgreSQL clients, distributed over 100 institutions or concentrated in one. They use in-process Django calls, synthetic histories, a small escalation queue, bounded relationship reviews and identical unit vectors; they do not measure 100k import, realistic embedding distributions, physical network concurrency or matching accuracy. The original `limits` string in the scale JSON incorrectly says no review traffic; the measured `review` endpoint entries show the bounded review requests. The command's description has been corrected without altering its recorded timings.

At 100k rows, dashboard p95 was 2.06s distributed / 2.52s concentrated, above the 1s laptop target. Notices measured 1.44s / 3.76s, while exact institution-filtered vector search measured 44ms / 509ms. The concentrated institution's profile and case-list p95 were 1.54s and 1.80s. These results do not demonstrate million-record readiness or justify switching to HNSW as the first fix. Some smaller runs also missed the dashboard target; all observations are retained in the JSON rather than selecting only the best values.

The first 100k attempt exhausted PostgreSQL's original 64MB shared memory allocation; `compose.yaml` now provides 256MB. Only the failed 100k stage was repeated, successfully. Both distributed and concentrated disposable databases were cleaned up; the working application database was not replaced. Source assets and active model weights were unchanged by these scale fixtures.

Resource samples in `completion-resources*.json` reflect a shared Windows laptop (i5-13450HX, 16GB RAM, RTX 3050 A 4GB). Sampling is periodic and includes other applications; it cannot establish an absolute process peak or exclusive GPU use. No additional fine-tuning was run.

`completion-delivery.json` records a separate attempted restore rehearsal at source `2af2ddf` / migration 0010: restored asset hashes, configuration and eight database-table counts/checksums passed. Host access to the healthy API on Docker's internal-only network failed, so the full browser/worker/no-egress rehearsal did **not** complete. Physical internet disconnection was not performed. The new migration-0011 backup is a further recovery checkpoint, not a claimed successful restore test. Backups, resolved credentials, datasets, private uploads and model binaries remain ignored.
