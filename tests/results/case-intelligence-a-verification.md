# Case Intelligence 2.0 — Milestone A verification

Date: 1 November 2026 (Asia/Calcutta). Scope: simpler official workspace only. Status: **Milestone A complete; feature branch verified, not merged or published**.

## Baseline and safety

- Verified local `main` and remote `main`: `da32e1ad2eefc98da3250d4ce79a88a29e9c313f`.
- Implementation branch: `codex/case-intelligence`.
- Recovery branch: `checkpoint/pre-case-intelligence-da32e1a` at the unchanged baseline.
- The previously untracked `docs/plans/case-intelligence-2.0.md` was preserved and is included as the design reference.
- Existing recovery branches, ignored datasets/models/private assets and Graphify artifacts were preserved. The previous graph was additionally copied into the ignored run directory before refresh.
- Verification uses `sih-readiness-115600`, API `8001`, bundled Vite preview `5174`, database `coordination_audit` and separate private storage. Django created/destroyed its own test database inside that stack. Browser fixture writes target only that isolated stack.
- No working-database mutations, migrations, backend source changes, new dependencies, model changes, main updates or publication were performed.

## Delivered interface and files

| File | Change |
| --- | --- |
| `frontend/src/main.tsx` | Five primary links, section-aware breadcrumbs/current navigation, contextual links for existing workflows, `/work` route, visible approaching-deadline filter, comparison metadata and links, neutral pending decisions and required selection/reason |
| `frontend/src/my-work.tsx` | Small role-aware hub using existing case filters and routes; no invented counts or personal-assignment claims |
| `frontend/src/style.css` | Responsive task cards, readable comparison text, wrapped long evidence, decision fieldset, labeled mobile navigation and visible contextual links |
| `tests/browser/case-intelligence.spec.ts` | Ten dedicated Milestone A regressions |
| `tests/browser/imports.spec.ts`, `starter.spec.ts` | Use the renamed Data Imports primary destination |
| `tests/browser/workflow.spec.ts` | Reach Case registry through My Work; existing assertions and workflow retained |
| `START-HERE.md`, `README.md`, `tests/README.md` | Explain the five sections, deliberate relationship review and verification evidence |
| `docs/plans/case-intelligence-2.0.md` | Retained staged implementation plan; later milestones remain proposed |
| `graphify-out/graph.json`, `graph.html`, `GRAPH_REPORT.md`, `GRAPH_HEALTH.json`, `GRAPH_HEALTH.txt` | Refreshed source/document map and diagnostics |
| `tests/results/case-intelligence-a/` | Selected before/after screenshots, separate from ignored logs/traces |

Primary destinations: **Home → Institutions → My Work → Data Imports → Reports**.

My Work contains current-scope case/deadline queues and role-authorized coordination tasks. Source intake and complete source-upload history remain under Data Imports. Detailed movements and cross-Bureau activity remain under Reports. All 23 existing route patterns are preserved; `/work` is the only new route. A source-level comparison against the baseline confirms this. Institution profiles remain all-time, independent of Home date filters.

The two comparison columns show canonical institution/Permanent ID, original case reference/summary/description, current Bureau, source system/reference, category, classification, receipt/incident dates and status. Each links to the original case, action history and authorized attachments. Missing metadata is labeled Not recorded. Metadata agreement/difference is descriptive, not a finding; cosine is not a confidence percentage.

## API compatibility

No new or changed API contract. The hub links to existing case/coordination filters. Comparison uses the existing scoped `/api/overlaps` response and `/api/overlaps/{id}/review` optimistic-version mutation. Evidence links reuse `/api/cases/{id}` and its existing authorized history/attachments. `/api/institutions` lookup and all pagination contracts remain intact.

No pending candidate has a preselected relationship. Required native radio validation and a nonblank-reason guard prevent accidental submissions. Existing decisions remain selected. A real stale review returns 409, retains both draft fields, disables submission and offers explicit reload/discard. The existing backend records the decision for both complaints without merging, transferring or closing them.

## Test results

| Check | Actual result |
| --- | --- |
| All discovered Django tests | **148 passed**, 57.836 seconds; expected injected model-unavailable exception exercised failure handling, not a test failure |
| TypeScript + production Vite build | **Passed** (`tsc -b && vite build`); 5,182 modules, 22.82-second Vite build; final entry assets `index-KBWr9F1y.js` and `index-D8pbJg4N.css` |
| Full Edge/Playwright suite against final assets | **63 passed**, 3.9 minutes; includes all ten new Milestone A tests and the existing 53 regressions |
| Dedicated Milestone A coverage | Ten tests included in the full suite |
| Working backend/model/schema changes | None (`git diff -- backend` empty) |

The first focused browser pass found an assertion expecting a nonexistent deadline checkbox. The registry now exposes the already-supported approaching filter. Visual inspection also identified the inherited mobile `nav a { font-size: 0 }` rule; explicit mobile labels/contextual-link font sizes and regression assertions address it. The final production build and complete 63-test suite include those final CSS changes. The earlier full pass also passed 63 tests (7.2 minutes); final sign-off uses the later complete run. No existing workflow assertions were removed or weakened.

### Requirement-to-test traceability

| Requirement | Evidence |
| --- | --- |
| Exactly five primary destinations, current section and role scope | Three role-specific cases in `case-intelligence.spec.ts` |
| Existing routes, source history, movements, manual relationships and Back | Contextual-navigation test; existing institution/source/movement/coordination suites |
| No default decision, explicit choice and nonblank reason | Pending-review test inspects zero checked radios, blocked submission and exact versioned request |
| Previously recorded decisions preserved | Existing reviewed-pair assertion and real concurrent review test |
| Two original complaints and missing/long metadata | Desktop/mobile comparison test, numeric cosine and metadata table assertions |
| 409 draft preservation | Real concurrent API mutation followed by stale browser submission and explicit reload |
| Officers cannot obtain restricted comparisons, auditors cannot mutate | Browser UI/direct URL checks plus real 403/404 API assertions; complete backend permission regressions |
| Keyboard and 390px layout | Enter/Space navigation and selection, anchor focus, Back, width containment and nonzero mobile text-size assertions |
| Loading, error and empty views | Delayed/503/empty synthetic responses; existing malformed-dashboard/report tests |
| Existing institutional/workflow/report/import behavior | Complete Django and browser regression suites, including >20 pagination, transfers, history, exports and provided 1,000-row workbook |

Presentation edge cases use clearly synthetic intercepted responses. They do not prove model accuracy. Real stale-review and authorization tests use the isolated Django endpoints. External-request blocking is an application request check, not physical offline certification.

## Reproduction and local evidence

Ignored run directory: `tests/results/runs/case-intelligence-a-20261101-182017/`.
Metadata: `tests/results/logs/case-intelligence-a-run.json`.
Final browser output: `browser-final-suite.log`; final build: `production-build-final.log`; traces/report: `final-suite/`; actual-stack captures: `final-captures/`. Earlier evidence remains preserved alongside these directories.

```powershell
$audit = Get-Content tests/results/logs/readiness-run.json | ConvertFrom-Json
$env:AUDIT_RESULTS = $audit.directory
docker compose -p $audit.project -f compose.audit.yaml exec -T api python manage.py test cases --noinput
$env:API_PROXY_TARGET = 'http://127.0.0.1:8001'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5174'
# Use a fresh ignored evidence directory for every run.
$env:AUDIT_ARTIFACT_DIR = Join-Path (Get-Location) ('tests/results/runs/milestone-a-' + (Get-Date -Format yyyyMMdd-HHmmss))
Push-Location frontend
npm run build
# The isolated Vite preview must already be serving dist on 5174.
npx playwright test
Pop-Location
```

### Selected screenshots

| Screen | Before | After |
| --- | --- | --- |
| Home, desktop | [Before](case-intelligence-a/before-home-desktop.png) | [After](case-intelligence-a/after-home-desktop.png) |
| Home, 390px | [Before](case-intelligence-a/before-home-mobile.png) | [After](case-intelligence-a/after-home-mobile.png) |
| Comparison, desktop | [Before](case-intelligence-a/before-review-desktop.png) | [After](case-intelligence-a/after-review-desktop.png) |
| Comparison, 390px | [Before](case-intelligence-a/before-review-mobile.png) | [After](case-intelligence-a/after-review-mobile.png) |
| New My Work | Not present at baseline | [Desktop](case-intelligence-a/after-work-desktop.png), [390px](case-intelligence-a/after-work-mobile.png) |

Screenshots show synthetic isolated-stack data at capture time; fixture counts can change during tests. They compare layout and navigation, not fixed analytics totals. Long-text stress captures and traces remain in ignored per-run evidence.

## Graphify, recovery and limitations

The source map retains directed relationships, source locations and extracted/inferred distinctions: **1,099 nodes, 3,038 edges, 86 communities**. Diagnostics show zero dangling endpoints, zero exact duplicate edges and zero unverified code nodes; 13 self-loops are retained. Code extraction uses no LLM calls; community fallback names are based on hubs. Nine unsupported CSS/batch/extensionless files remain outside symbol extraction; source and tests are authoritative. A final incremental refresh found no further topology changes.

Recovery: the pre-change branch above preserves the baseline. The commit containing this report on `codex/case-intelligence` is the verified feature checkpoint, also retained as `checkpoint/case-intelligence-a-verified`. Its exact hash is recorded in the final delivery message. The graph was generated from this feature working tree before committing; its commit label names the parent baseline. `main` remains unchanged. No force-push or merge was performed.

Milestones B/C/D were not started. No fine-tuning, lexical ranking, entity extraction, incident groups, MCP/UTCP or matching-threshold changes were introduced. Real AICTE workflow compliance, independent real-world matching accuracy and physically disconnected cold startup remain unverified. Performance was not rebenchmarked in this UI milestone.
