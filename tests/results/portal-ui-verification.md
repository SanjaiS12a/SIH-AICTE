# Portal UI — 2 November 2026

Baseline: `1034997b85c71b19bfda45d78ab539dd7acbdbbc`. Feature branch: `codex/portal-ui`.

## Delivered interface

- Compact AICTE identity and prototype label; green workspace navigation with a clear orange active state.
- Institution search and Bureau/receipt-date filters in one workspace panel. Search supports keyboard submission to the existing paginated registry.
- Four authoritative management totals with plain explanations. Under-process remains included in Open; overdue links retain receipt filters.
- Existing priority-institution and urgent-case lists, with clearer headings, readable table spacing and overdue badges.
- Coordination links on their own action row, separate from the all-time scope label and cross-bureau institution previews.
- Consistent orange/green chart colors, with the existing accessible values and filtered drill-downs preserved.
- Shared panels, institution tabs and work queues retain existing workflows. Phone/tablet navigation moves above content, with all five destinations labelled and sign-out accessible.

No backend, schema, permission, API, model, dependency or training change. `portal.css` is a final shared presentation layer over the existing theme; page components and their scoped API requests remain authoritative. The officer home keeps its two totals and category chart. Auditor controls remain read-only.

## Verification

Verified source checkpoint: `60b13d54727aae93da4a26de49ff741cb20c1397`.

| Check | Result |
|---|---|
| Production TypeScript/Vite build | Passed; final Vite build 9.63 seconds |
| Complete Playwright/Edge suite against bundled assets | **77 passed**, 3.8 minutes as reported by Playwright |
| New UI checks repeated with both experimental flags disabled | **4 passed**, 10.1 seconds |
| Initial focused dashboard/readiness/UI run | 18 passed, 40.5 seconds |
| Visual inspection | Desktop 1440px, phone 390px; directory and institution profile inspected |
| Tablet navigation | 820px; all destinations and sign-out visible, no document overflow |
| Phone containment | Dashboard and profile document width 390px at a 390px viewport |
| Graphify refresh | 1,423 nodes / 3,561 directed edges; no dangling endpoints |

Four new browser tests cover keyboard institution search, profile navigation, management scope labels, mobile/tablet layout, phone filters, primary navigation, sign-out and role presentation. The full suite also verifies registration, transfer, independent complaint histories, relationship reviews, stale updates, paginated institutions/cases/timelines, import/report/export reconciliation, malformed responses and Bureau isolation. No existing test was weakened. The backend suite was not rerun for this frontend-only change; the prior 200-test result remains historical evidence.

All browser runs use `127.0.0.1:5174` with the isolated audit API/database. The working demo database is not used. Full-suite experimental facts/groups are enabled only for their existing regression tests and restored to the default disabled state afterwards. Synthetic fixtures are recorded only in the isolated database.

Raw build logs, browser reports, traces and screenshots are retained in the ignored `tests/results/runs/portal-ui-20261102-060614/` directory. Screenshots show synthetic audit data; they are not real AICTE workload statistics.

Selected default-mode screenshots: [desktop](portal-ui-desktop.png), [phone](portal-ui-mobile.png).

## Source changes and integration

- `frontend/src/main.tsx`: shared stylesheet, workspace identity and accessible mobile sign-out.
- `frontend/src/dashboard.tsx`: grouped institution search/filter panel, coordination action row and consistent chart colors.
- `frontend/src/management.tsx`: authoritative totals with plain explanations and receipt/all-time scope distinction.
- `frontend/src/portal.css`: shared government palette, navigation, dashboard, responsive and print presentation; reuses existing classes/components.
- `tests/browser/portal-ui.spec.ts`: four dedicated browser regressions.
- `README.md`, this report and the five portable `graphify-out` artifacts: verification and handoff evidence.

Existing `/api/dashboard`, `/api/institution-registry`, institution profiles, filtered case/coordination lists and `/accounts/logout/` remain the integration points. Their contracts and backend authorization are unchanged. Profile totals remain all-time and independent of Home receipt filters. Graphify's detector omits CSS, so its report explicitly records supplemental stylesheet mapping and digest checking rather than claiming automatic CSS extraction.

## Limits

This is a presentation and browser-workflow verification, not a new backend benchmark, comprehensive accessibility certification or physically disconnected test. Existing real-data accuracy, permissions and physical-offline gates remain open. No claim of official AICTE branding approval or production compliance is made.
