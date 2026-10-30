# AICTE 26264 — Phase 1 institution frontend

Date: 30 October 2026. Branch: `feature/institution-module`.

Recovery checkpoints: original application `5fba35f`; verified institution backend `dfa6e5d`, retained as local branch `checkpoint/institution-backend-dfa6e5d`. No backend source, migration, API contract, dependency or database schema changes are included in this frontend delivery. Main is not merged or updated.

## Screens and behavior

- Primary **Institutions** navigation and breadcrumbs.
- `/institutions`: server-paginated directory, name/Permanent-ID search, region/bureau filters, accessible table and empty/error/loading states.
- `/institutions/new`: coordinator registration with optional contacts and required audit reason.
- `/institutions/{id}/edit`: coordinator editing, read-only Permanent ID and loaded-version submission. A real HTTP 409 preserves the draft, disables another stale save and offers an explicit reload that discards unsaved entries.
- `/institutions/{id}`: all-time Overview, paginated Cases, paginated authoritative CaseAction History, Coordination and Reports sections. Management date filters are not sent to profile overview or inherited into its case/history requests.
- Overview shows real scoped totals, identity/contacts and bureau counts, with case drill-downs. Cases supports search/status/category/bureau filters, server pagination and CSV export. History includes case references, actor, timestamps, reasons and authorized changes, without a second history store.
- Coordination uses existing current-owner notices and paginated suggestions/relationships. Officers do not request restricted coordination endpoints. Coordinators/auditors reuse the existing queue for review/inspection; no new decision workflow is added.
- Reports reuse existing scoped statistics, asynchronous CSV export and print/PDF layout. Profile controls and section navigation are hidden in print media.
- Canonical institution names link to profiles from case tables/details, dashboard attention/notices, coordination and imported summary reports. The case-detail institution preview links to the complete paginated list.
- Orange/white/green styling and existing controls are retained, with responsive tables, keyboard-operable links and loading, empty and error states.

## Existing API integrations

| Endpoint | Frontend use |
|---|---|
| `GET /api/institution-registry` | Search, filters and server-side directory pagination |
| `POST /api/institution-registry` | Coordinator institution registration |
| `GET /api/institutions/{id}` | All-time scoped profile and edit version |
| `PATCH /api/institutions/{id}` | Audited coordinator edits with expected_version/reason |
| `GET /api/institutions/{id}/cases` | Complete paginated case list and filters |
| `GET /api/institutions/{id}/history` | Complete paginated authorized action history |
| `GET /api/dashboard?institution={id}` | Scoped reporting and current cross-bureau notices |
| `GET /api/overlaps?institution={id}&decision=all&page=...` | Paginated suggestions and reviewed relationships |
| Existing `/api/exports` creation/status/download endpoints | Reused institution-scoped CSV exports |

The original `GET /api/institutions` array lookup is unchanged. Session authentication, CSRF, current membership/ownership scope, audit writes and concurrency remain backend responsibilities. Role-aware rendering never substitutes for server permission checks.

## Files

Created:

- `frontend/src/institutions.tsx`: directory, forms, profile sections and API integration.
- `frontend/src/ui.tsx`: existing heading, loading/error/empty states, badge, case table and pagination moved from main for reuse.
- `tests/browser/institutions.spec.ts`: nine real-backend browser acceptance scenarios, including two read-only roles.
- `tests/results/institution-frontend-verification.md`: this delivery record.
- `tests/results/institution-directory.png`, `tests/results/institution-profile.png`, `tests/results/institution-profile-mobile.png`: selected visual evidence.

Modified:

- `frontend/src/api.ts`: additive institution profile/history types and HTTP status-bearing errors.
- `frontend/src/main.tsx`: navigation/routes, shared controls, profile links and complete-history link. Pair selection buttons remain separate from institution links.
- `frontend/src/dashboard.tsx`: canonical profile links and reusable response validation.
- `frontend/src/imports.tsx`: embedded report heading and existing summary institution-ID links.
- `frontend/src/style.css`: responsive institution layouts using the existing palette.
- `README.md`: navigation, role behavior, edit conflicts and reproducible verification instructions.
- Graphify source/document map, manifest and health/report artifacts.

## Verification

- **Backend:** 60 tests passed in 18.100 seconds using `docker compose exec -T api python manage.py test cases --noinput`. This includes all existing institution, permission, CSRF, audit, migration, concurrency and complaint/import workflow checks. The intentionally mocked model failure in the suite is expected.
- **Production build:** `npm run build` passed TypeScript and Vite checks; final build 18.74 seconds. No dependencies added.
- **Browser:** all **23 Edge/Playwright tests passed in one full run (3.0 minutes)** against the production bundle: 14 existing regressions plus nine institution tests. This includes both read-only roles, server pagination beyond 20, real HTTP 409 recovery, print media and mobile layout after section data loads.
- **Source map:** Graphify refreshed to 643 nodes and 1,703 edges, with no missing/dangling endpoints. Three source-graph self-loops remain; source/tests are authoritative. Structural extraction uses no model tokens; host semantic usage is unavailable, not reported as zero.

Git diff from backend checkpoint `dfa6e5d`: 19 changed/created files comprising eight frontend source/test files, two documentation files, three screenshots and six graph artifacts. The frontend source/test commit is `f303605` (1,921 insertions, 181 deletions); much of the new UI helper file is existing controls moved out of main. Backend diff is empty. No generated bundles, dependencies, secrets, uploads, datasets or model weights are committed.

The new browser suite creates explicitly synthetic institutions and 25-case fixtures split across RB/PGRC. It checks directory pagination/search/filters; all-time totals despite a future dashboard date query; cases and actions beyond page one; empty states; registration/editing; a real concurrent API edit and HTTP 409 recovery; direct server rejection of auditor/officer writes; suppressed restricted officer requests; scoped notices/reports; malformed/error/loading states; institution links, keyboard navigation, mobile containment and print layout. Requests to external origins are blocked.

One exploratory run exposed an exact-label test selector issue, corrected to use the combobox's accessible role/name. Another run recorded a browser scheduling/visibility stall before an officer profile request; the response was correct. Acceptance tests explicitly foreground the browser page, consistent with the app's existing background-tab polling behavior. No backend permission or production timeout was relaxed.

## Limits

Phase 1 frontend acceptance is complete, with no known blocking issue from these checks. Repeated browser runs retain labelled synthetic institutions/cases; their global dashboard totals are not a clean seed benchmark. The earlier backend verification report records the backend-only milestone and its then-current UI limitation; this report covers its frontend completion.

Skipped: Phase 2 workflows, model fine-tuning, new scale benchmarks, public hosting and physical network-adapter disconnection. Official AICTE workflow compliance and real grievance accuracy remain unvalidated. Database-owner tampering remains outside the demonstrated audit guarantees.

Follow-up: `tests/results/recovery-offline-followup.md` records a successful full restore into a separate database, migrated/API-checked recovery, and a cold tokenizer/model check in a network-disabled container. Physical-disconnection rehearsal remains unverified.
