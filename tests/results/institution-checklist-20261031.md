# Institution frontend acceptance follow-up

Date: 31 October 2026. Branch: `feature/institution-module`.

The attachment's claim that the institution frontend was pending was outdated. The directory, forms, profile sections and dedicated browser coverage were already delivered. This follow-up checked that implementation against the requested checklist and completed the missing district filter without rewriting working screens.

## Acceptance evidence

| Requirement | Implementation and verification |
|---|---|
| Navigation and directory | Institutions navigation; server-side pagination; Permanent-ID/name, region, district and bureau filters. Browser tests verify page reset and empty/error/loading states. |
| Registration and editing | Coordinator-only forms call existing audited APIs. Permanent ID remains read-only during editing. A real stale update returns HTTP 409, retains the draft and requires explicit reload. |
| Consolidated profile | Overview, Cases, History, Coordination and Reports reuse backend responses. All-time profile totals remain independent of management date filters. |
| Complete cases and history | Separate server-paginated case and authoritative CaseAction endpoints; browser fixtures exercise more than 20 records. No frontend history store added. |
| Role isolation | Auditor/officer writes rejected by the backend. Officers do not request restricted coordination data. Backend checks recalculate current membership and ownership without requiring another login. |
| Links and presentation | Institution links across existing case, dashboard, coordination and report views; keyboard, print and mobile checks pass. |
| District filtering | Case-insensitive partial search includes canonical institutions without cases. Scoped case totals, dashboard and CSV use the same validated filter. Invalid overlong values return HTTP 400. |

## Files changed in this follow-up

- `backend/cases/serializers.py`: optional validated `district` query parameter, maximum 80 characters.
- `backend/cases/access.py`: reuse shared institution district filtering for scoped cases, dashboard and exports.
- `backend/cases/institutions.py`: directory district filtering independent of whether an institution has cases.
- `frontend/src/institutions.tsx`: labelled District control using existing URL state and server pagination.
- `tests/backend/test_institutions.py`: two new regression tests for district filtering, legacy lookup compatibility, scoped totals/exports and changed membership.
- `tests/browser/institutions.spec.ts`: tenth institution scenario, covering server response, no-case institutions, page reset, clearing filters and mobile containment.
- `README.md`: document district behavior and unchanged lookup contract.
- `tests/results/institution-directory.png`: updated directory screenshot. Other regenerated screenshots were restored to keep this change focused.
- This report and refreshed Graphify source/document artifacts.

## API compatibility

Existing integrations remain `GET/POST /api/institution-registry`, `GET/PATCH /api/institutions/{id}`, paginated `/cases` and `/history` beneath the institution, institution-filtered `/api/dashboard` and `/api/overlaps`, and existing export endpoints. Only the optional district filter was added. The original `GET /api/institutions` lookup remains an array with its existing fields. No schema migrations, dependencies, role grants or Phase 2 operations were added.

## Verification

- Django regression suite: **62 passed in 17.196 seconds** (`docker compose exec -T api python manage.py test cases --noinput`). The model-unavailable traceback is an expected mocked failure scenario.
- Production build: TypeScript and Vite passed (`npm run build`), Vite build **40.33 seconds**.
- Production-bundle Edge/Playwright suite: **24 passed in 3.1 minutes**, comprising 14 existing regressions and 10 institution scenarios. Includes registration, transfers, audit history, report-source regressions, role restrictions, pagination, concurrency, keyboard, print and mobile behavior.
- Django system check passed; `makemigrations --check --dry-run` found no changes.
- Runtime model remains `/models/minilm`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, threshold `0.603080153465271`. Active weights match the saved baseline checksum. No experimental embeddings were activated or backfilled.
- Reproducible command logs are under ignored `tests/results/logs/institution-checklist-{backend,build,browser}.log`.

Phase 1 institution frontend acceptance passes. Phase 2 remains pending. Historical verification reports describe their original checkpoints and are not rewritten.

## Recovery and limits

Pre-change recovery branch: `checkpoint/institution-checklist-36268db` at `36268db`. Work stays on the feature branch; `main` remains at `5fba35f`. Existing backend and historical complaint/review records are preserved. Browser tests add explicitly synthetic fixtures to the local demo database.

The separately packaged PAWS candidate remains research-only, with no claim of real AICTE complaint accuracy. Training, Phase 2 workflows and a physically disconnected full-system rehearsal were outside this follow-up. Browser external-origin blocking and the earlier isolated offline model-load check do not establish full offline readiness. See the existing research and recovery reports for those limitations.
