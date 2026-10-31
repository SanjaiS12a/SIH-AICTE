# Phase 2 Task 3 — manual escalation verification

Verified 31 October 2026 on `feature/phase2-workflows`, starting from `8e32699` (accepted classification and next-action work). Pre-change source checkpoint: `checkpoint/pre-escalation-8e32699`. Main remains `5fba35f`; no merge or force push.

**Task 3 acceptance passes.** Task 4 manual relationships and Task 5 enhanced coordination notices are not implemented here. The original MiniLM remains active.

## Recovery completed before schema changes

- Fully restored the previous `backups/phase2-before-20261031.dump` into the separate database `coordination_task3_restore_20261031` with `pg_restore --exit-on-error`. Verified 7,741 cases, 8,037 case actions and 36,707 existing relationships; applied migration 0008 to that copy and checked registry/profile/paginated cases/history endpoints returned 200. Legacy cases remained Unclassified.
- Created **and fully restored** a new current-state archive, `backups/escalation-before-20261031.dump`, into `coordination_task3_current_restore_20261031`. Compared every row of seven core tables using sorted row checksums and counts against the working database, including existing classification and next-action values. All matched: 61 institutions, three Bureaus, five memberships, 7,806 cases, 8,113 actions, 36,959 relationship rows and 12,620 notifications.
- New archive SHA-256: `a281d0be98cc5762c8e4a5807920471a2f62642afa8630c11bc0b04b81fb6536`. Evidence: `tests/results/escalation-recovery-verification.json`. Both restores preceded generation/application of migration 0009. Restored copies were retained separately; the working database was not replaced or rolled back.
- These are database-only archives. Uploaded files, models and other filesystem assets are separate. Source rollback is not database rollback. Reversing 0009 would discard escalation history and cannot safely restore the old non-null notification-deadline schema while new event notifications exist. Use the verified pre-0009 archive with the matching source checkpoint, preserving subsequent work separately when recovering.

## Schema

`backend/cases/migrations/0009_manual_escalations.py` is additive apart from making the existing notification deadline nullable for a new event type:

- Escalation UUID, unique submission UUID, protected case/creator/resolver references, original reason, pending/resolved status, creation/resolution timestamps, resolution reason and optimistic version.
- PostgreSQL partial unique constraint: one pending escalation per case. Further checks require a reason and a consistent pending/resolved state. Queue index on status/creation timestamp.
- Nullable protected Notification→Escalation reference and unique recipient/escalation event key. Escalation notifications have null deadline; existing reminders retain their deadlines and uniqueness constraint. A check constraint distinguishes these two notification shapes.
- Existing case history, classifications, next actions, reviewed relationships and embedding configuration are not replaced. Escalations are read-only in Admin; workflow mutations go through audited endpoints.

## API contract

| Endpoint | Contract |
|---|---|
| `GET /api/escalations` | Coordinator/auditor queue; server pagination. `state=pending` default, `resolved` or `all`; existing case filters apply, including institution, Bureau, classification and case status. |
| `GET /api/cases/{id}/escalations` | Complete server-paginated authorized case history, default `state=all`. Current ownership/membership controls access. |
| `POST /api/cases/{id}/escalations` | `submission_id` UUID, `expected_version` of case, nonblank `reason` ≤4,000 characters. Active current-owning-Bureau officer or coordinator. Returns 201; identical actor/case/request/reason replay returns 200, including after resolution. Changed content, stale versions or another pending request return 409. Closed-case creation returns 400; unauthorized cases 404. |
| `POST /api/escalations/{id}/resolve` | Coordinator-only. Escalation `expected_version` and nonblank `reason` ≤4,000 characters. Returns 200; same resolver/reason retry against the immediately preceding version returns the saved result. Stale/different decisions return 409. Original request remains preserved. |
| Existing case/detail/list responses | Add `has_unresolved_escalation`; `escalated=true` reuses common scoped filtering, including reports/exports. |
| Existing institution profile | Adds all-time scoped `overview.unresolved_escalations`, including requests still outstanding on closed cases. |
| Existing notifications GET/POST | Existing reminder fields retained; new event metadata `created_at`, `escalation_id`, `escalation_status`, with null deadline for escalation events. Counts, display and mark-read revalidate recipient role and case scope. |

Creation and resolution lock the case first and escalation second where required, increment the case version, and append a CaseAction in the same transaction. They do not change ownership, status, disposal deadline, next action, assignment or model fields. Transfer/closure do not resolve an escalation. A new escalation can be submitted after manual resolution only if its case remains active and a new submission UUID is used.

## Notifications and retry semantics

Creation durably enqueues `cases.tasks.notify_escalation` in the existing PostgreSQL ORM broker, transactionally with the request/action. The worker notifies currently active coordinators. Delivery is transactional and uses the event/recipient unique key, so repeats cannot duplicate notifications. Partial failures roll back delivery, and a retry safely completes it. No encoder inference is involved.

Existing worker limits remain one worker, 120-second timeout, 300-second retry interval and three attempts. After exhausted retries, inspect the Django Q failed task in Admin, fix the cause and requeue the same `cases.tasks.notify_escalation` UUID event with `async_task` from `manage.py shell`; the README gives the exact call. There is no new worker-failure dashboard or retry endpoint. Eligibility is evaluated at delivery time, and notification APIs hide escalation metadata/counts from inactive or demoted coordinator recipients even if they still have case access. Resolved requests retain their original notification event; its displayed status reflects the current escalation state.

For that shell retry, first run `from django_q.tasks import async_task`, then `async_task('cases.tasks.notify_escalation', '<escalation UUID>')` using the existing request's UUID, not a new request.

## Frontend

- Authorized active case action **Escalate for supervisory review**, required reason, retry UUID and existing case-version conflict handling. Pending requests suppress duplicate escalation controls. Auditor forms remain absent.
- Unresolved indicators in case headers/tables and institution Overview, with a case-list drill-down independent of management date filters.
- Paginated case escalation history, including requests surviving transfer and closure.
- Primary **Escalations** navigation for coordinators/auditors, pending/resolved/all queue, case/institution search and links, and coordinator-only reasoned resolution. Officers are denied both the route's data and the backend queue.
- Real HTTP 409 resolution conflicts retain drafts and block stale resubmission until explicit reload/discard. Editing pauses polling; a saved escalation snapshot keeps the resolution draft separate from refreshed list data.
- Notifications reload on opening and link to the case history. New event timestamps are displayed separately from reminder deadlines. Loading/error/empty states and mobile table containment use existing components/styles; no theme redesign.

Selected evidence: `escalation-queue.png`, `escalation-case-mobile.png`, updated case-detail and institution-profile desktop/mobile screenshots. Unrelated regenerated images were restored to keep the diff focused.

## Verification

- **89 backend tests passed in 26.646 seconds**: all 75 prior tests plus 14 escalation tests. Coverage includes owning-Bureau/coordinator authorization, auditor restrictions, reason validation, database partial uniqueness, true concurrent creation/replay/resolution, idempotent audit/notification behavior, required resolution reason/version, transfer/closure independence, membership/ownership changes, notification role/count filtering, transactional rollback on audit or enqueue failure, interrupted delivery and retry, protected references, history pagination beyond 20 and updates with AI deliberately unavailable.
- **33 Edge/Playwright tests passed in 3.5 minutes** against the production bundle: all 28 prior tests plus five escalation scenarios. New scenarios exercise officer creation → actual worker notification → coordinator resolution, closed/transferred pending requests and institution drill-down, auditor restrictions, a real stale-resolution 409 with retained draft, denied officer queue/foreign-case access, malformed responses, and mobile containment. Initial browser checks found a genuine mobile grid-width defect and selectors assuming a single status message; the three-line containment fix and targeted selectors were verified in the final full run.
- **Production build passed** TypeScript and Vite; final Vite build 21.22 seconds. Django system check passed. `makemigrations --check --dry-run` found no missing migrations. No dependency changes.
- Original model verified by weights checksum: `/models/minilm`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, threshold `0.603080153465271`. No training, candidate activation or existing embedding backfill.
- Command logs: ignored `tests/results/logs/escalation-{backend,build,browser}.log`. Backend suite: `docker compose exec -T api python manage.py test cases --noinput`; frontend: `npm run build`, then `npx playwright test` from frontend. Browser tests block external origins and add explicitly synthetic local fixtures.
- Graphify refreshed to **810 nodes and 2,130 edges**, with zero missing/dangling endpoints and five self-loops. README evidence is distinguished from structural extraction; source/tests remain authoritative. Source/test/delivery checkpoint **`266bd67`** contains 28 changed/created files, 1,527 insertions and 66 deletions. Six generated source-map artifacts are recorded separately.

## Changed source files

Created: `backend/cases/escalations.py`, migration 0009, `frontend/src/escalations.tsx`, `tests/backend/test_escalations.py`, `tests/browser/escalations.spec.ts`, recovery evidence and this report.

Modified backend: `models.py`, `access.py`, `serializers.py`, `institutions.py`, `tasks.py`, `api.py`, `urls.py`, `admin.py`. Modified frontend: `api.ts`, `main.tsx`, `institutions.tsx`, `ui.tsx`, `style.css`. Existing institution backend assertion and Phase 2 browser status selector were extended for the additive profile field and additional loading region. README documents contracts, recovery and task retries. Graphify source/document outputs are refreshed separately.

## Limits

Task 3 is complete; manual relationships, enhanced coordination notices and further model experiments remain pending. Physical offline startup, production-scale/performance benchmarking and restoration of private filesystem assets were not verified in this increment. Bounded notification failures require operator review/requeue after retries are exhausted. Synthetic fixtures and passing tests do not validate official AICTE procedures or production deployment readiness.
