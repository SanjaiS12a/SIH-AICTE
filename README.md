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

![Action-first AICTE dashboard](tests/results/dashboard-simple.png)

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

Browser tests use installed Microsoft Edge; change Playwright's `channel` if testing on another platform. Matching evaluation: `python backend/manage.py evaluate_matching`. `data/evaluation.json` contains labels and incident-family splits outside runtime tables. TF-IDF is fitted only on calibration text. MiniLM threshold selection uses calibration pairs only; held-out test results do not change the threshold. Precision/recall count both same-incident and related-issue pairs as review-worthy; Recall@5 measures same-incident retrieval. `tests/results/matching.json` records metrics and timing. Scenario labels are authored synthetic labels, **independent human review is pending**. Synthetic results cannot establish deployment accuracy.

Browser acceptance tests reject external HTTP requests and wait for a real worker scan to complete. `verify_queue_recovery` starts and stops two controlled worker clusters and asserts jobs queued while stopped finish after restart; run it only when the regular worker is stopped. `runtime_report` records actual stored matching durations and queue waits. Verification commands retain clearly marked synthetic complaints, so the live database grows beyond the original 500 seed records.

Run `python scripts/benchmark.py` while the API and worker are running for ten concurrent simulated sessions. It measures actual HTTP reads and creates synthetic benchmark complaints; these remain in the database and are clearly identified by source. Reports separate API response latency from worker matching time. Targets: API reads/creation p95 <500 ms, dashboard p95 <1 s, warm matching <3 s, synthetic precision >=85%, Recall@5 >=90%. Targets are not guarantees. See generated `tests/results/` for actual measurements.

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

The collector downloads PAWS from its publisher mirror if the original archive is inaccessible, verifies publisher checksums, preserves published partitions, and audits the Indian government-tweet SQL **without executing SQL**. Raw research files and experimental weights are ignored by Git and Graphify. The derived tweet file removes direct metadata columns and replaces handles/emails/URLs/phone-like strings, but still requires manual privacy review; it is excluded from pair training. DARPG is an authorized-access lead, not a bundled dataset. See `tests/results/source-register.json` for actual acquisition status.

The education corpus contains 1,440 authored pairs across 360 families, with entire allegation templates held within one partition. `data/research/education_pair_review.csv` is the independent-review worksheet. Fine-tuning compares unchanged MiniLM, domain training, and a bounded PAWS-then-domain experiment using ContrastiveLoss, batch size 8, accumulation 4 and at most three epochs. It uses CUDA if available, otherwise CPU. Candidate selection uses validation, threshold selection uses calibration, and only the frozen selected candidate and baseline are tested. F1 ties use the fixed variant order (domain before PAWS-domain). The existing benchmark remains separate; run `python tests/research/check_matching_regression.py` after training to check it without recalibration. Reports and checkpoint hashes are written to `tests/results/training.json`; **nothing is automatically promoted** and synthetic results cannot validate real AICTE use.

Versioned deployment uses `python manage.py model_release stage --revision NAME --path experiments/RUN/domain --threshold VALUE --report tests/results/training.json` in the native environment. Paths must stay inside the models directory. Staging preserves current embeddings for rollback and writes separate candidate vectors. Approval requires the evaluation gate and a documented completed human review in the experiment report; the current authored labels are not independently reviewed. `model_release activate --revision NAME` and `model_release rollback --revision PREVIOUS` reject unapproved or incomplete releases, change vectors and active revision atomically, and refresh pending suggestions while preserving reviewed evidence. A rollback after additional cases requires staging the old model for those cases first. Containers use model paths relative to `/models`; pass reports mounted under `/reports`.

Reproduce performance checks while the prepared API and worker run:

```powershell
.venv/Scripts/python scripts/benchmark_import.py --rows 1000
.venv/Scripts/python scripts/benchmark_import.py --rows 1000 --format xlsx --concentrated
.venv/Scripts/python scripts/benchmark_import.py --rows 1000 --kind monthly
.venv/Scripts/python scripts/benchmark_scale.py
```

HTTP benchmarks retain explicitly synthetic source-labelled records and measure nine readers alongside the importer. XLSX runs also sample container resource use. The scale script creates its own disposable `coordination_scale_*` database, measures 10,000/100,000-record reads, dashboards and exact vector queries, then removes only that database. Its unit vectors and absent histories/overlap rows make it a **read/search benchmark, not proof of full 100,000-row ingestion or production capacity**. Do not claim a million-record deployment from these results. See `tests/results/upgrade-verification.md` for measured timings and remaining limits.

For the prepared offline presentation, stop the Vite development server, then run `npm run build` and `npm run preview` inside `frontend`. The preview serves bundled assets on port 5173 and reuses the same-origin API proxy. Development remains available through `npm run dev`.

## Dashboard crash fix and release checks

`usePoll` accepts a disabled (`null`) URL, cancels obsolete requests and prevents prior-source data from rendering under a new URL. Import and report responses are checked before required fields are accessed. The dashboard API adds `attention` (up to eight active cases ordered by deadline/ID) and `active_categories`; overlap queries reuse case filters, including institution and dates. Existing database statuses and workflow rules are unchanged. See `tests/results/dashboard-verification.md` for current checks and screenshots.

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

Run `docker compose exec api python manage.py test cases --noinput` for institution and existing workflow regressions. See `tests/results/institution-phase1-verification.md` for the delivery checks and limitations.

### Institution frontend

Open **Institutions** in the primary navigation (`/institutions`). The directory uses server-side name/Permanent-ID search, region/bureau filters, partial case-insensitive district search and pagination. District searches include institutions with no cases; complaint counts and case filters retain current permission scope. The optional `district` query parameter is also supported by shared case/dashboard/export filtering, with an 80-character limit. The existing `GET /api/institutions` lookup contract is unchanged. Coordinators can register an institution at `/institutions/new` and edit one at `/institutions/{id}/edit`; permanent IDs are read-only after registration. Profile editing sends the loaded version and a reason. HTTP 409 preserves the draft and offers an explicit reload that discards unsaved entries; it never silently overwrites a newer profile.

Profiles at `/institutions/{id}` have Overview, Cases, History, Coordination and Reports sections. Overview always displays all-time scoped figures regardless of management-dashboard dates. Cases and CaseAction history load every page from the backend; the client holds only the requested page. The Case detail's existing limited institution preview now links to the complete paginated profile. Canonical institution names link to profiles from case tables/details, dashboard attention/notices, coordination and imported summary reports.

### Phase 2: classification and next actions

Migration `0008_case_classification_next_action` adds three case fields without replacing existing records. Every legacy case starts as `unclassified`; categories and bureau ownership are unchanged. Classification values are `grievance`, `regulatory_compliance` and `unclassified`. Manual registration requires an explicit choice; older API clients and complaint spreadsheets may omit it and retain the Unclassified default. The complaint import template has an optional `classification` column. Historical submission/import fingerprints remain compatible when the classification is Unclassified.

Use the existing `POST /api/cases/{id}/actions` contract, always with `expected_version` and a nonblank `reason`:

- `kind: "classification"`, `classification: "grievance"`: coordinator-only correction. Original allegation text and embeddings remain unchanged.
- `kind: "next_action"`, `next_action: "Request inspection evidence"`, `next_action_date: "2026-11-12"`: coordinator or current owning-bureau officer. Date is optional; omission/null clears the date. Empty description and null/omitted date clear the operational next action. A date requires a description; maximum description length is 1,000 characters.

Both operations increment the case version and append before/after values to the authoritative CaseAction history. Stale writes return HTTP 409. The case form retains its draft, blocks stale resubmission and offers an explicit reload that discards the draft. Setting a next-action date does not change the disposal deadline, status, ownership, notifications or relationships. Closing a case clears next-action fields in the same transaction and preserves their previous values in the closure action. Reopening does not resurrect cleared work; record a new next action explicitly. Closed cases reject next-action updates.

The case registry, institution Cases tab and dashboard More filters accept classification; existing case/report/export APIs reuse that permission-scoped filter. Institution Overview returns all-time `classifications: [{classification, count}, ...]` for all three values and provides case drill-downs. CSV exports append Classification, Next action and Expected action date, preserving the earlier column order. Aggregate monthly/snapshot datasets have no case classifications and remain separate.

Run `docker compose exec api python manage.py migrate`, then restart the API and worker before using the new bundled frontend. Use the existing test commands below; focused workflow tests are in `tests/backend/test_phase2.py` and `tests/browser/phase2.spec.ts`. Escalation support is described separately below; manual relationships, model changes and embedding backfills remain outside these capabilities.

### Phase 2 Task 3: manual escalations

Apply migration `0009_manual_escalations` and restart API/worker before serving the new build. On an active case, a current owning-bureau officer or coordinator chooses **Escalate for supervisory review** and supplies a reason. Only one unresolved request is allowed. Requests remain pending through transfer and case closure; their current Bureau determines officer access. Coordinators resolve requests with a separate reason from the **Escalations** queue or case's paginated escalation history. Auditors can inspect but cannot create or resolve. Institution Overview and case lists show scoped unresolved indicators, including outstanding requests on closed cases.

- `GET /api/escalations`: coordinator/auditor queue, server-paginated. `state=pending` is the default; `resolved` and `all` are supported. Existing case filters (including institution and classification) apply to its owning cases. Case status uses the existing `status` filter, separately from escalation `state`.
- `GET /api/cases/{id}/escalations`: complete, server-paginated history of authorized case requests; default `state=all`.
- `POST /api/cases/{id}/escalations`: `submission_id` (client UUID), `expected_version` (case version) and nonblank `reason` (maximum 4,000 characters). Returns 201, or 200 for the same actor/case/request/reason retry, even after resolution. Reusing the UUID with different content or creating another pending request returns 409. Original-actor access is not retained after ownership/membership changes.
- `POST /api/escalations/{id}/resolve`: coordinator-only, `expected_version` (escalation version) and nonblank `reason`. Returns 200. An identical retry by the resolver against the prior version returns the recorded result; stale/different resolution attempts return 409. The form retains a conflicting draft until explicit reload/discard.

Each creation/resolution increments the case version and appends a CaseAction in the same transaction. It changes no case status, deadline, next action, ownership, assignment or model field. Protected foreign keys retain the escalation when parent deletion is attempted. PostgreSQL enforces a partial unique index for pending requests, valid resolution state and one notification per recipient/escalation event. New `has_unresolved_escalation` case responses and `overview.unresolved_escalations` institution totals reuse current authorization. `escalated=true` filters case lists, dashboard/report queries and exports.

Creation durably queues `cases.tasks.notify_escalation` using the existing ORM broker. Delivery is transactional and idempotent, targets currently active coordinators and can run again safely after failure. Coordinator notifications are permission-checked again when read/marked read; demoted or inactive recipients receive no escalation metadata or counts. New escalation events have `deadline: null` and separate `created_at`, `escalation_id` and `escalation_status` fields. Existing deadline reminders keep their values and uniqueness rule. Notifications link to the case's escalation history.

The worker retains the configured bounded retries. If these are exhausted, inspect the failed Django Q task in Admin, address the cause, then enqueue the same event again from `manage.py shell` with `async_task('cases.tasks.notify_escalation', '<escalation UUID>')`. This does not duplicate requests, audit entries or existing recipient notifications. There is no new task-retry interface or automatic escalation rule.

Before adding this schema, both the previous backup and a new current-state backup were fully restored to separate databases; counts, core-table row checksums and institution APIs were checked. See `tests/results/escalation-recovery-verification.json` and the Task 3 verification report. Database rollback is separate from a Git checkout; the database archives exclude private file/model assets. Manual relationships and enhanced cross-bureau notices remain pending, and model experiments remain paused.

Officers see current-bureau case totals and histories and do not request cross-bureau coordination data. Coordinators and auditors can inspect current-owner notices and paginated suggestions/relationships; decisions still use the existing coordination queue, with auditor read-only access. Reports reuse institution-scoped analytics, CSV exports and print/PDF output. Every data request remains protected by the existing backend permissions; UI visibility does not grant access.

Existing portal controls, status labels, responsive styles and local assets are reused. To verify the bundled UI, run `npm run build` and `npm run preview` inside `frontend`, then `npx playwright test`. Institution browser tests create explicitly synthetic institutions and 25-case fixtures; repeated runs retain these test records. The verified backend recovery branch is `checkpoint/institution-backend-dfa6e5d`. See `tests/results/institution-frontend-verification.md` for final acceptance evidence and file/API details.

## Tests, evidence and database environment

All test bodies and evidence are centralized under `tests/`: Django checks in `backend/`, Playwright in `browser/`, research checks in `research/`, and reports/metrics/screenshots in `results/`. Logs, traces and HTML reports live in ignored subdirectories of `tests/results/`. See `tests/README.md` for commands. The existing `manage.py test cases` command remains supported through a small discovery entrypoint. Compose mounts `tests/` into the application and keeps `/reports` as a container alias for the same result folder.

Use the existing **PostgreSQL 17 + pgvector** service for this project. `.env.example` documents its variables; copy it to the ignored `.env` before first startup. Docker Compose reads `.env` automatically. Host tools connect to `127.0.0.1:5438` by default; API/worker connect to `db:5432`. Native Django uses process environment variables and defaults, not automatic dotenv loading. Existing PostgreSQL volumes keep their initialized database credentials: changing a password string in `.env` alone does not rotate the existing database password. The local environment preserves those credentials. Secrets, uploads, raw datasets, model files, training environments and large model bundles stay out of Git.

## Public-data MiniLM candidate experiment

The public-pair upgrade uses Google Research PAWS-Wiki Final plus its human-labelled Swap-only auxiliary training split. After duplicate/conflicting-pair removal, **79,656** training pairs remain. Official dev is divided by connected sentence groups into validation/calibration; official test stays separate. Prepared files are publisher-checksum verified; no normalized sentence crosses training/evaluation or validation/calibration boundaries. These are paraphrase/different-meaning labels, **not AICTE same-incident labels**. Source/provenance and token-limit audits are in `tests/results/public-pairs-audit.json` and `source-register.json`.

The separate complaint-language audit includes the previously acquired Indian government tweets and published CFPB student-loan narratives. These have no incident-overlap labels, so they are not silently converted into supervised pairs. Raw/derived complaint text remains excluded from Git and needs privacy review before sharing. No verified open AICTE complaint-text corpus was found; DARPG records remain an authorized-access lead.

GPU training is isolated from the working CPU application environment. From the repository root, after the existing `.venv` research dependencies and baseline model are installed:

```powershell
.venv/Scripts/python -m venv .venv-training
.venv-training/Scripts/python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
.venv/Scripts/python -c "from pathlib import Path; Path('.venv-training/Lib/site-packages/project_dependencies.pth').write_text(str(Path('.venv/Lib/site-packages').resolve())+'\n',encoding='utf-8')"
.venv/Scripts/python scripts/collect_training_data.py
.venv/Scripts/python scripts/prepare_public_pairs.py
.venv/Scripts/python scripts/collect_complaint_context.py
.venv-training/Scripts/python -u scripts/train_public_paraphrase.py
```

This Windows setup shadows only the training environment's PyTorch and reuses the pinned project dependencies; it does not replace application PyTorch. The trainer checks CUDA, pilots memory/throughput, uses mixed precision and an effective batch of 32, discards pilot updates, trains a fresh baseline copy for one predeclared epoch, calibrates separately and evaluates the frozen candidate once. It retains the deployed baseline. Progress is in ignored `tests/results/public-paraphrase-progress.json`; final measurements are in `public-paraphrase-training.json`. `artifacts/minilm-public-paraphrase-candidate.zip` is the teammate bundle, including weights, tokenizer, configuration, licences, evaluation and offline CPU-loading instructions. Share the complete folder/ZIP, not only the `.safetensors` file. Model promotion still requires domain validation and the existing release/backfill gates.
