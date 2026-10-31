# Phase 2 Tasks 1–2: classification and next actions

Verified 31 October 2026 on `feature/phase2-workflows`, created from accepted Phase 1 commit `0e43f7e`. Recovery branch `checkpoint/phase1-0e43f7e` retains that source checkpoint. Main remains `5fba35f`; no merge or force push.

## Delivered behavior

- Classification: Grievance (`grievance`), Regulatory / Compliance (`regulatory_compliance`), Unclassified (`unclassified`). Manual registration requires a deliberate selection, including an explicit Unclassified choice. API/import omission defaults to Unclassified. Bureau ownership never determines classification.
- Coordinator classification corrections require a nonblank reason, the expected case version and an authoritative CaseAction containing before/after classification values. Officers and auditors cannot correct classification. Original allegation text, category, matching state and embedding configuration are not rewritten.
- Coordinators and currently authorized owning-bureau officers can set or clear a next-action description and optional calendar date through the existing action endpoint. A date requires a description; description limit is 1,000 characters. Omitting/nulling the date clears it. Clear both fields to remove the operational next action. Auditors remain read-only.
- Both updates hold the case row lock, check the expected version, increment it and append history atomically. Current membership/ownership is revalidated on each request. A real HTTP 409 retains the browser draft, blocks stale resubmission and offers an explicit reload/discard operation. Matching polling pauses while editing; a draft's version is captured before changes and is not silently refreshed underneath it.
- Closing clears next-action fields and includes previous values in the same closure CaseAction. Closed cases reject next-action updates. Reopening does not restore previous next actions; the officer records new work explicitly. Transfer preserves classification and pending next action. None of these operations changes or automatically triggers deadlines, escalation, relationships or reminders.
- Registration, case detail/action form, case-table classification labels, institution Cases filter and Overview classification totals are integrated. Overview counts include all-time authorized cases, independently of dashboard date filters. Dashboard More filters and existing factual reports/drill-downs/exports share the classification filter. Monthly/snapshot aggregate datasets remain separate and do not acquire inferred case classifications.

## Migration and preservation

`backend/cases/migrations/0008_case_classification_next_action.py` adds `classification`, `next_action`, `next_action_date`, a classification index and database constraints for valid classifications, date-requires-description and no operational next action on closed cases. Existing rows receive Unclassified, empty description and null date. No history, category or relationship table is replaced.

Measured immediately before and after applying migration, before new browser fixtures:

| Record | Before | After |
|---|---:|---:|
| Cases | 7,741 | 7,741 |
| Case actions | 8,037 | 8,037 |
| Existing overlap/relationship rows | 36,707 | 36,707 |
| Embedded cases | 7,741 | 7,741 |

All 7,741 legacy cases were confirmed Unclassified with empty next actions. Existing embedding revisions remained `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. See `phase2-migration-preservation.json`. Tests independently migrate a historical closed case and its history through the new migration and verify preservation. The institution migration test now restores the current migration leaf rather than leaving the test database at 0007.

Pre-migration local backup: ignored `backups/phase2-before-20261031.dump`, SHA-256 `7a58c46d4a7130f113a2a8c042bf0572e59f089f3c6c8dccbac2d8a3a4aa196c`. This new archive was created successfully but not separately restored during this increment. A source checkpoint is not a database rollback: reversing 0008 drops the new operational values, and old closure code does not satisfy the new closure constraint when a next action is present. Use the backup/recovery procedure when rolling back, preserving subsequent work separately. Previous Phase 1 restore evidence remains in its existing report.

## API additions and compatibility

| Interface | Additive contract |
|---|---|
| `POST /api/cases` | Optional `classification`, default Unclassified; returned case includes all three new fields. Manual React form requires a selection. |
| `POST /api/cases/{id}/actions` | `kind=classification` plus `classification`, or `kind=next_action` plus description and optional `next_action_date`; both require `reason` and `expected_version`. Existing 400/403/404/409 conventions remain. |
| Case detail/list and institution cases | Include `classification`, `next_action` and `next_action_date`. Shared `classification` query filter validates the three values. |
| `GET /api/institutions/{id}` | Adds all-time scoped `classifications: [{classification, count}, ...]`, including zero counts. |
| Dashboard, complaint import report, reports/CSV and async exports | Reuse the shared classification scope/filter. CSV appends Classification, Next action, Expected action date after the eight existing columns. |
| Complaint import template/preview | Optional classification column; invalid values rejected. Omission/blank defaults to Unclassified. Legacy import/submission fingerprints remain compatible; changed source content remains a conflict. |

Original `GET /api/institutions` lookup array is unchanged. Existing status values, including `disposed` (UI Closed), session authentication, CSRF, immutable allegation text and reviewed relationships are retained. Registration still queues matching durably; the new workflow updates do not invoke the encoder or require its queue.

## Changed files

Backend: `cases/models.py`, migration 0008, `serializers.py`, `api.py`, `access.py`, `institutions.py`, `imports.py`, `exports.py`. No dependency changes.

Frontend: `src/api.ts` types/labels; `main.tsx` registration, action form, next-action display and stale-draft handling; `institutions.tsx` scoped classifications/filter/response validation; `dashboard.tsx` classification filter; `ui.tsx` shared table labels. Existing styles/components reused; no CSS redesign or new frontend dependencies.

Tests: new `tests/backend/test_phase2.py` and `tests/browser/phase2.spec.ts`; existing `test_imports.py`, `test_institutions.py` and browser `workflow.spec.ts` extended. README documents contract, migration/startup and behavior. This report, migration evidence JSON, refreshed Graphify artifacts and selected case/institution screenshots are retained under the existing centralized result layout.

## Verification

- **75 backend tests passed in 12.875 seconds**, including all prior workflow/import/institution regressions and 13 additional tests. Tests cover legacy backfill/default/idempotency, import omission and validation, classification reason/audit/permissions, current membership changes, next-action validation/version conflicts, closure preservation/reopening, scoped counts/filters/CSV, direct database constraints, transfer independence, and updates with AI/queue deliberately unavailable.
- **28 Edge/Playwright tests passed in 58.6 seconds** against the production bundle: all 24 previous scenarios plus four Phase 2 scenarios. Checks include required manual classification, correction/closure/history/report journey, a real concurrent 409 with draft recovery, officer/auditor UI and backend restrictions, old transfers/reviews, institution pagination beyond 20 and mobile containment. Initial new-test selector errors were corrected to role-based combobox selectors; the final full run passed without changing the application to accommodate those errors.
- **TypeScript/Vite production build passed**, final Vite build 6.48 seconds. Django system check passed; `makemigrations --check --dry-run` found no pending changes.
- **Production model verified unchanged** by weights checksum against the saved baseline; path `/models/minilm`, revision above, threshold `0.603080153465271`. No new training, candidate activation, existing-vector backfill or matching configuration changes.
- Commands: `docker compose exec -T api python manage.py test cases --noinput`; `python manage.py check` and `makemigrations --check --dry-run` inside the API container; `npm run build` and `npx playwright test` from frontend. Detailed logs are ignored under `tests/results/logs/phase2-{backend,build,browser}.log`.
- Graphify refreshed to **745 nodes / 1,915 edges**, with zero missing/dangling endpoints and four self-loops. README evidence is distinguished from structural extraction; source and tests remain authoritative. Code/test/delivery checkpoint: `1f9e5d7` (25 files, 926 insertions and 31 deletions); six generated source-map artifacts are recorded separately.

## Limits and remaining work

This completes only Phase 2 Tasks 1–2. Escalations, manual relationship creation and enhanced cross-bureau notices are not added here. Full physical offline startup, production-load benchmarks, new backup restoration and real AICTE workflow compliance were not revalidated. Browser runs block external origins and add explicitly synthetic local fixtures; they do not establish production readiness. Model experiments remain paused.
