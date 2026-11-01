# SIH 26264 corrective readiness verification

**Date:** 1 November 2026. **Status:** application corrections and local verification completed. After disclosure of the remaining physical-offline limitation, the user explicitly authorized publication to `main`. Physical-network-disconnected cold startup remains unverified; publication does not change that result.

For a plain-language explanation and ready-to-upload data, open [START-HERE](../../START-HERE.md). This report records observed results, not production-compliance or real-data-accuracy guarantees.

## Source and preservation

- Confirmed starting local and remote `main`: `996b2ff7e094aa1e276e1738fcba141ba4a2faa7`.
- Corrective branch: `codex/sih26264-readiness`.
- Verified application checkpoint: `8347261`; tested demo/data/guide checkpoint: `285336e`. The final branch includes this report and the generated source map. Resolve its delivery SHA with `git rev-parse codex/sih26264-readiness`.
- Recovery branch: `checkpoint/pre-readiness-996b2ff`.
- Original untracked Graphify work was copied to ignored `backups/readiness-preflight-20261101-110720` before changes. Rotating graph backups remain local and ignored.
- No merge, force-push, model retraining, experimental activation or destructive database reset was performed.

The isolated stack is project `sih-readiness-115600`: API on 8001, frontend on 5174, database `coordination_audit`, separate database/private-storage volumes and read-only model assets. Django tests create their test database within this service. Browser tests default to the isolated port and reject working-demo ports 5173/8000. Output paths are unique per run unless explicitly supplied.

## Implemented corrections and traceability

| Requirement | Implementation | Verification |
|---|---|---|
| Malformed management objects and missing ageing must not blank the page | `frontend/src/dashboard-data.ts`, `dashboard.tsx`: typed counts, nested arrays and management structures; genuine zero remains valid | `readiness.spec.ts`: omitted management, missing ageing, null counts, malformed Bureau details and genuine empty cohort |
| Unexpected page-render failures preserve navigation | `page-boundary.tsx`, `main.tsx`: route-level boundary, retry and preserved navigation | Retry after corrected response and navigation recovery browser check |
| General reports must not parse session data as import metadata | Disabled `usePoll(null)`, validators, request cancellation and source-change cleanup | General/import/source-change/invalid-response browser regressions |
| Action-first management homepage | Institution search; Bureau/receipt filters; Received/Open/Under-process/Closed totals; five priority institutions; eight urgent cases; current coordination and acknowledgment links; two charts | Dashboard, completion and readiness browser checks; desktop/mobile screenshots |
| Detailed analytics remain available | Existing ManagementPanels reused in Reports; officer homepage retained | Report category, region, workload, ageing, movement and drill-down checks; officer/auditor regressions |
| Exact scope and reconciliation | Shared permission/filter querysets; under-process filter; active-institution escalation links include `pending=true` | Dashboard/list/CSV backend reconciliation; open versus closed-case escalation report browser regression |
| Distinct pending acknowledgment records | `awaiting_acknowledgment()` uses `Exists`; all-time institution/region/district scope | Two unacknowledged participants count as one record; receipt filters do not suppress it; invalid filters rejected |
| Invalid responsible-officer assignments | Current active membership exposed as `assignment_current`, prefetched for participants; coordinator warning uses existing revise workflow | Inactive and transferred-membership backend tests; visible warning and officer-denial browser checks |
| Obsolete reminders not actionable | Notification reads check current ownership, status, exact deadline and current reminder band | Deadline change, closure, membership change and boundary/idempotence tests |
| Reminder generation must not starve imports | One PostgreSQL `INSERT ... SELECT ... ON CONFLICT DO NOTHING`, current active memberships, stable insertion order | Original 120-second timeout captured; 148-test regression; one-query and repeat-idempotence assertions; real-corpus measurement below |
| Historical responsibility at action insertion | Additive migration `0013_caseaction_bureau_at_action.py` | ORM and direct SQL insertion, destination after transfer, append-only protection, preserved old rows and restored-copy migration |
| Complete source-upload history | `GET /api/source-intake/jobs`; source/Bureau/conflict filters; server pagination; links to older unresolved rows | 25-upload pagination, distinct conflict counts, auditor/officer scopes and browser navigation |
| Safe prepared startup/shutdown | One PowerShell controller; batch wrappers; explicit preparation; frozen model checks; database/service readiness; owned PID checks; no implicit pull/build on ordinary startup | Three operational checks, successful isolated startup, corrupt-weight rejection, unrelated PID rejection and forbidden test-port guard |
| Institution-centred working journey | Existing registry/profiles, cases/history, human relationships, coordination, transfer and audit retained | Complete multi-Bureau browser scenario, role isolation, stale-edit drafts, pagination beyond 20 and supplied-workbook checks |

## Metric definitions and data scope

Let S be the authorized cases matching the selected receipt-cohort filters.

- Received = count(S). Open = count(S where status is not `disposed`). Closed = count(S where status is `disposed`).
- Under-process = count(S where status is `under_review` or `awaiting_response`); it is included in Open.
- Overdue = open cases with `due_at < now`. Approaching = open cases with `now <= due_at <= now + 7 days`; overdue cases are excluded.
- Priority institutions group open S by canonical institution and order by overdue count descending, unresolved escalation count descending, earliest deadline, then institution ID. Five are shown.
- Urgent cases are the first eight open S ordered by deadline and ID.
- Cross-Bureau notices use all-time active cases and distinct **current** owning Bureaus. Institution/region/district filters apply; receipt/Bureau/category restrictions do not suppress these notices.
- Pending acknowledgments count distinct open coordination records with at least one participant whose acknowledgment is missing, under the same geographic scope. They are not participant totals.
- Institution profiles remain all-time and permission-scoped, independent of management receipt-date filters. Summary imports remain separate from individual complaints.

A case deadline, next-action date, manual escalation and reviewed relationship remain independent concepts. Human decisions do not merge complaints or automatically dispose of cases.

## Migration and API details

Migration `0013` adds nullable, non-editable `CaseAction.bureau_at_action`, referencing Bureau with `PROTECT`. A PostgreSQL `BEFORE INSERT` trigger reads the case's current ownership using a row share lock and sets the snapshot, including the destination ownership after a transfer. Caller-supplied snapshots cannot override it.

Existing rows are left NULL. No ownership backfill is attempted. Existing update/delete append-only triggers remain installed. Case actions continue to protect their parent cases. Action/history/movement responses expose the nullable read-only Bureau code; movement CSV appends a Bureau-at-action column. Related-query loading prevents a new query per history row.

Preserved interfaces include `GET /api/institutions`, existing statuses and optimistic versions. Additions are management priority institutions and pending-acknowledgment counts, `awaiting_ack=true` and geographic record-list filters, and paginated `/api/source-intake/jobs?source=...&bureau=...&conflicts=true`.

## Fresh checks

| Check | Observed result |
|---|---|
| Django full regression after reminder optimization and CSV reconciliation | **148/148 passed**, 51.902 seconds |
| Full Edge suite after application corrections | **51/51 passed**, including role isolation, concurrency conflicts, keyboard/mobile checks and multi-Bureau workflow |
| Supplied six-case and 1,000-row workbook UI tests | **2/2 passed**; six-case CSV contained one header plus six records; 1,000-row upload test completed in 58.7 seconds |
| Final combined browser suite | **53/53 passed**, 5.9 minutes; includes both supplied-workbook tests |
| Windows operational tests | **3/3 passed**, including checksum failure and unowned-process refusal |
| Working-port guard | Port 5173 explicitly rejected before browser tests load |
| Production build | Passed; Vite build 25.10 seconds for the final application assets |
| Pinned model and calibration | Preserved revision and threshold; no experimental activation |

The starter refund pair was retrieved with cosine similarity **0.867991** and shared explicit reference evidence. Its human decision remains pending. This is one fictional demonstration, not an accuracy estimate.

Selected screenshots: [operational dashboard](readiness-dashboard.png), [institution profile](readiness-institution.png). Raw logs/traces remain in ignored per-run storage rather than replacing older evidence.

## Measured performance

Hardware: Windows 11, Intel i5-13450HX (10 cores/16 logical processors), approximately 16 GB RAM, RTX 3050 A Laptop GPU with 4094 MiB VRAM. Node 24.19.0 and Docker 29.8.0 were recorded. Inference remains CPU with two Torch threads.

Tests used ten distinct local users. Larger imports retain synthetic records, so the corpus includes previous fixtures. These are laptop measurements with explicitly fictional text, not million-record or production promises.

| Workload | Preview | Statistical report available after confirmation | Matching and report after confirmation | Whole measured run |
|---|---:|---:|---:|---:|
| Final 1,000-row XLSX, distributed institutions | 5.90 s | 12.10 s | 44.23 s | 52.50 s |
| Diagnostic 10,000-row CSV, one institution | 49.42 s | 205.01 s | 735.22 s | 786.95 s |

The final 1,000-row statistical response contained all 1,000 cases while **15 were matched and 985 pending**. This directly verifies reporting availability before matching finishes. It met the initial 10-second preview, 30-second statistical reporting and two-minute warm-completion objectives.

The 10,000-row diagnostic included the original scheduled-reminder timeout, a controlled worker restart and investigation/regression activity. It is not a clean steady-state throughput claim. All 10,000 rows nevertheless imported and matched; the timeout evidence is retained. No two-minute target was claimed for 10,000 rows.

| HTTP measurement | p95 reads | p95 dashboard | p95 registration |
|---|---:|---:|---:|
| Ten users after initial 1,000-row import | 312 ms | 366 ms | 475 ms |
| Ten users at 11,805 existing cases | 381 ms | 528 ms | 430 ms |
| During final 1,000-row processing, nine readers plus importer | 198 ms | 416 ms | Not measured in this run |

Ordinary-request samples comprised 50 reads, 50 dashboard requests and ten registrations per run. Import-concurrent samples comprised 27 reads and 27 dashboard requests. The 500 ms reads/registration and one-second dashboard objectives were met under these conditions.

Model-only check: cold loading **5.88 seconds**; warm encoding 1,000 44-wordpiece-or-shorter summaries **7.51 seconds**, approximately **133 summaries/second**. This excludes queue and database matching. Final import timings recorded 0.075-second import queue delay, 11.02-second registration, 0.20-second matching queue delay and 31.91-second matching stage.

Reminder generation over **12,819 cases** took **0.455 and 0.497 seconds**, one SQL statement each, inserting zero duplicates. The old implementation's worker timeout occurred at 120 seconds and was preserved as diagnostic evidence.

Peak sampled whole-laptop memory use was **14.03 GiB**. Sampled container maxima were API 342 MiB, worker 508 MiB and database 314 MiB. Device-wide GPU memory reached 945 MiB, including other desktop software; this is not model VRAM allocation. Samples can miss instantaneous peaks.

## Recovery and worker evidence

The pre-change dump SHA256 is `0ab2bf785208206a9bed3a3912efbe447ce7b6f43d6353765b8ca6ac599d2470`.

The preserved working database was restored separately, with exact counts and row checksums compared across 18 core tables. **9,577 cases and 10,909 actions were preserved.** All 98 archived configuration/private/model files were extracted and hash-checked, and the stored attachment reference resolved.

A second restored copy applied migration 0013, served dashboard/registry API reads and an authorized 431-byte private attachment download, and encoded text with the restored model. All 10,909 historical Bureau snapshots remained NULL. The working database was unchanged by this verification.

Pinned model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. Weight SHA256: `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`. Threshold remains **0.603080153465271**, from existing synthetic calibration. Apache-2.0 licence text is bundled under `backend/licenses/`.

A real two-row import was confirmed with the worker stopped and completed after restart, including both matches, in **9.45 seconds**. The larger diagnostic also survived a controlled restart. Initial matching preparation subsequently processed 504 seed/demo cases in **20.64 seconds**, closing the seed-embedding preparation gap.

Recovery archives and restored databases are retained locally and ignored; they must not be added to Git.

## Offline gate and publication

**Physical-offline cold startup is unverified.** The connected-network guard correctly refused to mark it passed. Windows denied the WLAN interface query, and a safe automatic reconnect could not be established. No physical network disconnection was attempted. Absence of a cloud inference API alone is not proof of full offline startup.

Local weights loaded with offline settings, model files were read-only and checksum-verified, and browser tests blocked external requests where configured. These checks do not replace the physical gate.

The prepared operator check is `scripts/verify-physical-offline.ps1`. It requires physical adapters disconnected, cold-starts only the audit portal and records actual results. It never disables adapters itself. Docker Desktop must already be available; this is a portal-service cold start, not a Windows cold boot.

The user subsequently instructed publication to `main` after this limitation was disclosed, revising the publication requirement for this delivery. The physical-offline check remains open. Recovery checkpoints are retained; publication uses a fast-forward-only update, a normal push and local/remote SHA verification. No force-push is permitted.

## Five-minute demonstration

1. Sign in to the isolated portal on 5174 as coordinator. Search `SIH-26264-DEMO` and open the fictional Lotus institution.
2. Inspect its all-time profile, current Bureaus and chronological history. Upload `start-here-6-cases.xlsx` through Import data and inspect its six-row report.
3. Compare the two `TRAIN-REFUND-2026-A` cases; review their evidence and record a reasoned relationship. Contrast the different applicant's 2025 deposit request or the laboratory safety issue.
4. Open a coordination record, designate lead/participant officers and instructions. Officers acknowledge/complete their agreed actions; the coordinator records the outcome. Transfer a case where appropriate.
5. Show the independent case histories, destination Bureau snapshot and refreshed institution/dashboard/report. Explain the 30-day demonstration policy, receipt-cohort versus all-time scope and human review of suggestions.

Repeating identical workbook rows must produce duplicates rather than new cases. For a larger test, the supplied 1,000-row workbook uses only the standard 30 fictional Permanent IDs. Both supplied workbook paths have been exercised through the browser, not merely generated.

## Graphify and remaining limits

The refreshed source/document map retains JSON, HTML and a report. Current extraction has **1,075 nodes, 2,995 edges and 81 communities**. Runtime code-node IDs were asserted preserved when outdated guide nodes were replaced. Secrets, model files, uploads, datasets and rotating graph backups are excluded.

The health diagnostic reports zero missing/dangling endpoints, zero unverified code nodes and zero exact duplicate edges. **12 self-loops** and **one potential edge collapse if direction were removed** are retained in `GRAPH_HEALTH`; the directed graph is preserved. AST links and extracted guide headings aid navigation, while runtime permissions, SQL triggers and tests remain authoritative. Host document work is unmetered, so no token-savings claim is made.

Outstanding limits: physical offline gate; real AICTE workflow/compliance validation; real complaint-text matching accuracy; no million-record test; no clean steady-state 10,000-row import claim. Training and experimental activation were deliberately excluded from this corrective cycle.

## Local evidence index

Run directory: `tests/results/runs/readiness-20261101-115600/` (ignored). Logs: `tests/results/logs/readiness-*.log` (ignored). Selected machine-readable measurements are retained in [readiness-metrics.json](readiness-metrics.json).

Key logs include `readiness-final-backend`, `readiness-release-browser`, `readiness-handoff-browser`, `readiness-starter-full`, `readiness-startup-complete`, `readiness-final-import-1000`, `readiness-import-10000`, `readiness-http-10000`, `readiness-reminder-timeout`, `readiness-reminder-performance`, `readiness-restored-runtime` and `readiness-worker-recovery`.

## Files created and modified

The following source/artifact manifest is relative to baseline 996b2ff. Generated graph JSON/HTML and fictional test fixtures account for most added lines; application architecture and dependency stack are retained.

```text
M	.gitignore
A	.graphifyignore
M	README.md
A	START-HERE.md
M	backend/Dockerfile
M	backend/cases/access.py
M	backend/cases/analytics.py
M	backend/cases/api.py
M	backend/cases/coordination_workflow.py
M	backend/cases/institutions.py
M	backend/cases/management/commands/download_model.py
A	backend/cases/migrations/0013_caseaction_bureau_at_action.py
M	backend/cases/models.py
M	backend/cases/serializers.py
M	backend/cases/source_intake.py
M	backend/cases/tasks.py
M	backend/cases/urls.py
M	backend/config/settings.py
A	backend/licenses/minilm-LICENSE.txt
A	backend/model-manifest.json
A	compose.audit.yaml
M	frontend/playwright.config.ts
M	frontend/src/api.ts
M	frontend/src/coordination-workflow.tsx
A	frontend/src/dashboard-data.ts
M	frontend/src/dashboard.tsx
M	frontend/src/imports.tsx
M	frontend/src/institutions.tsx
M	frontend/src/main.tsx
M	frontend/src/management.tsx
A	frontend/src/page-boundary.tsx
M	frontend/src/source-intake.tsx
M	frontend/src/style.css
M	frontend/vite.config.ts
A	graphify-out/GRAPH_HEALTH.json
A	graphify-out/GRAPH_HEALTH.txt
A	graphify-out/GRAPH_REPORT.md
A	graphify-out/graph.html
A	graphify-out/graph.json
A	scripts/benchmark.py
M	scripts/benchmark_import.py
M	scripts/start.ps1
A	scripts/verify-physical-offline.ps1
M	scripts/verify_import_recovery.py
A	scripts/verify_readiness_restore.py
M	start.bat
M	stop.bat
M	tests/README.md
A	tests/backend/test_readiness.py
M	tests/browser/completion.spec.ts
M	tests/browser/coordination-workflow.spec.ts
M	tests/browser/dashboard.spec.ts
M	tests/browser/escalations.spec.ts
M	tests/browser/imports.spec.ts
M	tests/browser/institutions.spec.ts
M	tests/browser/phase2.spec.ts
A	tests/browser/readiness.spec.ts
M	tests/browser/source-intake.spec.ts
A	tests/browser/starter.spec.ts
A	tests/browser/support.ts
M	tests/browser/workflow.spec.ts
A	tests/fixtures/sih-walkthrough/generate.py
A	tests/fixtures/sih-walkthrough/load-test-1000-cases.csv
A	tests/fixtures/sih-walkthrough/load-test-1000-cases.xlsx
A	tests/fixtures/sih-walkthrough/start-here-6-cases.csv
A	tests/fixtures/sih-walkthrough/start-here-6-cases.xlsx
A	tests/operations/test_startup.py
A	tests/performance/encoder.py
A	tests/performance/reminders.py
A	tests/results/readiness-dashboard.png
A	tests/results/readiness-institution.png
A	tests/results/readiness-metrics.json
A	tests/results/readiness-verification.md
```
