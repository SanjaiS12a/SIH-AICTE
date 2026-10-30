# Graph Report - SIH  (2026-10-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 643 nodes · 1703 edges · 29 communities (13 shown, 16 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 178 edges (avg confidence: 0.94)
- Token cost: structural extraction uses zero model tokens; host semantic extraction usage is unavailable and is not estimated.

## Graph Freshness
- Built from source commit: `f3036059`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.tsx
- api.py
- imports.py
- package.json
- Coordination - AICTE 26264
- train_matching.py
- WorkflowTests
- collect_training_data.py
- ImportTests
- InstitutionTests
- matching.py
- django_db
- commands/benchmark_scale.py
- compilerOptions
- benchmark_import.py
- signals.py
- tokenizer
- Backend Python requirements
- InstitutionAdmin
- Command
- InstitutionAdminForm
- InstitutionMigrationTests

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 48 edges
2. `Institution` - 42 edges
3. `WorkflowTests` - 41 edges
4. `Coordination - AICTE 26264` - 30 edges
5. `InstitutionTests` - 26 edges
6. `CaseAction` - 24 edges
7. `role()` - 23 edges
8. `ImportTests` - 22 edges
9. `AuditEvent` - 21 edges
10. `scoped_cases()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `CSRF-protected Coordination sign-in form` --implements--> `Complaint monitoring and cross-bureau coordination prototype`  [INFERRED]
  backend/templates/registration/login.html → README.md
- `Coordination frontend HTML entrypoint` --implements--> `Complaint monitoring and cross-bureau coordination prototype`  [INFERRED]
  frontend/index.html → README.md
- `Django Q2 worker service` --implements--> `Django Q2 durable task worker`  [INFERRED]
  compose.yaml → backend/requirements.txt
- `DashboardTests` --uses--> `CaseAction`  [INFERRED]
  backend/cases/test_imports.py → backend/cases/models.py
- `DashboardTests` --uses--> `Institution`  [INFERRED]
  backend/cases/test_imports.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (29 total, 16 thin omitted)

### Community 0 - "main.tsx"
Cohesion: 0.07
Nodes (79): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, categories, csrf() (+71 more)

### Community 1 - "api.py"
Cohesion: 0.07
Nodes (57): coordination(), current_bureau_id(), filtered_cases(), role(), scoped_cases(), writable(), actions(), case_detail() (+49 more)

### Community 2 - "imports.py"
Cohesion: 0.07
Nodes (40): ReadOnlyAdmin, chunks(), build_export(), safe(), scope_hash(), accessible_jobs(), cell(), digest() (+32 more)

### Community 3 - "package.json"
Cohesion: 0.05
Nodes (33): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+25 more)

### Community 4 - "Coordination - AICTE 26264"
Cohesion: 0.06
Nodes (39): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Action-first deadline and bureau-coordination dashboard, Immutable allegations and append-only corrections and audit history, PostgreSQL dump and private-files backup and restore, Complaint monitoring and cross-bureau coordination prototype, Coordination - AICTE 26264, Human overlap review, transfer and independent case histories (+31 more)

### Community 5 - "train_matching.py"
Cohesion: 0.08
Nodes (13): evaluation_dataset(), seed_records(), calibrate(), Command, metrics(), EvaluationTests, main(), evaluate() (+5 more)

### Community 7 - "collect_training_data.py"
Cohesion: 0.12
Nodes (9): Command, Migration, main(), redact(), sql_values(), main(), download(), main() (+1 more)

### Community 10 - "matching.py"
Cohesion: 0.21
Nodes (9): refresh_active_matches(), baseline_runtime(), cached_encoder(), encoder(), match_batch(), match_case(), revision(), runtime() (+1 more)

### Community 11 - "django_db"
Cohesion: 0.13
Nodes (6): Migration, Migration, Migration, Migration, Migration, Migration

### Community 13 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 15 - "benchmark_import.py"
Cohesion: 0.29
Nodes (6): browser(), main(), request(), simulate(), docker(), main()

### Community 17 - "tokenizer"
Cohesion: 0.22
Nodes (4): Command, cached_tokenizer(), ModelUnavailable, tokenizer()

### Community 18 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

## Knowledge Gaps
- **79 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 222 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `api.py`, `imports.py`, `train_matching.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `filtered_cases()` connect `api.py` to `imports.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `InstitutionTests` (e.g. with `AuditEvent` and `CaseAction`) actually correct?**
  _`InstitutionTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _79 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06942983378918578 - nodes in this community are weakly interconnected._
- **Should `api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06825619448340346 - nodes in this community are weakly interconnected._