# Coordination · AICTE 26264

A laptop-first complaint monitoring and cross-bureau coordination prototype. React + Django REST Framework + PostgreSQL/pgvector + a durable Django Q2 worker. English only. All bundled institutions and allegations are fictional.

## Quick start (Windows / PowerShell)

Install Node.js 22+ and Docker Desktop with Linux containers, then start Docker Desktop.

```powershell
# First setup: downloads packages and MiniLM weights. Internet required.
powershell -ExecutionPolicy Bypass -File scripts/start.ps1 -Prepare
# Later runs: local model and database, no network calls needed.
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
```

Open http://127.0.0.1:5173. Use `coordinator` / `Demo-only-26264!` (change `DEMO_PASSWORD` in `.env` before the first seed to choose another password).

Other demo accounts: `officer_rb`, `officer_pgrc`, `officer_demo`, `auditor`, `admin`. Same initial password. `admin` is for `/admin/`, not case-work privileges. Re-running seed preserves existing passwords, records, assignments, and reviews. Django Admin can change passwords.

The first setup creates 30 fictional institutions and 500 complaints, evaluates matching on incident-separated synthetic pairs, embeds seed cases, and starts the reminder scheduler. Wait for it to finish before judging. `MATCH_THRESHOLD` defaults to 0.75 only until calibration is available; `backend/calibration.json` contains the frozen synthetic-calibration threshold.

### Native development alternative

Use Python 3.12; the system Python 3.14 is not the tested interpreter. PostgreSQL still runs in Docker.

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt
docker compose up -d db
.venv/Scripts/python backend/manage.py migrate
.venv/Scripts/python backend/manage.py download_model
.venv/Scripts/python backend/manage.py seed_demo
.venv/Scripts/python backend/manage.py evaluate_matching
.venv/Scripts/python backend/manage.py match_pending
.venv/Scripts/python backend/manage.py runserver 127.0.0.1:8000 --noreload
# Second terminal
.venv/Scripts/python backend/manage.py qcluster
# Third terminal
cd frontend
npm ci
npm run dev
```

Use either native API/worker or container API/worker, not both. `docker compose stop api worker` frees the API port for native development. Vite proxies API, login and admin requests to port 8000. Bindings are localhost only. Model downloads happen only through the explicit download command; runtime tokenizer and inference use local files only.

## Working dashboard and coordination demo

The home screen prioritizes **Open complaints**, **Overdue complaints** (included in open complaints), and coordinator/auditor-only **Possible overlaps**. Possible overlaps count case pairs awaiting human review, not confirmed duplicates. Eight open cases appear in deadline order, followed by institutions needing cross-bureau coordination and two supporting charts. Officers see their bureau's cases and category chart; auditors can inspect without changing records. Full bureau names, date filters and accessible chart-value links keep the figures understandable and traceable.

1. Sign in as coordinator and open an overdue complaint from the attention list. Inspect its original allegation, deadline, responsible bureau and chronological history.
2. Open **Needs coordination**, inspect the institution's complaints, and follow **Review overlaps**. The institution and active filters stay applied when changing review tabs.
3. Compare the evidence and record same incident, related issue or unrelated with a reason. Both case histories update; neither complaint is merged or automatically closed.
4. Register or import a complaint, assign/transfer it using the existing case actions, and watch scoped dashboard figures refresh. Closing a case requires a resolution note; reopening remains coordinator-only.
5. Open **Reports** for factual analysis, ageing, matching coverage, exports and print/PDF. General reports do not request import metadata. Changing report sources cancels old requests; malformed responses show an error instead of crashing.
6. Sign in as a bureau officer to confirm transferred cases and cross-bureau suggestions are inaccessible. Check the auditor's read-only view.

The home charts show monthly receipts/closures and active workload. Their links preserve the current permission scope and intersect selected dates, so the case list agrees with the displayed count. Detailed technical diagnostics remain in Reports. The 30-day deadline is a clearly labelled demo policy, not an AICTE rule.

![Action-first AICTE dashboard](reports/dashboard-simple.png)

## Contract and limits

- Original summaries/descriptions are immutable. Corrections are append-only notes; they do not change v1 matching inputs.
- A 30-calendar-day deadline is a demo policy, **not an AICTE regulatory rule**. Reminder checks run every five minutes, with 7-day, 1-day and overdue bands; a case receives only its current band's reminder if earlier bands were missed.
- Officers see current-bureau cases. Coordinators and auditors see all demo bureaus. Only coordinators review overlaps, transfer, assign, reopen and alter deadlines. Audit accounts cannot mutate cases.
- Matching searches the same institution, across all categories and dates, including disposed cases. Top-five candidates above the calibrated threshold are suggestions only. Broad cross-bureau notices are independent of semantic scores.
- Model: `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, CPU, Apache-2.0. Summary limit is enforced with its actual tokenizer (256 wordpieces including special tokens).
- PDF/PNG/JPEG up to 5 MB; content checked; private storage; forced downloads. No antivirus/CDR: use synthetic, trusted demonstration files only. No attachment OCR or matching.
- Audit history is append-only through application interfaces and admin; database administrators can still alter it.
- Session authentication, CSRF protection, object/query scope, uniqueness, optimistic versions, transactional changes, bounded worker retries and idempotent tasks are included. This localhost prototype is not a production authorization or compliance certification.

## Verification

```powershell
.venv/Scripts/python backend/manage.py test cases --verbosity 2
docker compose run --rm api python manage.py test cases --verbosity 1
cd frontend
npm run build
npm run test:e2e
```

Browser tests use installed Microsoft Edge; change Playwright's `channel` if testing on another platform. Matching evaluation: `python backend/manage.py evaluate_matching`. `data/evaluation.json` contains labels and incident-family splits outside runtime tables. TF-IDF is fitted only on calibration text. MiniLM threshold selection uses calibration pairs only; held-out test results do not change the threshold. Precision/recall count both same-incident and related-issue pairs as review-worthy; Recall@5 measures same-incident retrieval. `reports/matching.json` records metrics and timing. Scenario labels are authored synthetic labels, **independent human review is pending**. Synthetic results cannot establish deployment accuracy.

Browser acceptance tests reject external HTTP requests and wait for a real worker scan to complete. `verify_queue_recovery` starts and stops two controlled worker clusters and asserts jobs queued while stopped finish after restart; run it only when the regular worker is stopped. `runtime_report` records actual stored matching durations and queue waits. Verification commands retain clearly marked synthetic complaints, so the live database grows beyond the original 500 seed records.

Run `python scripts/benchmark.py` while the API and worker are running for ten concurrent simulated sessions. It measures actual HTTP reads and creates synthetic benchmark complaints; these remain in the database and are clearly identified by source. Reports separate API response latency from worker matching time. Targets: API reads/creation p95 <500 ms, dashboard p95 <1 s, warm matching <3 s, synthetic precision >=85%, Recall@5 >=90%. Targets are not guarantees. See generated `reports/` for actual measurements.

## Backup and restore

`powershell -File scripts/backup.ps1` writes a PostgreSQL custom dump and optional private-files archive under ignored `backups/`. Keep both together. Never commit uploads, credentials, or dumps.

Restore into a **new empty database** before changing the working database:

```powershell
docker compose exec db createdb -U coordination coordination_restore
docker compose cp backups/YOUR_BACKUP.dump db:/tmp/restore.dump
docker compose exec db pg_restore -U coordination -d coordination_restore --exit-on-error /tmp/restore.dump
docker compose exec db psql -U coordination -d coordination_restore -c "SELECT count(*) FROM cases_complaint;"
```

The pgvector image contains the extension required by restore. Restore matching attachment files separately. The restore-check database can be kept for inspection; no command here deletes existing data.

## Development map

Backend `cases`: relational models; scoped query/filter logic; serializers; API actions; matching; reminders; management commands; acceptance tests. Frontend: typed API helper, case workflows, import workspace and factual report screens. Migrations are checked in. `compose.yaml`, lock files, `.env.example`, and startup scripts define the local runtime.

Graphify indexes source/docs only; `.graphifyignore` excludes credentials, data, weights, backups, reports, uploads and dependencies. `graphify-out/graph.html`, `graph.json` and `GRAPH_REPORT.md` are development aids, never an application dependency.

## Research

- [Sentence-BERT, EMNLP 2019](https://aclanthology.org/D19-1410/): reusable sentence embeddings.
- [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2): model limits and license.
- [PAWS, NAACL 2019](https://aclanthology.org/N19-1131/): high lexical overlap can conceal different meanings.
- [IIT Kanpur IGMS](https://iitk.ac.in/intelligent-grievance-monitoring-system-igms): grievance analytics precedent.
- [DARPG data documentation](https://event.data.gov.in/challenge/darpg-challenge/): detailed records can be restricted.
- [pgvector](https://github.com/pgvector/pgvector), [Django Q2](https://github.com/django-q2/django-q2), [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/), [OWASP uploads](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

This prototype makes no connection to AICTE or CPGRAMS and its demo seed contains no real complainants. Research complaint texts are kept outside Git and are not loaded into the portal. Official workflow compliance and real-data model accuracy require authorized validation.


## Spreadsheet imports, reports and model experiments

Open **Import data** in the portal. Download a complaint, monthly-flow or status-snapshot template, fill one sheet, upload CSV/XLSX, check the mapping and rejected rows, then confirm. Limits: 10,000 rows, 20 MB compressed, 80 MB expanded XLSX; formulas/macros/external workbook links are rejected. Canonical permanent institution IDs are mandatory. The importer never overwrites existing allegations or silently changes source records. Identical records are skipped; conflicts are rejected for review.

Complaint statistics become available before matching finishes. Import batches are durable and resumable, with private row-error CSVs. Officers lose access to an import containing a case transferred outside their bureau; remaining authorized cases stay accessible through the case registry. Status snapshots use one selected date; aggregate summaries never become individual complaints or inflate complaint totals. Report pages show source, filters, coverage and data quality, with CSV downloads and browser Print / Save PDF. Summary tables preview at most 100 rows; CSV includes every selected row.

Dashboard polling is every five seconds, active import polling every two; hidden browser tabs pause polling. Completed/failed imports stop continuous polling. Dashboard aggregates use five-second PostgreSQL-backed caching for coordinator/auditor views only, invalidated by application case/review changes. Bureau officers always query their current scope directly. The immutable baseline model files are cached per process; restart API/worker after manually changing baseline calibration files. Approved database-backed model releases switch without that file cache becoming stale.

Native research tooling (separate from the application dependencies):

```powershell
.venv/Scripts/python -m pip install -r scripts/requirements-research.txt
.venv/Scripts/python scripts/collect_training_data.py
.venv/Scripts/python scripts/train_matching.py
```

The collector downloads PAWS from its publisher mirror if the original archive is inaccessible, verifies publisher checksums, preserves published partitions, and audits the Indian government-tweet SQL **without executing SQL**. Raw research files and experimental weights are ignored by Git and Graphify. The derived tweet file removes direct metadata columns and replaces handles/emails/URLs/phone-like strings, but still requires manual privacy review; it is excluded from pair training. DARPG is an authorized-access lead, not a bundled dataset. See `reports/source-register.json` for actual acquisition status.

The education corpus contains 1,440 authored pairs across 360 families, with entire allegation templates held within one partition. `data/research/education_pair_review.csv` is the independent-review worksheet. Fine-tuning compares unchanged MiniLM, domain training, and a bounded PAWS-then-domain experiment using ContrastiveLoss, batch size 8, accumulation 4 and at most three epochs. It uses CUDA if available, otherwise CPU. Candidate selection uses validation, threshold selection uses calibration, and only the frozen selected candidate and baseline are tested. F1 ties use the fixed variant order (domain before PAWS-domain). The existing benchmark remains separate; run `python scripts/check_matching_regression.py` after training to check it without recalibration. Reports and checkpoint hashes are written to `reports/training.json`; **nothing is automatically promoted** and synthetic results cannot validate real AICTE use.

Versioned deployment uses `python manage.py model_release stage --revision NAME --path experiments/RUN/domain --threshold VALUE --report reports/training.json` in the native environment. Paths must stay inside the models directory. Staging preserves current embeddings for rollback and writes separate candidate vectors. Approval requires the evaluation gate and a documented completed human review in the experiment report; the current authored labels are not independently reviewed. `model_release activate --revision NAME` and `model_release rollback --revision PREVIOUS` reject unapproved or incomplete releases, change vectors and active revision atomically, and refresh pending suggestions while preserving reviewed evidence. A rollback after additional cases requires staging the old model for those cases first. Containers use model paths relative to `/models`; pass reports mounted under `/reports`.

Reproduce performance checks while the prepared API and worker run:

```powershell
.venv/Scripts/python scripts/benchmark_import.py --rows 1000
.venv/Scripts/python scripts/benchmark_import.py --rows 1000 --format xlsx --concentrated
.venv/Scripts/python scripts/benchmark_import.py --rows 1000 --kind monthly
.venv/Scripts/python scripts/benchmark_scale.py
```

HTTP benchmarks retain explicitly synthetic source-labelled records and measure nine readers alongside the importer. XLSX runs also sample container resource use. The scale script creates its own disposable `coordination_scale_*` database, measures 10,000/100,000-record reads, dashboards and exact vector queries, then removes only that database. Its unit vectors and absent histories/overlap rows make it a **read/search benchmark, not proof of full 100,000-row ingestion or production capacity**. Do not claim a million-record deployment from these results. See `reports/upgrade-verification.md` for measured timings and remaining limits.

For the prepared offline presentation, stop the Vite development server, then run `npm run build` and `npm run preview` inside `frontend`. The preview serves bundled assets on port 5173 and reuses the same-origin API proxy. Development remains available through `npm run dev`.

## Dashboard crash fix and release checks

`usePoll` accepts a disabled (`null`) URL, cancels obsolete requests and prevents prior-source data from rendering under a new URL. Import and report responses are checked before required fields are accessed. The dashboard API adds `attention` (up to eight active cases ordered by deadline/ID) and `active_categories`; overlap queries reuse case filters, including institution and dates. Existing database statuses and workflow rules are unchanged. See `reports/dashboard-verification.md` for current checks and screenshots.

## Institution module — Phase 1

The institution module extends the existing portal with a React directory, coordinator forms and consolidated profiles. Apply migrations with `docker compose exec api python manage.py migrate`, then restart API and worker. Migrations preserve existing identities and cases, add optional `address`, `official_email`, `official_phone` and `version` (initially 1), and enforce permanent-ID immutability in PostgreSQL. CaseAction and AuditEvent rows reject UPDATE/DELETE; corrections must append new records. These safeguards do not prevent database-administrator tampering.

| Endpoint | Contract |
|---|---|
| `GET /api/institutions?q=...` | Existing array lookup, unchanged; identity fields only, maximum 100. |
| `GET /api/institution-registry` | Paginated identity directory; ID/name search, region and existing case filters. Case filters select institutions through currently authorized cases. |
| `POST /api/institution-registry` | Coordinator registration; required name, permanent ID, region, district and reason; optional official contacts. |
| `GET /api/institutions/{id}` | Identity, contacts, version, all-time scoped totals, bureau breakdown and case/history links. Management date filters do not alter these profile totals. |
| `PATCH /api/institutions/{id}` | Coordinator edit; reason and expected_version required. Stale edits return 409; permanent-ID changes return 400. |
| `GET /api/institutions/{id}/cases` | Complete paginated cases, including closed cases; supports existing case filters. |
| `GET /api/institutions/{id}/history` | All-time paginated authorized CaseAction records, newest first, including case ID and reference. |

Paged responses use `count`, `next`, `previous`, `results`, with 20 rows per page. Institution metadata is shared with portal roles even where they have no cases; complaint counts, bureau breakdowns, pages and histories are scoped before aggregation. Officers see only cases owned by their current bureau. Coordinators and auditors see consolidated profiles; auditors cannot edit. Accounts without a portal role are denied the new endpoints. Membership and ownership are queried afresh rather than trusting cached user relations. Restricted relationship review reasons and identifiers are redacted on officer history paths.

Institution creates/edits append `institution_created`/`institution_updated` AuditEvent records with actor, reason, version and changed before/after values, in the same transaction as the profile save. Django Admin uses the same audited save path, requires a reason, protects the permanent ID and rejects stale edits. Institution case timelines derive from CaseAction; they do not duplicate action history or incorporate institution edits into case records.

Run `docker compose exec api python manage.py test cases --noinput` for institution and existing workflow regressions. See `reports/institution-phase1-verification.md` for the delivery checks and limitations.

### Institution frontend

Open **Institutions** in the primary navigation (`/institutions`). The directory uses server-side name/Permanent-ID search, region/bureau filters and pagination. Coordinators can register an institution at `/institutions/new` and edit one at `/institutions/{id}/edit`; permanent IDs are read-only after registration. Profile editing sends the loaded version and a reason. HTTP 409 preserves the draft and offers an explicit reload that discards unsaved entries; it never silently overwrites a newer profile.

Profiles at `/institutions/{id}` have Overview, Cases, History, Coordination and Reports sections. Overview always displays all-time scoped figures regardless of management-dashboard dates. Cases and CaseAction history load every page from the backend; the client holds only the requested page. The Case detail's existing limited institution preview now links to the complete paginated profile. Canonical institution names link to profiles from case tables/details, dashboard attention/notices, coordination and imported summary reports.

Officers see current-bureau case totals and histories and do not request cross-bureau coordination data. Coordinators and auditors can inspect current-owner notices and paginated suggestions/relationships; decisions still use the existing coordination queue, with auditor read-only access. Reports reuse institution-scoped analytics, CSV exports and print/PDF output. Every data request remains protected by the existing backend permissions; UI visibility does not grant access.

Existing portal controls, status labels, responsive styles and local assets are reused. To verify the bundled UI, run `npm run build` and `npm run preview` inside `frontend`, then `npx playwright test`. Institution browser tests create explicitly synthetic institutions and 25-case fixtures; repeated runs retain these test records. The verified backend recovery branch is `checkpoint/institution-backend-dfa6e5d`. See `reports/institution-frontend-verification.md` for final acceptance evidence and file/API details.
