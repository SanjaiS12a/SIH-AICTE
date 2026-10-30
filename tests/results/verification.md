# Verification · AICTE 26264

Verified on 30 October 2026 on the user's Windows laptop, with Linux containers for Django, PostgreSQL/pgvector and the worker. The React interface runs locally through Vite.

## Passing checks

- **26 backend tests pass in the container**, including concurrent idempotent registration, bureau isolation across lists/details/exports/counts/files, rollback on history/queue failure, optimistic conflicts, coordinator-only mutations, token limits, CSRF, private file validation, reminder boundaries, and human review preservation.
- **4 Edge browser tests pass**: registration → actual asynchronous matching → note → transfer → history; dashboard drill-down and coordination review; officer access restrictions; mobile table containment, keyboard focus and sign-out.
- Browser acceptance tests abort external HTTP requests. Model inference and tokenizer validation read local weights/files only; the container sets `HF_HUB_OFFLINE=1`.
- Two controlled worker cycles processed real durable jobs submitted while the worker was stopped. See `queue-recovery.json`.
- `verified-demo.dump` restored successfully into the separate `coordination_restore_check` database: **513 complaints** at that backup snapshot. No working database was overwritten.
- TypeScript and Vite production build pass. Django system checks and dependency consistency checks pass. Initial migrations applied successfully, including the pgvector extension.

## Measured HTTP performance

Ten simultaneous authenticated sessions against the container API, with 500 original seed complaints plus explicitly marked verification records:

| Operation | Requests | p95 | Target |
|---|---:|---:|---:|
| Filtered case reads | 50 | 150 ms | <500 ms |
| Dashboard | 50 | 279 ms | <1,000 ms |
| Registration | 10 | 447 ms | <500 ms |

See `latency.json` for raw summary values. A per-user registration lock initially serialized unrelated requests; it was removed in favor of database uniqueness and replay handling, with a real concurrent-submission regression test. These are local measurements, not guarantees for other machines or deployments.

## Matching evaluation

Model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Exact, institution-scoped pgvector retrieval; frozen cosine threshold **0.603080153465271**, selected exclusively on calibration families.

| Method | Held-out precision | Held-out recall | F1 | Same-incident Recall@5 |
|---|---:|---:|---:|---:|
| TF-IDF baseline | 100% | 67.5% | 80.6% | 100% |
| MiniLM | 94.2% | 95.0% | 94.6% | 100% |

The corpus contains 400 authored synthetic descriptions, 300 labelled pairs, and 60 held-out retrieval queries. Both `same_incident` and `related_issue` count as review-worthy in binary precision/recall. Incident families do not cross calibration/test partitions. The reference corpus remains available for retrieval. Native cold model load measured about 7.1 seconds; batch encoding of the 400 evaluation records measured about 0.78 seconds. Runtime timings are recorded separately in `matching-runtime.json` and include worker cold starts and both native/container runs.

**Independent human label review is pending.** Templates repeat across families, and this small synthetic benchmark is easier than real grievance data. Its scores do not establish production accuracy. Complaint relationships remain human decisions; no automatic merging or closure is implemented.

## Artifacts and remaining limits

Desktop, coordination, case-detail and mobile screenshots are saved alongside this report. The original seed is 30 fictional institutions and 500 complaints. Tests and benchmarks deliberately retain their labelled synthetic cases, so the running database contains more than 500 records.

Graphify generated a source/document navigation map and health report. Unresolved external references, a self-loop and collapsed parallel relationships make it approximate; code and tests are authoritative. Semantic extraction token usage was unavailable from the host, and no estimated cost is claimed.

Public hosting, official AICTE/CPGRAMS integration, real-data validation, production security/compliance review, training, multilingual support, OCR and automatic merging remain outside this prototype. First preparation needs internet for packages/images/weights; the prepared demonstration uses local resources.
