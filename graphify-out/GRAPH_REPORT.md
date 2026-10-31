# Graph Report - SIH  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 711 nodes · 1835 edges · 39 communities (21 shown, 18 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 186 edges (avg confidence: 0.93)
- Token cost: structural extraction 0; host semantic extraction usage unavailable.

## Graph Freshness
- Built from commit: `0d99e1df`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.tsx
- Complaint
- Coordination - AICTE 26264
- WorkflowTests
- api.py
- test_workflow.py
- imports.py
- matching.py
- package.json
- ImportTests
- institutions.py
- collect_training_data.py
- json
- train_matching.py
- InstitutionTests
- institutions.spec.ts
- compare_fresh_models.py
- compilerOptions
- prepare_public_pairs.py
- evaluate_matching.py
- Backend Python requirements
- apps.py
- InstitutionAdmin
- compilerOptions
- ReadOnlyAdmin
- InstitutionAdminForm
- invalidate_dashboard
- Centralized test commands and result layout
- README.md

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

## Communities (39 total, 18 thin omitted)

### Community 0 - "main.tsx"
Cohesion: 0.07
Nodes (78): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, categories, csrf() (+70 more)

### Community 1 - "Complaint"
Cohesion: 0.09
Nodes (19): options(), process_import(), Command, Command, Command, Command, Bureau, CaseAction (+11 more)

### Community 2 - "Coordination - AICTE 26264"
Cohesion: 0.05
Nodes (44): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Action-first deadline and bureau-coordination dashboard, Immutable allegations and append-only corrections and audit history, PostgreSQL dump and private-files backup and restore, Complaint monitoring and cross-bureau coordination prototype, Coordination - AICTE 26264, Human overlap review, transfer and independent case histories (+36 more)

### Community 3 - "WorkflowTests"
Cohesion: 0.06
Nodes (5): evaluation_dataset(), seed_records(), submit(), EvaluationTests, WorkflowTests

### Community 4 - "api.py"
Cohesion: 0.11
Nodes (25): current_bureau_id(), writable(), actions(), case_detail(), cases(), replay(), Conflict, download() (+17 more)

### Community 5 - "test_workflow.py"
Cohesion: 0.07
Nodes (8): Migration, Migration, Migration, Migration, Migration, Migration, Migration, InstitutionMigrationTests

### Community 6 - "imports.py"
Cohesion: 0.12
Nodes (25): authorized_file(), build_export(), export_detail(), export_download(), exports(), get_export(), query(), safe() (+17 more)

### Community 7 - "matching.py"
Cohesion: 0.11
Nodes (18): Command, Command, Command, refresh_active_matches(), swap_release(), baseline_runtime(), cached_encoder(), cached_tokenizer() (+10 more)

### Community 8 - "package.json"
Cohesion: 0.06
Nodes (30): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+22 more)

### Community 9 - "ImportTests"
Cohesion: 0.13
Nodes (5): cell(), parse_file(), DashboardTests, ImportTests, RolloutTests

### Community 10 - "institutions.py"
Cohesion: 0.19
Nodes (21): coordination(), filtered_cases(), role(), scoped_cases(), compute_dashboard(), dashboard(), dashboard_data(), overlaps() (+13 more)

### Community 11 - "collect_training_data.py"
Cohesion: 0.15
Nodes (8): main(), redact(), sql_values(), main(), download(), main(), synthetic(), main()

### Community 12 - "json"
Cohesion: 0.16
Nodes (8): browser(), main(), request(), simulate(), main(), simulate(), docker(), main()

### Community 13 - "train_matching.py"
Cohesion: 0.17
Nodes (14): evaluate(), main(), save(), seed(), train_epoch(), vectors(), epoch(), export() (+6 more)

### Community 15 - "institutions.spec.ts"
Cohesion: 0.16
Nodes (4): createInstitution(), csrf(), post(), stamp

### Community 16 - "compare_fresh_models.py"
Cohesion: 0.21
Nodes (5): education_pairs(), main(), summarize(), unseen(), FreshComparisonTests

### Community 17 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 18 - "prepare_public_pairs.py"
Cohesion: 0.30
Nodes (7): clean_training(), download(), main(), normalized(), split_dev(), texts(), PublicDataTests

### Community 20 - "evaluate_matching.py"
Cohesion: 0.29
Nodes (4): calibrate(), Command, metrics(), measured()

### Community 21 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 24 - "compilerOptions"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

## Knowledge Gaps
- **89 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 246 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `Complaint`, `api.py`, `imports.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `filtered_cases()` connect `institutions.py` to `imports.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `InstitutionTests` (e.g. with `AuditEvent` and `CaseAction`) actually correct?**
  _`InstitutionTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _89 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.070446735395189 - nodes in this community are weakly interconnected._
- **Should `Complaint` be split into smaller, more focused modules?**
  _Cohesion score 0.09014675052410902 - nodes in this community are weakly interconnected._