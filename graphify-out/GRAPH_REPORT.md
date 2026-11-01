# Graph Report - SIH  (2026-11-01)

## Corpus Check
- 119 files · ~56,987 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: (none) 5, .css 2, .bat 2)

## Summary
- 1075 nodes · 2995 edges · 81 communities (31 shown, 50 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 300 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `285336e7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Browser verification
- Backend verification
- Spreadsheet intake
- Management reporting
- Bureau coordination
- Runtime support
- Institution profiles
- Backend verification
- Semantic matching
- Portal components
- Complaint operations
- Management reporting
- Local tooling
- Backend verification
- Complaint operations
- Runtime support
- Institution profiles
- Runtime support
- Runtime support
- Spreadsheet intake
- Backend verification
- Portal components
- Management commands
- Backend verification
- Backend verification
- Portal components
- Runtime support
- Backend verification
- Runtime support
- Source reconciliation
- Backend verification
- Runtime support
- Bureau coordination
- Backend verification
- Backend verification
- Management commands
- Backend verification
- Backend verification
- Backend verification
- Runtime support
- Render recovery
- Backend verification
- Runtime support
- Runtime support
- Project documentation
- Project documentation
- Backend verification
- Backend verification
- Runtime support
- Runtime support
- Management commands
- Project documentation
- Backend verification
- Backend verification
- Backend verification
- Schema migrations
- Schema migrations
- Schema migrations
- Project documentation
- Runtime support
- Portal components

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 57 edges
2. `WorkflowTests` - 51 edges
3. `Institution` - 48 edges
4. `CaseAction` - 44 edges
5. `ErrorBox()` - 36 edges
6. `role()` - 35 edges
7. `scoped_cases()` - 35 edges
8. `Shell()` - 32 edges
9. `usePoll()` - 30 edges
10. `Loading()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `EscalationConcurrencyTests` --uses--> `CaseAction`  [INFERRED]
  tests/backend/test_escalations.py → backend/cases/models.py
- `EscalationConcurrencyTests` --uses--> `Escalation`  [INFERRED]
  tests/backend/test_escalations.py → backend/cases/models.py
- `ConcurrentSubmissionTests` --uses--> `Bureau`  [INFERRED]
  tests/backend/test_workflow.py → backend/cases/models.py
- `ConcurrentSubmissionTests` --uses--> `CaseAction`  [INFERRED]
  tests/backend/test_workflow.py → backend/cases/models.py
- `ConcurrentSubmissionTests` --uses--> `Complaint`  [INFERRED]
  tests/backend/test_workflow.py → backend/cases/models.py

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`

## Communities (81 total, 50 thin omitted)

### Community 0 - "Browser verification"
Cohesion: 0.06
Nodes (36): endpoint, @playwright/test, makeCase(), makeInstitution(), post(), stamp, token(), post() (+28 more)

### Community 1 - "Backend verification"
Cohesion: 0.05
Nodes (8): evaluation_dataset(), seed_records(), Command, EscalationConcurrencyTests, ConcurrentSubmissionTests, submit(), EvaluationTests, WorkflowTests

### Community 2 - "Spreadsheet intake"
Cohesion: 0.11
Nodes (36): current_bureau_id(), writable(), accessible_jobs(), cell(), digest(), get_job(), import_detail(), import_errors() (+28 more)

### Community 3 - "Management reporting"
Cohesion: 0.09
Nodes (25): filtered_cases(), action_query(), analytics(), Meta, movements(), movements_csv(), chunks(), MovementSerializer (+17 more)

### Community 4 - "Bureau coordination"
Cohesion: 0.10
Nodes (23): audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput, ParticipantInput (+15 more)

### Community 5 - "Runtime support"
Cohesion: 0.09
Nodes (15): main(), Memory, ticks(), digest(), main(), run(), shell(), snapshot() (+7 more)

### Community 7 - "Institution profiles"
Cohesion: 0.17
Nodes (28): CoordinationRecordPage(), CoordinationRequests(), CoordinationWorkspace(), usePoll(), InstitutionCases(), change(), InstitutionDirectory(), InstitutionEditor() (+20 more)

### Community 8 - "Backend verification"
Cohesion: 0.10
Nodes (5): Notification, notify_escalation(), send_reminders(), EscalationTests, AccountabilityTests

### Community 9 - "Semantic matching"
Cohesion: 0.13
Nodes (17): Command, Command, refresh_active_matches(), swap_release(), baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder() (+9 more)

### Community 10 - "Portal components"
Cohesion: 0.07
Nodes (28): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+20 more)

### Community 11 - "Complaint operations"
Cohesion: 0.21
Nodes (21): ApiError, Attachment, Case, CaseDetail, categories, classifications, csrf(), Dashboard (+13 more)

### Community 12 - "Management reporting"
Cohesion: 0.13
Nodes (22): date(), Movement, DashboardHome(), monthName(), InstitutionCoordination(), InstitutionOverview(), AgeingPanel(), BureauWorkloadPanel() (+14 more)

### Community 13 - "Local tooling"
Cohesion: 0.12
Nodes (10): Migration, browser(), main(), Memory, request(), simulate(), main(), simulate() (+2 more)

### Community 14 - "Backend verification"
Cohesion: 0.15
Nodes (3): DashboardTests, ImportTests, RolloutTests

### Community 15 - "Complaint operations"
Cohesion: 0.18
Nodes (16): coordination(), role(), scoped_cases(), actions(), case_detail(), download(), notifications(), options() (+8 more)

### Community 17 - "Institution profiles"
Cohesion: 0.19
Nodes (17): institutions(), page(), detail(), history(), institution_cases(), InstitutionHistorySerializer, InstitutionProfileSerializer, InstitutionWriteSerializer (+9 more)

### Community 18 - "Runtime support"
Cohesion: 0.18
Nodes (16): cases(), replay(), Conflict, case_escalations(), CreateEscalationSerializer, EscalationSerializer, Meta, queue() (+8 more)

### Community 19 - "Runtime support"
Cohesion: 0.11
Nodes (9): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+1 more)

### Community 20 - "Spreadsheet intake"
Cohesion: 0.19
Nodes (20): validDashboard(), Bars(), ErrorNotice(), ExportButton(), Facts, ImportDetail(), Imports(), isExport() (+12 more)

### Community 22 - "Portal components"
Cohesion: 0.16
Nodes (17): api(), errorText(), Escalation, CoordinationAction(), submit(), CaseEscalations(), EscalationList(), EscalationQueue() (+9 more)

### Community 23 - "Management commands"
Cohesion: 0.14
Nodes (3): calibrate(), Command, metrics()

### Community 26 - "Portal components"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 27 - "Runtime support"
Cohesion: 0.24
Nodes (10): overlap_data(), overlap_queryset(), overlaps(), safe(), OverlapCandidate, decide(), export(), chunks() (+2 more)

### Community 30 - "Source reconciliation"
Cohesion: 0.23
Nodes (11): ReviewConflict(), submit(), Row, Source, SourceJob, SourceRows(), time(), validJob() (+3 more)

### Community 31 - "Backend verification"
Cohesion: 0.18
Nodes (3): _Base, WorkloadInstitutionCountTests, HomepageTests

### Community 32 - "Runtime support"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 33 - "Bureau coordination"
Cohesion: 0.29
Nodes (9): CaseAction, Participant, Record, Request, validHistory(), validPage(), validRecord(), validRecords() (+1 more)

### Community 36 - "Management commands"
Cohesion: 0.33
Nodes (4): dashboard(), dashboard_data(), Command, simulate()

### Community 47 - "Project documentation"
Cohesion: 0.40
Nodes (5): AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Start or stop a prepared demo, Data, permissions and demonstration, Verification and recovery, Prepare once while online

### Community 48 - "Project documentation"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, What runs on the laptop, Open the prepared demonstration

### Community 51 - "Runtime support"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

## Knowledge Gaps
- **94 isolated node(s):** `Attachment`, `ChartRow`, `InstitutionRow`, `Notice`, `Migration` (+89 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 371 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **50 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `Backend verification` to `Spreadsheet intake`, `Bureau coordination`, `Backend verification`, `Semantic matching`, `Complaint operations`, `Institution profiles`, `Runtime support`, `Runtime support`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `filtered_cases()` connect `Management reporting` to `Spreadsheet intake`, `Complaint operations`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `analytics()` connect `Management reporting` to `Bureau coordination`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Attachment`, `ChartRow`, `InstitutionRow` to the rest of the system?**
  _94 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Browser verification` be split into smaller, more focused modules?**
  _Cohesion score 0.060041407867494824 - nodes in this community are weakly interconnected._
- **Should `Backend verification` be split into smaller, more focused modules?**
  _Cohesion score 0.05079825834542816 - nodes in this community are weakly interconnected._
## Extraction limits

Code relationships use Graphify AST evidence. Document headings were extracted inline from the four current guides, with source lines retained. Only outdated guide nodes were intentionally replaced; runtime code-node identifiers were asserted unchanged before export. Host semantic work is unmetered; numeric zero tooling counters are not a claim that host reasoning consumed no tokens. Runtime permissions, SQL triggers and behavior remain governed by source and tests. Secrets, model files, private uploads, datasets, generated test runs and rotating graph backups are excluded.
