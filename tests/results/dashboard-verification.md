# Working-dashboard release verification — 30 October 2026

The general Reports crash is fixed and the home page now prioritizes case actions rather than technical metrics. This release keeps React, Django, PostgreSQL and local charts, and does not change the active matching model.

## Root cause and fix

The reported bundle function `um` was `Report()`. Without `import_id`, it requested `/api/session` as an import `Job`, then called `job.state.replaceAll()` on a session response. This was a response-contract error, not missing browser support for replaceAll.

`usePoll` now accepts a disabled null URL, cancels old requests and keys results to their request URL and refresh version. Reports request import metadata only for an actual import. Runtime checks cover job, report and export response fields; malformed responses show an alert without rendering invalid data. The other replaceAll callers were checked; uncertain status/action/notification labels have explicit fallbacks. The unused export-session request was also removed.

## Action-first home

- Three clear figures: Open complaints, Overdue complaints (a subset of open), and possible-overlap pairs awaiting human review. Officers never see cross-bureau suggestion counts, text or navigation.
- Eight active cases sorted by deadline and ID, with institution, full responsible bureau name, deadline and an Open case link. Closed cases leave the attention list.
- A coordination section shows institutions with active cases across bureaus. Institution and case filters remain applied in overlap review and when switching review tabs. Auditors can inspect but cannot mutate.
- Two non-animated supporting charts: monthly receipts/closures and open workload. Officers see their category workload instead of a single-bureau chart. Values are visible and have equivalent keyboard-accessible links/tables.
- Bureau/date filters remain visible; category/region are under More filters. Monthly links intersect existing receipt/disposal date limits, so drill-down counts agree with chart values. Zero monthly values are not links to impossible date intersections.
- Detailed ageing, matching coverage and data-quality diagnostics remain in Reports. Database status `disposed` remains unchanged; explanatory UI labels use Closed.

The API adds `attention` and `active_categories` to `/api/dashboard`. `/api/overlaps` now reuses the shared case filter/scope definitions. Existing registration, assignment, transfer, status, deadline, evidence, review and audit operations remain in use. No schema migration or automatic merging was added.

## Passing checks

- **42 backend tests pass** in the application container, including attention ordering/scope, transfer/closure invalidation, filtered overlap review, both case histories, auditor restrictions and the previous import, authorization, concurrency and file checks.
- **14 Edge browser tests pass** against production bundles in one complete run. They cover general Reports, cancellation/source changes, malformed data, filter-aware drilldowns, institution-tab preservation, bureau restrictions, auditor read-only access, mobile containment/focus, registration/transfer/audit, human review, imports, snapshots and exports. Browser requests to external origins are blocked.
- TypeScript/Vite build passes. Django checks and migration-drift checks pass. Python compilation passes.
- Mobile overflow was fixed at its causes: wrapping header actions, genuinely hiding closed filter panels, containing report tables, and positioning the table scroll wrapper so its hidden accessibility label cannot escape to the viewport.
- Graphify source/document outputs are refreshed; extracted facts and inferred implementation bridges remain distinguished. Source code/tests are authoritative.

Screenshots: `dashboard-simple.png`, `dashboard-simple-mobile.png`, `case-detail.png`, `coordination.png`, `import-report.png` and `summary-report.png`.

## Publication and limits

The initial main-branch release includes application source, migrations, dependency locks, reproducible startup/research scripts and selected verification artifacts. Credentials, private uploads/exports, database dumps, model weights, downloaded research/benchmark data, dependency directories, logs and rotating graph backups are excluded.

The goal remains a working centralized complaint/cooperation portal. Similarity suggests review; an official records the decision, and independent case histories remain intact. The 30-day deadline is demonstration policy. This release does not establish real AICTE accuracy, official workflow compliance or million-record production capacity. No new fine-tuning or Power BI cloud integration was performed. Refer to `upgrade-verification.md` for earlier measured performance and rejected training experiments.
