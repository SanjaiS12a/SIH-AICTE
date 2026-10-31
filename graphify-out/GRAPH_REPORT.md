# Graph Report - SIH  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 745 nodes · 1915 edges · 35 communities (14 shown, 21 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 192 edges (avg confidence: 0.93)
- Token cost: structural extraction 0; host semantic extraction usage unavailable.

## Graph Freshness
- Built from commit: `1f9e5d74`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api.py
- main.tsx
- train_matching.py
- Complaint
- Coordination - AICTE 26264
- package.json
- WorkflowTests
- ImportTests
- institutions.spec.ts
- InstitutionTests
- Phase2Tests
- django_db
- compilerOptions
- InstitutionAdmin
- models.py
- signals.py
- demo_data.py
- Backend Python requirements
- 0001_initial.py
- compilerOptions
- Command
- InstitutionMigrationTests
- Phase2MigrationTests
- Centralized test commands and result layout
- README.md

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 49 edges
2. `WorkflowTests` - 43 edges
3. `Institution` - 39 edges
4. `Coordination - AICTE 26264` - 37 edges
5. `InstitutionTests` - 28 edges
6. `ImportTests` - 23 edges
7. `role()` - 23 edges
8. `CaseAction` - 22 edges
9. `scoped_cases()` - 21 edges
10. `Shell()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `RolloutTests` --uses--> `ImportJob`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `DashboardTests` --uses--> `CaseAction`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `DashboardTests` --uses--> `Institution`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `DashboardTests` --uses--> `OverlapCandidate`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `ImportTests` --uses--> `Complaint`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (35 total, 21 thin omitted)

### Community 0 - "api.py"
Cohesion: 0.05
Nodes (84): coordination(), current_bureau_id(), filtered_cases(), role(), scoped_cases(), writable(), actions(), case_detail() (+76 more)

### Community 1 - "main.tsx"
Cohesion: 0.07
Nodes (79): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, categories, classifications (+71 more)

### Community 2 - "train_matching.py"
Cohesion: 0.05
Nodes (38): calibrate(), Command, metrics(), main(), redact(), sql_values(), main(), download() (+30 more)

### Community 3 - "Complaint"
Cohesion: 0.05
Nodes (31): Command, Command, Command, refresh_active_matches(), swap_release(), Command, baseline_runtime(), cached_encoder() (+23 more)

### Community 4 - "Coordination - AICTE 26264"
Cohesion: 0.05
Nodes (46): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Action-first deadline and bureau-coordination dashboard, Immutable allegations and append-only corrections and audit history, PostgreSQL dump and private-files backup and restore, Audited case classification with backward-compatible Unclassified default, Complaint monitoring and cross-bureau coordination prototype, Coordination - AICTE 26264 (+38 more)

### Community 5 - "package.json"
Cohesion: 0.06
Nodes (30): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+22 more)

### Community 7 - "ImportTests"
Cohesion: 0.16
Nodes (3): process_import(), DashboardTests, ImportTests

### Community 8 - "institutions.spec.ts"
Cohesion: 0.12
Nodes (8): createInstitution(), csrf(), post(), stamp, createCase(), csrf(), post(), stamp

### Community 11 - "django_db"
Cohesion: 0.12
Nodes (6): Migration, Migration, Migration, Migration, Migration, Migration

### Community 12 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 14 - "InstitutionAdmin"
Cohesion: 0.14
Nodes (4): InstitutionAdmin, InstitutionAdminForm, Meta, ReadOnlyAdmin

### Community 17 - "demo_data.py"
Cohesion: 0.20
Nodes (3): evaluation_dataset(), seed_records(), EvaluationTests

### Community 18 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 20 - "compilerOptions"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

## Knowledge Gaps
- **93 isolated node(s):** `Migration`, `Migration`, `Migration`, `Meta`, `Migration` (+88 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 256 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `api.py`, `demo_data.py`, `Complaint`, `models.py`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `InstitutionTests` (e.g. with `AuditEvent` and `CaseAction`) actually correct?**
  _`InstitutionTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _93 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.051036682615629984 - nodes in this community are weakly interconnected._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.070271407532085 - nodes in this community are weakly interconnected._
- **Should `train_matching.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05025394279604384 - nodes in this community are weakly interconnected._