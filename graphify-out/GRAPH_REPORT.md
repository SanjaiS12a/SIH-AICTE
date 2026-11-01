# Graph Report - SIH  (2026-11-01)

## Corpus Check
- 122 files · ~68,590 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .css 2, .bat 2)

## Summary
- 1168 nodes · 3231 edges · 86 communities (37 shown, 49 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 321 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `55f38048`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- source-intake.spec.ts
- WorkflowTests
- imports.py
- exports.py
- coordination_workflow.py
- verify_delivery.py
- main.tsx
- EscalationTests
- matching.py
- package.json
- institutions.tsx
- management.tsx
- benchmark_scale.py
- ImportTests
- api.py
- Institution
- escalations.py
- django_db_models_deletion
- imports.tsx
- InstitutionTests
- api
- json
- CoordinationCompletionTests
- Phase2Tests
- Portal components
- CaseSerializer
- SourceIntakeTests
- ReadOnlyAdmin
- source-intake.tsx
- _Base
- Backend Python requirements
- evidence.py
- AgeingBucketTests
- DisposalRateTests
- EvidenceWorkflowTests
- Backend verification
- Backend verification
- Backend verification
- signals.py
- react
- Backend verification
- role
- InstitutionAdmin
- AICTE institution monitoring and cross-Bureau coordination — SIH 26264
- What this project does
- UnderProcessTests
- RoleIsolationTests
- Runtime support
- usePoll
- AICTE SIH 26264 — Case Intelligence 2.0 implementation plan
- Project documentation
- Backend verification
- Command
- HistoricalMigrationTests
- 0003_modelrelease.py
- 0005_institution_contacts_version.py
- 0006_identity_and_audit_protection.py
- bureau-intake/README.md
- CSRF-protected Coordination sign-in form
- evidence.tsx
- Coordination frontend HTML entrypoint
- 0004_dashboard_cache.py
- apps.py
- test_startup.py
- Command

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 59 edges
2. `WorkflowTests` - 51 edges
3. `Institution` - 50 edges
4. `CaseAction` - 47 edges
5. `ErrorBox()` - 36 edges
6. `role()` - 35 edges
7. `scoped_cases()` - 35 edges
8. `Shell()` - 33 edges
9. `usePoll()` - 30 edges
10. `Bureau` - 29 edges

## Surprising Connections (you probably didn't know these)
- `Read APIs and interface` --references--> `ActionReadSerializer`  [INFERRED]
  docs/evidence-v1.md → backend/cases/serializers.py
- `2. Requirement-to-code audit` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `Review screen` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `5. Milestone C — source-grounded briefs and incident organization` --references--> `ActionReadSerializer`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → backend/cases/serializers.py
- `Evidence contract` --references--> `score()`  [INFERRED]
  docs/evidence-v1.md → backend/cases/management/commands/evaluate_matching.py

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`

## Communities (86 total, 49 thin omitted)

### Community 0 - "source-intake.spec.ts"
Cohesion: 0.05
Nodes (41): endpoint, @playwright/test, post(), stamp, makeCase(), makeInstitution(), post(), stamp (+33 more)

### Community 1 - "WorkflowTests"
Cohesion: 0.08
Nodes (3): EscalationConcurrencyTests, submit(), WorkflowTests

### Community 2 - "imports.py"
Cohesion: 0.10
Nodes (34): accessible_jobs(), cell(), digest(), get_job(), import_detail(), import_errors(), import_report(), import_summary_csv() (+26 more)

### Community 3 - "exports.py"
Cohesion: 0.11
Nodes (20): filtered_cases(), action_query(), Meta, movements(), movements_csv(), chunks(), MovementSerializer, report() (+12 more)

### Community 4 - "coordination_workflow.py"
Cohesion: 0.10
Nodes (23): audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput, ParticipantInput (+15 more)

### Community 5 - "verify_delivery.py"
Cohesion: 0.22
Nodes (11): digest(), main(), run(), shell(), snapshot(), digest(), main(), run() (+3 more)

### Community 7 - "main.tsx"
Cohesion: 0.19
Nodes (25): CaseDetail, CoordinationAction(), CoordinationRecordPage(), CoordinationRequests(), CoordinationWorkspace(), InstitutionDirectory(), InstitutionEditor(), InstitutionForm() (+17 more)

### Community 8 - "EscalationTests"
Cohesion: 0.10
Nodes (5): Notification, notify_escalation(), send_reminders(), EscalationTests, AccountabilityTests

### Community 9 - "matching.py"
Cohesion: 0.11
Nodes (18): Command, Command, Command, refresh_active_matches(), swap_release(), baseline_runtime(), cached_encoder(), cached_tokenizer() (+10 more)

### Community 10 - "package.json"
Cohesion: 0.07
Nodes (28): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+20 more)

### Community 11 - "institutions.tsx"
Cohesion: 0.15
Nodes (24): ApiError, Attachment, Case, CaseAction, classifications, EvidenceComparison, Institution, InstitutionAction (+16 more)

### Community 12 - "management.tsx"
Cohesion: 0.19
Nodes (19): date(), Movement, InstitutionCoordination(), InstitutionOverview(), AgeingPanel(), BureauWorkloadPanel(), ChartRow, CoordinationNotices() (+11 more)

### Community 13 - "benchmark_scale.py"
Cohesion: 0.09
Nodes (12): browser(), main(), Memory, request(), simulate(), main(), simulate(), main() (+4 more)

### Community 14 - "ImportTests"
Cohesion: 0.15
Nodes (3): DashboardTests, ImportTests, RolloutTests

### Community 15 - "api.py"
Cohesion: 0.12
Nodes (19): Conflict, overlap_data(), overlap_queryset(), overlaps(), review(), review_snapshots(), decision_snapshot(), Command (+11 more)

### Community 17 - "Institution"
Cohesion: 0.24
Nodes (16): institutions(), page(), detail(), history(), institution_cases(), InstitutionHistorySerializer, InstitutionProfileSerializer, InstitutionWriteSerializer (+8 more)

### Community 18 - "escalations.py"
Cohesion: 0.19
Nodes (13): dashboard(), dashboard_data(), case_escalations(), CreateEscalationSerializer, EscalationSerializer, Meta, queue(), records() (+5 more)

### Community 19 - "django_db_models_deletion"
Cohesion: 0.12
Nodes (7): Migration, Migration, Migration, Migration, Migration, Migration, Migration

### Community 20 - "imports.tsx"
Cohesion: 0.14
Nodes (21): categories, Dashboard, Options, DashboardHome(), validDashboard(), monthName(), Facts, isExport() (+13 more)

### Community 22 - "api"
Cohesion: 0.15
Nodes (17): api(), csrf(), errorText(), Escalation, submit(), CaseEscalations(), EscalationList(), EscalationQueue() (+9 more)

### Community 23 - "json"
Cohesion: 0.10
Nodes (6): Command, eligible_corpus(), evaluate(), metrics(), Migration, Migration

### Community 26 - "Portal components"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 27 - "CaseSerializer"
Cohesion: 0.15
Nodes (10): analytics(), compute_dashboard(), active_cases(), enrich(), groups(), notices(), CaseSerializer, Meta (+2 more)

### Community 30 - "source-intake.tsx"
Cohesion: 0.25
Nodes (10): ReviewConflict(), Row, Source, SourceJob, SourceRows(), time(), validJob(), validRows() (+2 more)

### Community 31 - "_Base"
Cohesion: 0.18
Nodes (3): _Base, WorkloadInstitutionCountTests, HomepageTests

### Community 32 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 33 - "evidence.py"
Cohesion: 0.17
Nodes (6): build_evidence(), compare(), recorded(), corpus_fixture(), EvaluationSafetyTests, EvidenceContractTests

### Community 36 - "EvidenceWorkflowTests"
Cohesion: 0.18
Nodes (3): ConcurrentEvidenceTests, EvidenceFixture, EvidenceWorkflowTests

### Community 41 - "react"
Cohesion: 0.33
Nodes (3): Boundary, PageBoundary(), react

### Community 45 - "role"
Cohesion: 0.25
Nodes (16): coordination(), current_bureau_id(), role(), scoped_cases(), writable(), actions(), case_detail(), cases() (+8 more)

### Community 46 - "InstitutionAdmin"
Cohesion: 0.10
Nodes (4): InstitutionAdmin, InstitutionAdminForm, Meta, Phase2MigrationTests

### Community 47 - "AICTE institution monitoring and cross-Bureau coordination — SIH 26264"
Cohesion: 0.40
Nodes (5): AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Start or stop a prepared demo, Data, permissions and demonstration, Verification and recovery, Prepare once while online

### Community 48 - "What this project does"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, What runs on the laptop, Open the prepared demonstration

### Community 51 - "Runtime support"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

### Community 52 - "usePoll"
Cohesion: 0.23
Nodes (11): Bars(), ErrorNotice(), ExportButton(), Imports(), Report(), usePoll(), InstitutionCases(), change() (+3 more)

### Community 53 - "AICTE SIH 26264 — Case Intelligence 2.0 implementation plan"
Cohesion: 0.06
Nodes (26): evaluation_dataset(), seed_records(), calibrate(), score(), Evidence contract, Read APIs and interface, Relationship evidence v1 and decision snapshots, Review transaction and versioning (+18 more)

### Community 68 - "evidence.tsx"
Cohesion: 0.25
Nodes (10): MatchingEvidence, ReviewSnapshot, CapturedMetadata(), fields, PairEvidence(), ReviewEvidence(), states, value() (+2 more)

## Knowledge Gaps
- **109 isolated node(s):** `Meta`, `Meta`, `Meta`, `Migration`, `Migration` (+104 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 398 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **49 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `dashboard_data()` connect `escalations.py` to `CaseSerializer`, `exports.py`, `role`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `compute_dashboard()` connect `CaseSerializer` to `imports.py`, `exports.py`, `role`, `api.py`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `WorkflowTests` connect `WorkflowTests` to `imports.py`, `coordination_workflow.py`, `EscalationTests`, `api.py`, `Institution`, `AICTE SIH 26264 — Case Intelligence 2.0 implementation plan`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Meta`, `Meta`, `Meta` to the rest of the system?**
  _109 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `source-intake.spec.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.052160493827160495 - nodes in this community are weakly interconnected._
- **Should `WorkflowTests` be split into smaller, more focused modules?**
  _Cohesion score 0.07681365576102418 - nodes in this community are weakly interconnected._