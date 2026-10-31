# Graph Report - SIH  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 810 nodes · 2130 edges · 35 communities (18 shown, 17 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 215 edges (avg confidence: 0.93)
- Token cost: structural extraction 0; host semantic extraction usage unavailable.

## Graph Freshness
- Built from commit: `266bd671`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api.py
- main.tsx
- matching.py
- models.py
- Coordination - AICTE 26264
- WorkflowTests
- ImportTests
- escalations.spec.ts
- package.json
- InstitutionTests
- EscalationTests
- collect_training_data.py
- train_matching.py
- Phase2Tests
- compilerOptions
- compare_fresh_models.py
- prepare_public_pairs.py
- signals.py
- Backend Python requirements
- train_public_paraphrase.py
- evaluate
- InstitutionAdmin
- compilerOptions
- ReadOnlyAdmin
- InstitutionAdminForm
- Centralized test commands and result layout
- README.md

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 49 edges
2. `WorkflowTests` - 46 edges
3. `Coordination - AICTE 26264` - 40 edges
4. `Institution` - 39 edges
5. `InstitutionTests` - 28 edges
6. `CaseAction` - 26 edges
7. `role()` - 26 edges
8. `scoped_cases()` - 25 edges
9. `ImportTests` - 23 edges
10. `EscalationTests` - 22 edges

## Surprising Connections (you probably didn't know these)
- `RolloutTests` --uses--> `Complaint`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `ModelRelease`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `OverlapCandidate`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `EscalationTests` --uses--> `Escalation`  [INFERRED]
  tests/backend/test_escalations.py → backend/cases/models.py
- `EscalationTests` --uses--> `Membership`  [INFERRED]
  tests/backend/test_escalations.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (35 total, 17 thin omitted)

### Community 0 - "api.py"
Cohesion: 0.05
Nodes (93): coordination(), current_bureau_id(), filtered_cases(), role(), scoped_cases(), writable(), actions(), case_detail() (+85 more)

### Community 1 - "main.tsx"
Cohesion: 0.07
Nodes (87): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, categories, classifications (+79 more)

### Community 2 - "matching.py"
Cohesion: 0.05
Nodes (25): process_import_matching(), Command, Command, refresh_active_matches(), Command, baseline_runtime(), cached_encoder(), cached_tokenizer() (+17 more)

### Community 3 - "models.py"
Cohesion: 0.05
Nodes (17): evaluation_dataset(), seed_records(), Command, Migration, Migration, Migration, Migration, Migration (+9 more)

### Community 4 - "Coordination - AICTE 26264"
Cohesion: 0.05
Nodes (49): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Action-first deadline and bureau-coordination dashboard, Immutable allegations and append-only corrections and audit history, PostgreSQL dump and private-files backup and restore, Audited case classification with backward-compatible Unclassified default, Complaint monitoring and cross-bureau coordination prototype, Coordination - AICTE 26264 (+41 more)

### Community 5 - "WorkflowTests"
Cohesion: 0.07
Nodes (3): EscalationConcurrencyTests, submit(), WorkflowTests

### Community 6 - "ImportTests"
Cohesion: 0.11
Nodes (9): process_import(), Command, swap_release(), ImportJob, StagedEmbedding, SummaryRecord, DashboardTests, ImportTests (+1 more)

### Community 7 - "escalations.spec.ts"
Cohesion: 0.10
Nodes (13): createCase(), csrf(), escalate(), post(), stamp, createInstitution(), csrf(), post() (+5 more)

### Community 8 - "package.json"
Cohesion: 0.06
Nodes (29): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+21 more)

### Community 11 - "collect_training_data.py"
Cohesion: 0.18
Nodes (8): main(), redact(), sql_values(), main(), download(), main(), synthetic(), main()

### Community 12 - "train_matching.py"
Cohesion: 0.18
Nodes (6): main(), save(), seed(), train_epoch(), vectors(), main()

### Community 14 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 15 - "compare_fresh_models.py"
Cohesion: 0.23
Nodes (5): education_pairs(), main(), summarize(), unseen(), FreshComparisonTests

### Community 16 - "prepare_public_pairs.py"
Cohesion: 0.30
Nodes (7): clean_training(), download(), main(), normalized(), split_dev(), texts(), PublicDataTests

### Community 18 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 19 - "train_public_paraphrase.py"
Cohesion: 0.36
Nodes (7): epoch(), export(), load(), main(), pair_scores(), save(), seed()

### Community 20 - "evaluate"
Cohesion: 0.31
Nodes (5): calibrate(), Command, metrics(), evaluate(), measured()

### Community 22 - "compilerOptions"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

## Knowledge Gaps
- **99 isolated node(s):** `Meta`, `Meta`, `Migration`, `Migration`, `Migration` (+94 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 274 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `api.py`, `models.py`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `InstitutionTests` (e.g. with `AuditEvent` and `CaseAction`) actually correct?**
  _`InstitutionTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Meta`, `Meta`, `Migration` to the rest of the system?**
  _99 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api.py` be split into smaller, more focused modules?**
  _Cohesion score 0.051842972729997 - nodes in this community are weakly interconnected._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06506965681277607 - nodes in this community are weakly interconnected._
- **Should `matching.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05194805194805195 - nodes in this community are weakly interconnected._