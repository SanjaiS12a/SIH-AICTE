# Graph Report - SIH  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 698 nodes · 1790 edges · 35 communities (15 shown, 20 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 185 edges (avg confidence: 0.93)
- Token cost: structural extraction 0; host semantic extraction usage unavailable.

## Graph Freshness
- Built from commit: `06ec0a40`
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
- ImportTests
- InstitutionTests
- benchmark_import.py
- matching.py
- institutions.spec.ts
- json
- compilerOptions
- signals.py
- model_release.py
- Backend Python requirements
- time
- InstitutionAdmin
- compilerOptions
- ReadOnlyAdmin
- InstitutionAdminForm
- Command
- README.md
- Centralized test commands and result layout

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 45 edges
2. `WorkflowTests` - 41 edges
3. `Institution` - 39 edges
4. `Coordination - AICTE 26264` - 35 edges
5. `InstitutionTests` - 28 edges
6. `role()` - 23 edges
7. `ImportTests` - 22 edges
8. `CaseAction` - 21 edges
9. `scoped_cases()` - 21 edges
10. `Shell()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `DashboardTests` --uses--> `CaseAction`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `DashboardTests` --uses--> `Institution`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `DashboardTests` --uses--> `OverlapCandidate`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `ImportTests` --uses--> `Complaint`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `ImportTests` --uses--> `ImportJob`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (35 total, 20 thin omitted)

### Community 0 - "api.py"
Cohesion: 0.05
Nodes (87): coordination(), current_bureau_id(), filtered_cases(), role(), scoped_cases(), writable(), actions(), case_detail() (+79 more)

### Community 1 - "main.tsx"
Cohesion: 0.07
Nodes (79): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, categories, csrf() (+71 more)

### Community 2 - "train_matching.py"
Cohesion: 0.08
Nodes (21): evaluation_dataset(), seed_records(), calibrate(), Command, metrics(), evaluate(), main(), save() (+13 more)

### Community 3 - "Coordination - AICTE 26264"
Cohesion: 0.05
Nodes (44): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Action-first deadline and bureau-coordination dashboard, Immutable allegations and append-only corrections and audit history, PostgreSQL dump and private-files backup and restore, Complaint monitoring and cross-bureau coordination prototype, Coordination - AICTE 26264, Human overlap review, transfer and independent case histories (+36 more)

### Community 4 - "test_workflow.py"
Cohesion: 0.07
Nodes (8): Migration, Migration, Migration, Migration, Migration, Migration, Migration, InstitutionMigrationTests

### Community 5 - "collect_training_data.py"
Cohesion: 0.10
Nodes (15): main(), redact(), sql_values(), main(), download(), main(), synthetic(), clean_training() (+7 more)

### Community 6 - "package.json"
Cohesion: 0.06
Nodes (29): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+21 more)

### Community 8 - "ImportTests"
Cohesion: 0.13
Nodes (5): cell(), parse_file(), DashboardTests, ImportTests, RolloutTests

### Community 10 - "benchmark_import.py"
Cohesion: 0.18
Nodes (8): browser(), main(), request(), simulate(), main(), simulate(), docker(), main()

### Community 11 - "matching.py"
Cohesion: 0.18
Nodes (13): Command, refresh_active_matches(), baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch(), match_case() (+5 more)

### Community 12 - "institutions.spec.ts"
Cohesion: 0.16
Nodes (4): createInstitution(), csrf(), post(), stamp

### Community 14 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 17 - "model_release.py"
Cohesion: 0.33
Nodes (4): Command, swap_release(), ModelRelease, StagedEmbedding

### Community 18 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 21 - "compilerOptions"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

## Knowledge Gaps
- **88 isolated node(s):** `Meta`, `Attachment`, `CaseAction`, `Facts`, `Job` (+83 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 243 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `api.py`, `train_matching.py`, `json`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `InstitutionTests` (e.g. with `AuditEvent` and `CaseAction`) actually correct?**
  _`InstitutionTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Meta`, `Attachment`, `CaseAction` to the rest of the system?**
  _88 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.052496798975672214 - nodes in this community are weakly interconnected._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06942983378918578 - nodes in this community are weakly interconnected._
- **Should `train_matching.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07729468599033816 - nodes in this community are weakly interconnected._