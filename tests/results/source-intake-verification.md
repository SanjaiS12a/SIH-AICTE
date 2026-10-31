# Milestone 2 — independent Bureau file consolidation

31 October 2026. Baseline `66ad4d4`; implementation branch `codex/bureau-data-consolidation`. The accepted coordination backend, stack, original MiniLM, institution lookup contract and independent case histories are retained.

## Verified results

| Check | Actual result |
|---|---|
| Complete Django regression suite after queue-authorization fixes | **118 passed**, 29.911 seconds |
| Complete bundled Edge browser regression suite | **45 passed**, 6.3 minutes |
| Production build | TypeScript/Vite **passed**, 15.89 seconds |
| Migration drift | **No changes detected** |
| Source-only bundled browser rerun after final queue guards | **4 passed**, 35.4 seconds |
| Fresh post-test schema-0012 backup / separate restore | **Passed**, 18 table counts and full row checksums matched; working database unchanged |
| Pre-change backup and separate restore | **Passed**, 17 table counts/row checksums matched |
| Migration 0012 in restored and working databases | **Passed**, existing-row checksums matched after excluding only newly added columns |

The browser suite adds four tests to the accepted 41-test baseline. It proves three independently formatted Bureau files consolidate into one institution; original references/statuses survive; repeated RB input creates no extra cases; changed source content is reviewed without replacement; stale case versions return 409 and preserve drafts until explicit reload; row 21 is reachable through server pagination; auditors are read-only; officers cannot obtain another import's rows or source counts; mobile containment and malformed responses work. Existing coordination, institution, report, import, escalation and case regressions also passed.

The final backend suite adds ten tests to the accepted 108-test baseline, including the permission transition between confirmation and queued processing. A transferred duplicate cannot receive unauthorized receipt metadata, and a deactivated owner cannot continue queued registration. Source fields are loaded with relationships without a query per candidate pair. Export tests reconcile the synchronous and asynchronous CSV paths. No new large-scale benchmark or model evaluation was run.

Local ignored logs: `source-intake-full-backend.log`, `source-intake-full-browser.log`, `source-intake-browser-final.log`, `source-intake-build.log`, `source-intake-migrations.log`, and recovery logs under `tests/results/logs/`. The source-only browser suite passed again after the final queue guards. Browser timings are functional test durations, not upload performance promises.

## Requirement-to-code trace

| Capability | Reuse / change | Source |
|---|---|---|
| Safe CSV/XLSX parsing, canonical institution IDs, mapped columns, durable 250-row batches | Reuse | `backend/cases/imports.py` |
| Source identity and explicit status translations | Extend existing ImportJob; validate source configuration | `models.py`, migration 0012, `source_intake.configuration`, `Imports` UI |
| Original source status/Bureau and receipt provenance | Add nullable/blank metadata without inventing historical values | `Complaint`, `CaseSerializer`, case detail/list, shared CSV formatter |
| Duplicate handling | Retain existing source/reference uniqueness and immutable allegations; update confirmed receipt metadata only | `validate_rows`, `process_import` |
| Changed-source review | Distinct conflict state for declared sources; keep original mapped input/raw row, dual version checks, reasoned keep-portal decision | `source_intake.rows/resolve`, `SourceRows`, existing CaseAction |
| Accurate totals and matching scope | Include only imported/unchanged duplicate rows in import-scoped cases, exports and matching retries | `access.filtered_cases`, `job_data`, matching task selection |
| Upload receipt catalog | Permission-scoped grouped source data, last upload/registration/full acceptance, unresolved conflict-row count, source search and server pagination | `/api/source-intake`, `SourceIntake` |
| Integrated institution journey | Original source references in existing case tables; existing all-time notices and coordination links reused | `ui.tsx`, `main.tsx`, existing institution/coordination screens |
| Recovery and preservation | Separate-database restores, checksums, retained ignored archives | recovery JSON and `scripts/verify_source_restore.py` |

New endpoints: `GET /api/source-intake`, `GET /api/imports/{id}/rows`, `POST /api/imports/{id}/rows/{number}/resolve`. Existing `/api/imports` accepts optional `source_system`, `source_bureau` and `status_mapping`; generic imports and summary datasets retain their contracts. Case CSVs append source fields; existing columns keep their positions. The original `GET /api/institutions` lookup contract is unchanged.

## Data and policy definitions

- Source ID + source reference is the identity namespace. Original Bureau is retained separately from current ownership. An original source status is stored separately from normalized/current portal status.
- Only mapped, validated fields determine equality. Unknown institution IDs are rejected; there is no fuzzy or automatic identity resolution. Unmapped extra columns remain raw evidence without becoming case fields.
- A changed source row does not update allegations, workflow status, deadlines, ownership, embeddings or human relationship decisions. A keep-portal review rejects the incoming replacement and appends one CaseAction, with safe retry handling. If a portal correction is warranted, use the existing authorized case operation separately.
- Last successful upload means registration completed and every row was imported or an unchanged duplicate. Rejected, conflicting or disputed/resolved rows do not advance that source's full acceptance time. Matching completion is separate. These are portal processing times, not upstream timestamps or live AICTE integration.
- Receipt updates acquire current authorized case locks. Current role/Bureau ownership is checked again during queued registration. A failed batch preserves prior committed batches and reports failure without publishing restricted records.

## Reproduction and recovery

Use `tests/fixtures/bureau-intake/README.md` and `manifest.json`. All inputs are explicitly fictional. The demonstration covers RB, PGRC and an additional cell, different headers/status labels, unchanged replay, changed status and unknown institution. Then continue through the existing institution Coordination section to assign/acknowledge/complete agreed work.

Recovery checkpoint: `checkpoint/pre-source-intake-66ad4d4`. `source-intake-recovery.json` records a full restore of the pre-change database, migration on that separate copy, and preservation checks on the working database. It includes coordination records/participants and import/audit data. `source-intake-latest-restore.json` records a fresh schema-0012 backup restore after source data exists. Both database archives are ignored; they contain private records/configuration and are not committed.

For another database-only check, run `python scripts/verify_source_restore.py` from the repository root. It briefly stops API/worker, snapshots a new archive, restores into a generated separate database, compares 18 tables including source provenance and auth/coordination records, verifies the working database is unchanged, then resumes the services. It retains its backup and separate restored database. This is not a filesystem/model restore or physical offline-startup check.

## Remaining scope and limitations

This completes file-based multi-Bureau intake, not automated external synchronization. The source catalog aggregates upload receipts; the existing Recent imports list remains the most recent 20 jobs. Older jobs and rows remain available by their preserved import IDs, including references in case/audit history; a separate complete source-job-history browser is not introduced here. Conflict counts represent rows across upload attempts, not distinct disputed incidents.

Management homepage redesign/expanded administrative analytics are the next milestone; no claim is made that they are completed by these intake screens. Physical offline startup, combined private-file/model restoration and official AICTE workflow/integration validation remain outstanding. Existing historical performance misses remain documented; no million-record or production-accuracy promise is made. No fine-tuning or model change was performed.

Graphify source/document refresh: 1,040 nodes and 2,950 edges; no unverified code nodes or missing/dangling endpoints. 8 self-loop edges remain explicitly reported. CSV/JSON fixture data, model assets, secrets, raw datasets and result archives are excluded. The graph includes source and the demonstration README; source/tests remain authoritative where extraction is incomplete. Structural extraction used no model tokens; host semantic token usage is unavailable.
