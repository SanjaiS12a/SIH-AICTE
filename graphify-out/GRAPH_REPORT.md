# Graph Report - SIH  (2026-11-01)

## Corpus Check
- 117 files · ~63,067 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .css 2, .bat 2)

## Summary
- 1099 nodes · 3038 edges · 86 communities (34 shown, 52 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 303 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `da32e1ad`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- source-intake.spec.ts
- WorkflowTests
- imports.py
- analytics.py
- coordination_workflow.py
- verify_delivery.py
- ErrorBox
- EscalationTests
- matching.py
- package.json
- main.tsx
- management.tsx
- benchmark_scale.py
- ImportTests
- api.py
- Institution
- CaseAction
- django_db_models_deletion
- imports.tsx
- InstitutionTests
- api
- json
- CoordinationCompletionTests
- Phase2Tests
- Portal components
- relationships.py
- SourceIntakeTests
- ReadOnlyAdmin
- source-intake.tsx
- _Base
- Backend Python requirements
- coordination-workflow.tsx
- AgeingBucketTests
- DisposalRateTests
- dashboard_data
- Backend verification
- Backend verification
- Backend verification
- signals.py
- Render recovery
- Backend verification
- exports.py
- InstitutionAdmin
- AICTE institution monitoring and cross-Bureau coordination — SIH 26264
- What this project does
- UnderProcessTests
- RoleIsolationTests
- Runtime support
- InstitutionAdminForm
- AICTE SIH 26264 — Case Intelligence 2.0 implementation plan
- Project documentation
- Backend verification
- Complaint
- HistoricalMigrationTests
- 0003_modelrelease.py
- 0005_institution_contacts_version.py
- 0006_identity_and_audit_protection.py
- bureau-intake/README.md
- CSRF-protected Coordination sign-in form
- Coordination frontend HTML entrypoint
- 0004_dashboard_cache.py
- DashboardHome
- StartupTests
- Command

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 57 edges
2. `WorkflowTests` - 51 edges
3. `Institution` - 48 edges
4. `CaseAction` - 44 edges
5. `ErrorBox()` - 36 edges
6. `role()` - 35 edges
7. `scoped_cases()` - 35 edges
8. `Shell()` - 33 edges
9. `usePoll()` - 30 edges
10. `Loading()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `2. Requirement-to-code audit` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `Review screen` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `5. Milestone C — source-grounded briefs and incident organization` --references--> `ActionReadSerializer`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → backend/cases/serializers.py
- `CoordinationCompletionTests` --uses--> `Attachment`  [INFERRED]
  tests/backend/test_coordination_completion.py → backend/cases/models.py
- `CoordinationCompletionTests` --uses--> `Bureau`  [INFERRED]
  tests/backend/test_coordination_completion.py → backend/cases/models.py

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`

## Communities (86 total, 52 thin omitted)

### Community 0 - "source-intake.spec.ts"
Cohesion: 0.06
Nodes (38): endpoint, @playwright/test, post(), stamp, makeCase(), makeInstitution(), post(), stamp (+30 more)

### Community 1 - "WorkflowTests"
Cohesion: 0.06
Nodes (6): evaluation_dataset(), seed_records(), EscalationConcurrencyTests, submit(), EvaluationTests, WorkflowTests

### Community 2 - "imports.py"
Cohesion: 0.11
Nodes (37): current_bureau_id(), role(), writable(), actions(), options(), session(), accessible_jobs(), digest() (+29 more)

### Community 3 - "analytics.py"
Cohesion: 0.12
Nodes (16): coordination(), action_query(), analytics(), Meta, movements(), movements_csv(), chunks(), MovementSerializer (+8 more)

### Community 4 - "coordination_workflow.py"
Cohesion: 0.09
Nodes (24): audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput, ParticipantInput (+16 more)

### Community 5 - "verify_delivery.py"
Cohesion: 0.22
Nodes (11): digest(), main(), run(), shell(), snapshot(), digest(), main(), run() (+3 more)

### Community 7 - "ErrorBox"
Cohesion: 0.17
Nodes (32): CoordinationRecordPage(), CoordinationRequests(), CoordinationWorkspace(), usePoll(), InstitutionCases(), change(), InstitutionCoordination(), InstitutionDirectory() (+24 more)

### Community 8 - "EscalationTests"
Cohesion: 0.10
Nodes (5): Notification, notify_escalation(), send_reminders(), EscalationTests, AccountabilityTests

### Community 9 - "matching.py"
Cohesion: 0.10
Nodes (15): Command, calibrate(), Command, metrics(), Command, baseline_runtime(), cached_encoder(), cached_tokenizer() (+7 more)

### Community 10 - "package.json"
Cohesion: 0.07
Nodes (28): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+20 more)

### Community 11 - "main.tsx"
Cohesion: 0.20
Nodes (22): ApiError, Attachment, Case, CaseDetail, categories, classifications, csrf(), Dashboard (+14 more)

### Community 12 - "management.tsx"
Cohesion: 0.20
Nodes (15): Movement, InstitutionOverview(), AgeingPanel(), BureauWorkloadPanel(), ChartRow, HorizontalDistribution(), InstitutionMonitoringPanel(), InstitutionRow (+7 more)

### Community 13 - "benchmark_scale.py"
Cohesion: 0.08
Nodes (12): browser(), main(), Memory, request(), simulate(), main(), simulate(), main() (+4 more)

### Community 14 - "ImportTests"
Cohesion: 0.13
Nodes (4): cell(), parse_file(), DashboardTests, ImportTests

### Community 15 - "api.py"
Cohesion: 0.16
Nodes (13): scoped_cases(), case_detail(), download(), notifications(), overlap_data(), overlaps(), review(), upload() (+5 more)

### Community 17 - "Institution"
Cohesion: 0.24
Nodes (16): institutions(), page(), detail(), history(), institution_cases(), InstitutionHistorySerializer, InstitutionProfileSerializer, InstitutionWriteSerializer (+8 more)

### Community 18 - "CaseAction"
Cohesion: 0.17
Nodes (17): cases(), replay(), Conflict, case_escalations(), CreateEscalationSerializer, EscalationSerializer, Meta, queue() (+9 more)

### Community 19 - "django_db_models_deletion"
Cohesion: 0.12
Nodes (7): Migration, Migration, Migration, Migration, Migration, Migration, Migration

### Community 20 - "imports.tsx"
Cohesion: 0.19
Nodes (20): validDashboard(), Bars(), ErrorNotice(), ExportButton(), Facts, ImportDetail(), Imports(), isExport() (+12 more)

### Community 22 - "api"
Cohesion: 0.14
Nodes (22): api(), date(), errorText(), Escalation, CoordinationAction(), submit(), CaseEscalations(), EscalationList() (+14 more)

### Community 23 - "json"
Cohesion: 0.14
Nodes (3): Command, Migration, Migration

### Community 26 - "Portal components"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 27 - "relationships.py"
Cohesion: 0.20
Nodes (4): export(), chunks(), manual(), ManualRelationshipSerializer

### Community 30 - "source-intake.tsx"
Cohesion: 0.25
Nodes (7): Row, Source, SourceJob, validJob(), validRows(), validSourceJobs(), validSources()

### Community 31 - "_Base"
Cohesion: 0.18
Nodes (3): _Base, WorkloadInstitutionCountTests, HomepageTests

### Community 32 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 33 - "coordination-workflow.tsx"
Cohesion: 0.29
Nodes (9): CaseAction, Participant, Record, Request, validHistory(), validPage(), validRecord(), validRecords() (+1 more)

### Community 36 - "dashboard_data"
Cohesion: 0.33
Nodes (4): dashboard(), dashboard_data(), Command, simulate()

### Community 45 - "exports.py"
Cohesion: 0.21
Nodes (14): filtered_cases(), report(), chunks(), authorized_file(), build_export(), case_values(), export_detail(), export_download() (+6 more)

### Community 47 - "AICTE institution monitoring and cross-Bureau coordination — SIH 26264"
Cohesion: 0.40
Nodes (5): AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Start or stop a prepared demo, Data, permissions and demonstration, Verification and recovery, Prepare once while online

### Community 48 - "What this project does"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, What runs on the laptop, Open the prepared demonstration

### Community 51 - "Runtime support"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

### Community 53 - "AICTE SIH 26264 — Case Intelligence 2.0 implementation plan"
Cohesion: 0.12
Nodes (16): 10. Order, effort and decisions, 1. Outcome and verified starting point, 2. Requirement-to-code audit, 3. Milestone A — simpler official workspace, 4. Milestone B — explainable matching, evaluated before activation, 5. Milestone C — source-grounded briefs and incident organization, 6. Milestone D — optional read-only MCP, 7. File-by-file execution backlog (+8 more)

### Community 56 - "Complaint"
Cohesion: 0.15
Nodes (10): Command, refresh_active_matches(), swap_release(), Command, Complaint, Meta, ModelRelease, StagedEmbedding (+2 more)

## Knowledge Gaps
- **105 isolated node(s):** `Meta`, `Meta`, `Meta`, `Migration`, `Migration` (+100 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 385 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **52 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Shell()` connect `ErrorBox` to `Render recovery`, `main.tsx`, `management.tsx`, `DashboardHome`, `imports.tsx`, `api`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `WorkflowTests` connect `WorkflowTests` to `imports.py`, `analytics.py`, `coordination_workflow.py`, `EscalationTests`, `api.py`, `Institution`, `CaseAction`, `Complaint`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `compute_dashboard()` connect `analytics.py` to `Complaint`, `CaseAction`, `exports.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Meta`, `Meta`, `Meta` to the rest of the system?**
  _105 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `source-intake.spec.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.05621621621621622 - nodes in this community are weakly interconnected._
- **Should `WorkflowTests` be split into smaller, more focused modules?**
  _Cohesion score 0.05612244897959184 - nodes in this community are weakly interconnected._