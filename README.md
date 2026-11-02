# AICTE institution monitoring and cross-Bureau coordination — SIH 26264

New to the project? Start with [the plain-language walkthrough and ready-to-upload Excel files](START-HERE.md).

The official workspace uses five primary sections: Home, Institutions, My Work, Data Imports and Reports. My Work groups case queues and coordination tasks; import history and movement reports remain available through contextual links. Existing URLs are preserved. See the [Case Intelligence implementation plan](docs/plans/case-intelligence-2.0.md) for the staged scope; later matching and protocol milestones are not enabled by the navigation revision.

Case Intelligence B1 adds [versioned comparison evidence and immutable review-time snapshots](docs/evidence-v1.md), with [verification and synthetic evaluation results](tests/results/case-intelligence-b1-verification.md). It preserves the existing MiniLM retrieval policy and threshold. Routine matching evaluation writes new reports only inside ignored run directories and never changes production calibration.

A local SIH prototype for identifying an institution, consolidating its cases across Bureaus, reviewing overlaps and recording accountable coordinated work. RB means **Regulation Bureau**; PGRC means **Public Grievance Redressal Cell**.

The existing React/Vite/TypeScript frontend, Django/DRF session API, PostgreSQL 17/pgvector database and Django Q2 ORM worker are retained. Exact institution-filtered vector search and the original local MiniLM provide suggestions; human decisions remain authoritative. This is a prototype, not an approved AICTE production deployment.

## Prepare once while online

Install Docker Desktop and supported Node.js (20.19+, 22.12+, or the verified Node 24 installation). Start Docker Desktop, then run from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1 -Action Prepare
```

Preparation creates a missing `.env` from `.env.example`, builds the application image, migrates the database, downloads only the pinned baseline model, verifies its checksum, creates missing fictional demo records and installs/builds the locked frontend. Existing account passwords and cases are not reset. Retain prepared images, dependencies, model assets and persistent volumes for later offline startup.

## Start or stop a prepared demo

Preparation also runs the existing `match_pending` command so seeded complaints can participate in similarity review before the offline demonstration.

Run `start.bat` or `stop.bat`. The wrappers use the same PowerShell controller. Normal startup does not install dependencies or download a model. It verifies prerequisites/assets, waits for database/API readiness, applies pending migrations and serves the bundled frontend at http://127.0.0.1:5173. Errors return a nonzero exit code instead of claiming success. Shutdown targets the recorded workspace-owned frontend process and stops services without deleting database volumes.

The backend is a localhost Django development server at port 8000; Vite preview serves the bundled local interface. This is not Gunicorn or a public-hosting configuration.

Demo usernames: `coordinator`, `auditor`, `officer_rb`, `officer_pgrc`, `officer_demo`. New demo accounts use `DEMO_PASSWORD` from the preparation environment. Existing accounts keep their database credentials. Do not assume that changing `.env` resets a password or changes credentials already initialized in a PostgreSQL volume.

## Data, permissions and demonstration

For the isolated operational demonstration, use `scripts/start.ps1 -Audit -Demo -Action Prepare`, then `-Action Start`. Open `/guide` through Help for the data flow, fictional CSV downloads and role-aware walkthrough. See the [operational workflow](docs/operational-workflow.md) for missing-category handling, reviewed source updates and demo isolation. Existing records and decisions are preserved; normal deployment defaults remain unchanged.

Use the [fictional independent Bureau fixtures](tests/fixtures/bureau-intake/README.md) to import RB, PGRC and other-cell records into one canonical institution. Source status mappings preserve original references and statuses; changed rows require review and never silently replace allegations. File uploads are snapshots, not live connections to AICTE systems.

Follow institution profile → Coordination → agreed responsibilities → officer acknowledgment/completion → coordinator outcome. Cases, transfers, deadlines, escalation and coordination states remain independent. Auditors inspect without modifying; officers retain current-Bureau case isolation and only receive instructions explicitly addressed to them.

The 30-calendar-day deadline is a demonstration policy, not an AICTE rule. Closed is the display label for stored status `disposed`. Original MiniLM revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; the calibrated threshold remains in `backend/calibration.json`. Its evidence is synthetic, with human domain review pending. No production accuracy, regulatory compliance or million-record capacity is claimed.

## Verification and recovery

The [core incident workflow](docs/core-intelligence.md) defines separate complaint/pair/group counts, audited group retirement, source-preserving experiments and versioned hand-off to Bureau coordination. The [six-case fixture](tests/fixtures/core-intelligence/README.md) exercises six independent complaints linked to one reviewed incident. Incident groups remain disabled by default; verify them on the isolated audit stack before any live-demo activation.

The [portal UI verification](tests/results/portal-ui-verification.md) covers the institution-first home layout, shared government theme, responsive navigation and browser workflow regressions.

The [movement CSV follow-up](tests/results/movement-export-hardening.md) records the post-publication export correction: 10,000 synthetic rows fell from 10,005 Django SQL executions to six with identical CSV bytes. The separate real-data and physical-offline acceptance gates remain open.

See [implementation design and five-minute demo](docs/technical-design.md) for HLD/LLD, schema relationships, lifecycle, permissions and case intelligence. Case briefs are read-only current-state views. Reviewed facts and manual incident groups are separate experiments, controlled by `ENABLE_REVIEWED_FACTS=1` and `ENABLE_INCIDENT_GROUPS=1`; both default off. Shadow discovery never changes production matching. [Research intake](docs/research-permission-and-intake.md) records the human and permission gates.

Preparation now invokes `seed_if_empty`: only an empty designated demo database is seeded. Existing data is neither reset nor augmented. Use `scripts/verify_final_restore.py` to verify recovery of current isolated audit data/private files/model into independent destinations. New scale runs require a fresh `coordination_scale_*` database and an explicit new `/reports/...` output path; do not reuse historical artifacts.

Test sources and historical evidence are under `tests/`; reports describe the commits and conditions actually tested. A discovered test count is not proof of a fresh passing run. Per-run execution evidence belongs in ignored `tests/results/runs/`, not over earlier screenshots.

The corrective readiness cycle uses `compose.audit.yaml`, a separate database/private-data volume, API port 8001 and frontend port 5174. Models are read-only. It must not use or reset the working demo database. Set `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5174`, `API_PROXY_TARGET=http://127.0.0.1:8001` and the audit artifact directory when running browser tests.

With the image and pinned assets already prepared, initialize a fresh audit run from the repository root:

```powershell
$stamp = Get-Date -Format yyyyMMdd-HHmmss
$auditProject = "sih-readiness-$stamp"
$auditRoot = Join-Path (Get-Location) "tests/results/runs/readiness-$stamp"
New-Item -ItemType Directory -Path $auditRoot | Out-Null
New-Item -ItemType Directory -Force tests/results/logs | Out-Null
@{run="readiness-$stamp";directory=$auditRoot;project=$auditProject} | ConvertTo-Json | Set-Content tests/results/logs/readiness-run.json
powershell -ExecutionPolicy Bypass -File scripts/start.ps1 -Action Prepare -Audit
powershell -ExecutionPolicy Bypass -File scripts/start.ps1 -Action Start -Audit
$env:AUDIT_RESULTS = $auditRoot
docker compose -p $auditProject -f compose.audit.yaml exec -T api python manage.py test cases --noinput
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5174'
$env:AUDIT_ARTIFACT_DIR = Join-Path $auditRoot 'browser'
Push-Location frontend
npx playwright test
Pop-Location
```

Browser tests default to the isolated port and reject the working demo ports. Unconfigured output paths are unique per run. Use `scripts/verify-physical-offline.ps1` only after the operator disconnects physical networking; it records failures as failures and never disables adapters itself.

Backups, configuration secrets, private uploads, datasets and weights stay out of Git. A database restore does not restore attachment/model files. Full physically disconnected cold startup and release performance must have separate recorded evidence before offline readiness is declared. A missing mandatory release gate blocks publication of the corrective release to main.

Graphify is a source/document navigation aid, not an application dependency. Its map must exclude secrets and data and be checked against source and tests. Experimental research files staged under ignored `trash/` are not required to run the deployed baseline model.
