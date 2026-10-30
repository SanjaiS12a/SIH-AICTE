# Graph Report - SIH  (2026-10-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 695 nodes · 1788 edges · 35 communities (18 shown, 17 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 185 edges (avg confidence: 0.93)
- Token cost: structural extraction uses zero model tokens; host semantic usage is unavailable and is not estimated.

## Graph Freshness
- Built from source commit: `4a9c25ec`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api.py
- main.tsx
- train_matching.py
- Coordination - AICTE 26264
- test_workflow.py
- collect_training_data.py
- package.json
- WorkflowTests
- benchmark_import.py
- ImportTests
- matching.py
- InstitutionTests
- institutions.spec.ts
- pathlib
- models.py
- compilerOptions
- Complaint
- commands/benchmark_scale.py
- Institution
- model_release.py
- Backend Python requirements
- apps.py
- InstitutionAdmin
- compilerOptions
- ReadOnlyAdmin
- Command
- README.md

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 45 edges
2. `WorkflowTests` - 41 edges
3. `Institution` - 39 edges
4. `Coordination - AICTE 26264` - 34 edges
5. `InstitutionTests` - 26 edges
6. `role()` - 23 edges
7. `ImportTests` - 22 edges
8. `CaseAction` - 21 edges
9. `scoped_cases()` - 21 edges
10. `Shell()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `ConcurrentSubmissionTests` --uses--> `CaseAction`  [INFERRED]
  tests/backend/test_workflow.py → backend/cases/models.py
- `ConcurrentSubmissionTests` --uses--> `Complaint`  [INFERRED]
  tests/backend/test_workflow.py → backend/cases/models.py
- `ConcurrentSubmissionTests` --uses--> `Institution`  [INFERRED]
  tests/backend/test_workflow.py → backend/cases/models.py
- `DashboardTests` --uses--> `CaseAction`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `DashboardTests` --uses--> `Institution`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (35 total, 17 thin omitted)

### Community 0 - "api.py"
Cohesion: 0.06
Nodes (75): coordination(), current_bureau_id(), filtered_cases(), role(), scoped_cases(), writable(), actions(), case_detail() (+67 more)

### Community 1 - "main.tsx"
Cohesion: 0.07
Nodes (79): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, categories, csrf() (+71 more)

### Community 2 - "train_matching.py"
Cohesion: 0.07
Nodes (21): evaluation_dataset(), seed_records(), calibrate(), Command, metrics(), evaluate(), main(), save() (+13 more)

### Community 3 - "Coordination - AICTE 26264"
Cohesion: 0.05
Nodes (44): CSRF-protected Coordination sign-in form, Centralized test commands and result layout, Coordination frontend HTML entrypoint, Action-first deadline and bureau-coordination dashboard, Immutable allegations and append-only corrections and audit history, PostgreSQL dump and private-files backup and restore, Complaint monitoring and cross-bureau coordination prototype, Coordination - AICTE 26264 (+36 more)

### Community 4 - "test_workflow.py"
Cohesion: 0.07
Nodes (8): Migration, Migration, Migration, Migration, Migration, Migration, Migration, InstitutionMigrationTests

### Community 5 - "collect_training_data.py"
Cohesion: 0.11
Nodes (15): main(), redact(), sql_values(), main(), download(), main(), synthetic(), clean_training() (+7 more)

### Community 6 - "package.json"
Cohesion: 0.06
Nodes (29): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+21 more)

### Community 8 - "benchmark_import.py"
Cohesion: 0.12
Nodes (8): browser(), main(), request(), simulate(), main(), simulate(), docker(), main()

### Community 9 - "ImportTests"
Cohesion: 0.15
Nodes (3): DashboardTests, ImportTests, RolloutTests

### Community 10 - "matching.py"
Cohesion: 0.18
Nodes (12): Command, baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch(), match_case(), ModelUnavailable (+4 more)

### Community 12 - "institutions.spec.ts"
Cohesion: 0.16
Nodes (4): createInstitution(), csrf(), post(), stamp

### Community 14 - "models.py"
Cohesion: 0.25
Nodes (10): Command, Attachment, Bureau, ImportRow, Membership, Meta, ModelRelease, Notification (+2 more)

### Community 15 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 16 - "Complaint"
Cohesion: 0.23
Nodes (4): Complaint, ActionSerializer, CreateCaseSerializer, send_reminders()

### Community 18 - "Institution"
Cohesion: 0.20
Nodes (5): InstitutionAdminForm, Meta, Command, Command, Institution

### Community 19 - "model_release.py"
Cohesion: 0.29
Nodes (4): Command, refresh_active_matches(), swap_release(), StagedEmbedding

### Community 20 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 23 - "compilerOptions"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

## Knowledge Gaps
- **86 isolated node(s):** `Meta`, `Attachment`, `CaseAction`, `Facts`, `Job` (+81 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 239 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `api.py`, `train_matching.py`, `models.py`, `Complaint`, `Institution`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `Complaint` connect `Complaint` to `models.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `InstitutionTests` (e.g. with `AuditEvent` and `CaseAction`) actually correct?**
  _`InstitutionTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Meta`, `Attachment`, `CaseAction` to the rest of the system?**
  _86 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05921601334445371 - nodes in this community are weakly interconnected._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06942983378918578 - nodes in this community are weakly interconnected._