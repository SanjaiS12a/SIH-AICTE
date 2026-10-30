# Graph Report - SIH  (2026-10-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 613 nodes · 1569 edges · 36 communities (19 shown, 17 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 171 edges (avg confidence: 0.94)
- Token cost: structural extraction uses zero model tokens; host semantic extraction usage is unavailable and is not estimated.

## Graph Freshness
- Built from source commit: `0f51b3c5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- imports.py
- main.tsx
- package.json
- WorkflowTests
- Coordination - AICTE 26264
- api.py
- django_db
- InstitutionTests
- tests.py
- Institution
- train_matching.py
- matching.py
- ImportTests
- collect_training_data.py
- Complaint
- benchmark_import.py
- seed_demo.py
- compilerOptions
- commands/benchmark_scale.py
- models.py
- evaluate_matching.py
- Backend Python requirements
- time
- apps.py
- InstitutionAdmin
- DashboardTests
- ReadOnlyAdmin
- InstitutionAdminForm

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 48 edges
2. `Institution` - 42 edges
3. `WorkflowTests` - 41 edges
4. `InstitutionTests` - 26 edges
5. `Coordination - AICTE 26264` - 26 edges
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
- `Command` --uses--> `Complaint`  [INFERRED]
  backend/cases/management/commands/runtime_report.py → backend/cases/models.py
- `Command` --uses--> `Complaint`  [INFERRED]
  backend/cases/management/commands/benchmark_scale.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (36 total, 17 thin omitted)

### Community 0 - "imports.py"
Cohesion: 0.07
Nodes (60): coordination(), current_bureau_id(), filtered_cases(), role(), scoped_cases(), writable(), actions(), cases() (+52 more)

### Community 1 - "main.tsx"
Cohesion: 0.07
Nodes (63): api(), Attachment, Case, CaseAction, CaseDetail, categories, csrf(), Dashboard (+55 more)

### Community 2 - "package.json"
Cohesion: 0.05
Nodes (31): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+23 more)

### Community 3 - "WorkflowTests"
Cohesion: 0.08
Nodes (3): submit(), EvaluationTests, WorkflowTests

### Community 4 - "Coordination - AICTE 26264"
Cohesion: 0.07
Nodes (35): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Action-first deadline and bureau-coordination dashboard, Immutable allegations and append-only corrections and audit history, PostgreSQL dump and private-files backup and restore, Complaint monitoring and cross-bureau coordination prototype, Coordination - AICTE 26264, Human overlap review, transfer and independent case histories (+27 more)

### Community 5 - "api.py"
Cohesion: 0.14
Nodes (16): case_detail(), compute_dashboard(), institutions(), notifications(), overlap_data(), review(), upload(), Attachment (+8 more)

### Community 6 - "django_db"
Cohesion: 0.10
Nodes (7): Migration, Migration, Migration, Migration, Migration, Migration, Migration

### Community 8 - "tests.py"
Cohesion: 0.19
Nodes (4): Membership, Notification, send_reminders(), ConcurrentSubmissionTests

### Community 9 - "Institution"
Cohesion: 0.11
Nodes (7): Command, Command, Bureau, Institution, CreateCaseSerializer, invalidate_dashboard(), InstitutionMigrationTests

### Community 10 - "train_matching.py"
Cohesion: 0.16
Nodes (6): main(), main(), save(), seed(), train_epoch(), vectors()

### Community 11 - "matching.py"
Cohesion: 0.20
Nodes (12): Command, baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch(), match_case(), ModelUnavailable (+4 more)

### Community 13 - "collect_training_data.py"
Cohesion: 0.19
Nodes (7): main(), redact(), sql_values(), main(), download(), main(), synthetic()

### Community 14 - "Complaint"
Cohesion: 0.22
Nodes (8): Command, refresh_active_matches(), swap_release(), Complaint, Meta, ModelRelease, StagedEmbedding, RolloutTests

### Community 15 - "benchmark_import.py"
Cohesion: 0.21
Nodes (6): browser(), main(), request(), simulate(), docker(), main()

### Community 16 - "seed_demo.py"
Cohesion: 0.20
Nodes (3): evaluation_dataset(), seed_records(), Command

### Community 17 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 19 - "models.py"
Cohesion: 0.31
Nodes (4): Command, ImportRow, OverlapCandidate, SummaryRecord

### Community 20 - "evaluate_matching.py"
Cohesion: 0.29
Nodes (4): calibrate(), Command, metrics(), evaluate()

### Community 21 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

## Knowledge Gaps
- **74 isolated node(s):** `Meta`, `Migration`, `Migration`, `Migration`, `Migration` (+69 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 212 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `imports.py`, `api.py`, `tests.py`, `Institution`, `Complaint`, `models.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `InstitutionTests` (e.g. with `AuditEvent` and `CaseAction`) actually correct?**
  _`InstitutionTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Meta`, `Migration`, `Migration` to the rest of the system?**
  _74 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `imports.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07058823529411765 - nodes in this community are weakly interconnected._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.07006151742993848 - nodes in this community are weakly interconnected._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._