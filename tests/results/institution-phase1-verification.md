# Institution registry and consolidated profiles — Phase 1 backend

Date: 30 October 2026. Baseline: `5fba35f`. Delivery branch: `feature/institution-module`; main remains unchanged. No React institution screens or Phase 2 workflows are included.

## Delivered

- Optional official contacts and version fields; existing identities and complaint records preserved.
- PostgreSQL trigger rejects permanent-ID updates, including direct SQL. API validation and Admin read-only identity provide usable errors before the database guard.
- Coordinator registration/editing with required reason, transactional before/after AuditEvent and optimistic version checks. Stale API edits return 409; stale Admin forms show a validation error.
- Paginated institution registry, identity search, scoped case filters, consolidated detail, complete paginated case list and reverse-chronological CaseAction timeline.
- Existing lookup array contract preserved. Profile totals are all-time and explicitly labelled independently of dashboard dates.
- Officer aggregates, bureau breakdowns, case pages and timelines use current membership and current ownership before querying/counting. Canonical institution metadata is shared; institutions with no authorized cases expose zero case totals.
- Coordinator/auditor consolidated views, auditor read-only access, no-role denial and session CSRF enforcement.
- Restricted relationship reasons and identifiers redacted in both officer history paths.
- Append-only CaseAction/AuditEvent database guards; parent-case protection retained. The seed command inserts original synthetic action timestamps rather than modifying history afterwards.

## Acceptance evidence

All twelve Phase 1 **backend** checks pass in the test suite: migration preservation; ID protection through SQL/API/Admin; coordinator creation/editing; edit audit; stale conflicts; registry search/pagination; more than twenty cases; complete action pagination; officer isolation; consolidated coordinator access; auditor restrictions; and lookup/workflow compatibility.

`docker compose exec -T api python manage.py test cases --noinput` passes **60 tests** in 19.983 seconds, comprising the existing 42 tests and 18 institution tests. Coverage includes audit-write failure rollback, unknown fields, malformed contacts, uniqueness, missing edit reasons/versions, direct SQL identity protection, append-only update/delete rejection, protected parent cases, 25-case pagination, 27-action pagination, fresh membership despite a cached Django relation, ownership changes without relogin, review redaction, CSRF, Admin edits, seed repeatability and forward/reverse migration preservation in a separate test database.

Django system checks and migration drift checks pass. The expected mocked model-unavailable traceback in the regression suite tests visible matching failure; the suite passes.

All **14 Edge browser regressions pass** against the bundled frontend in one final run (1.9 minutes), including reporting crash regressions, imports/exports, snapshot handling, transfer/audit history, coordination, role restrictions, mobile layout and keyboard access. Earlier attempts recorded a timeout during server restart and a Windows screenshot-file open error; the final full run passed without application or test changes. Generated screenshots were restored to the existing release artifacts because this milestone makes no UI changes.

## Local migration and smoke checks

Migrations 0005–0007 were applied to the demo database, then API/worker restarted. Before migration it contained 30 institutions, 7,553 synthetic/test cases and 7,821 actions. Browser regressions subsequently add explicitly synthetic records; these counts are not a clean 500-case benchmark.

An ignored pre-migration backup is retained at `backups/institution-phase1-before-20261030.dump`, with SHA-256 `2c8d86e49913f3224425202716b4bf537e69edb7b4424107005bc9fc24bd8e4c`; its archive table of contents was verified. The live database was not replaced or reset. Migration preservation and reversal were exercised in the test database; this backup was not restored during Phase 1.

A live-backend request smoke check sampled an institution with 1,277 cases visible to coordinator/auditor and 382 cases visible to its Regulation Bureau officer. Profile, cases and history endpoints returned 200 for each role. These single-request checks are not load benchmarks or p95 promises.

## Source map and limits

Graphify source and README map refreshed: 613 nodes, 1,569 edges, zero missing/dangling endpoints. Three self-loops remain in the source graph. Source code and tests remain authoritative; semantic usage is unavailable, not claimed as zero. Data, model weights, private files, secrets and backups remain excluded.

Skipped: institution React screens, Phase 2 workflows, new model training, new scale benchmarks and physical network-disconnection testing. Existing browser tests block external requests; this does not establish a fresh physical-offline test. Database owners can disable triggers, and official AICTE workflow compliance remains unvalidated.
