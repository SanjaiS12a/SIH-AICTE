# Movement CSV export follow-up — 2 November 2026

The previous verified implementation was published to main at `ff4025e388aea798c7e7a0cbdd635dfd0874e2b0` with the user's explicit approval. Earlier readiness reports describe their original verification/publication state; their real-data and physical-offline limitations remain unchanged.

## Correction

`movements_csv` constructed a DRF serializer and queried current membership for every exported action. A regression test reproduced growing query counts: 100 rows required 105 Django SQL executions, compared with seven for two rows.

The view now resolves its redaction context once for each authorized request and reuses that request's serializer through `to_representation`. It retains `action_query`, current membership/ownership scope, group-action exclusion, protected historical Bureau snapshots, CSV formula escaping, export audit logging and 1,000-row iterator chunks. It does not materialize the entire export on the server or cache permissions between requests.

No API contract, database migration, frontend asset or model changed. The affected callers are the Reports movement download, movement CSV reconciliation checks and history/relationship privacy tests.

## Measured result

The same complete 10,000-row registered-action export was consumed before and after the change in the isolated `coordination_scale_optimized_20261101_205207` database. The working demonstration database was not accessed. Measurements used one synthetic coordinator and Django's in-process API client, not an HTTP concurrency or p95 benchmark.

| Measure | Before | After |
|---|---:|---:|
| Exported rows | 10,000 | 10,000 |
| Django SQL executions | 10,005 | 6 |
| Complete CSV consumption | 17.500 s | 2.292 s |
| Bytes | 1,145,634 | 1,145,634 |

Both bodies have SHA-256 `e6d5df3571efdc12c49cdc66eaf328bb26b385e2fd37ef672afc6c1f5c54def8`. This is approximately 7.6 times faster in one before/after trial, with byte-for-byte identical output. The query counter wraps Django executions; cursor fetches still occur in bounded chunks. The benchmark consumer buffers the downloaded bytes solely for digest/row verification; the server remains streaming.

## Verification

- Three new focused tests pass, covering query-count growth, coordinator/auditor/officer redaction, membership changes, transfer visibility, historical Bureau attribution, multiline values, formula escaping and movement-list equivalence.
- The complete backend suite passes: **200 tests in 58.639 seconds**.
- The affected browser regression file passes: **four Edge tests in 12.3 seconds**, including real movement-list/CSV reconciliation and role workflows.
- Frontend source/assets are unchanged; a production rebuild was unnecessary for this backend-only change.

[Portable measurement summary](movement-export-summary.json). Raw baseline, failing regression, corrected regression and full verification logs are retained in the ignored `runs/movement-export-20261102-052735/` directory. The exact profiling script is retained there as `profile.py`; it asserts a `coordination_scale_*` database and never queries the working database.

Real-world matching acceptance, authorized education data, publisher access/permissions, independent human review and physically disconnected operation remain external gates. This patch does not establish production compliance, million-record capacity or real-world model accuracy.
