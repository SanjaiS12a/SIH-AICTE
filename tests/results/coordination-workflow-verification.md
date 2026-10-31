# Accountable coordination — verification

Verified 31 October 2026 on the local Windows laptop, PostgreSQL 17/pgvector and Docker API/worker, with the production Vite bundle served at localhost:5173. This is the focused first corrective milestone requested in the two realignment attachments, not final acceptance of every proposed milestone.

| Check | Actual result |
|---|---|
| Django complete regression suite | **108 passed**, 42.731 seconds |
| Edge/Playwright complete suite | **41 passed**, 3.7 minutes |
| Production build | **Passed**, TypeScript plus Vite; final build 6.53 seconds |
| Migration drift | **No changes detected** |
| Working database | Additive migration 0011 applied successfully after a new ignored backup |
| Source recovery | `checkpoint/pre-accountable-coordination-2af2ddf` retains the pre-correction commit |

Commands: `docker compose exec -T api python manage.py test cases --noinput`; `docker compose exec -T api python manage.py makemigrations --check --dry-run`; from `frontend`, `npm run build` and `npx playwright test`. Detailed logs are local ignored files in `tests/results/logs/coordination-*`; test sources and selected screenshots are versioned. Browser tests exercise bundled assets, not the development source transformer.

## New coverage

Seven backend tests cover the model-unavailable complete journey, atomic two-case history, independent case ownership/status, duplicate submission replay, conflicting payload reuse, stale versions, failed-audit rollback, current-membership revocation, restricted officer histories/inboxes, read-only auditors, invalid assignments, paginated records beyond 20, single-case shared work, coordinator revision/reassignment and fresh acknowledgment. A real two-thread/two-connection race returns one 200 and one 409 with one acknowledgment and exactly two linked case actions.

Four browser tests exercise institution → workspace → case selection across server pages → agreed lead/tasks → separate officer acknowledgment/completion → coordinator outcome; complete action history beyond the first 20; auditor read-only presentation; 390px mobile containment; stale-edit draft retention; officer denial at direct record URLs; malformed responses and empty workspaces. The existing 37 browser tests also passed, covering earlier institution, import/report, dashboard, manual review, escalation and case workflows. The reassignment UI is built and its endpoint is regression-tested; there is no separate browser test solely for the reassignment form.

The working database retains clearly synthetic browser fixtures and action histories, as earlier suites do. These tests do not use genuine AICTE complaints or establish official workflow approval.

## Files and interfaces

- Backend: `models.py`, additive migration 0011, new `coordination_workflow.py`, routes in `urls.py`, restricted action serialization, dashboard invalidation and the coordination movement-event filter.
- Frontend: new `coordination-workflow.tsx` for management list/create/detail/history and officer instruction inbox; routes/navigation in `main.tsx`; institution-profile and current-activity links in `institutions.tsx` / `management.tsx`.
- Tests: `tests/backend/test_coordination_workflow.py`, `tests/browser/coordination-workflow.spec.ts`.
- Documentation: README current milestone, `coordination-realignment-audit.md`, this verification and refreshed Graphify source/document artifacts.
- Integrated API routes: `/api/coordination-records`, `/{id}`, `/{id}/history`, `/{id}/actions`, `/api/coordination-requests`; reuse `/api/options` and `/api/institutions/{id}/cases`. Existing lookup contract remains unchanged.

Selected evidence: `accountable-coordination.png` and `accountable-coordination-mobile.png`. No additional dependencies, model training, embedding backfill, complaint merge or automatic case disposition was introduced.

## Remaining limits

The proposed demonstration workflow is not validated against actual AICTE approval/authority rules. Instructions are deliberately shared with their addressed officer; private reasons and other-case evidence remain management-only. Coordination records have immutable institution/case links after creation, support up to 50 linked cases, and have two explicit states. Case and institution histories still paginate independently without truncation. Revision and closure preserve prior actions; closed coordination cannot be reopened in this milestone.

The new backup has not undergone a separate full restore. Earlier baseline restore checks succeeded, but the composite asset/isolated-network rehearsal failed at Docker Desktop host access despite an internally healthy API (`completion-delivery.json`). Physical internet disconnection is unverified. Previously measured performance results remain separate historical evidence; no new speed promise, million-record claim, scale optimization or model-quality claim is made by this correction. Multi-source synchronization demonstration and later monitoring redesign remain next milestones.

The user subsequently authorized publishing the verified work to `main`, superseding the earlier keep-main-unchanged instruction. Publication must preserve recovery branches and use an ordinary non-force push, with local/remote commit comparison.
