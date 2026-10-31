# Graph Report - SIH  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1040 nodes · 2950 edges · 48 communities (28 shown, 20 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 295 edges (avg confidence: 0.93)
- Token cost: structural extraction 0; host semantic extraction usage unavailable.

## Graph Freshness
- Built from commit: `889e55f7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.tsx
- models.py
- WorkflowTests
- source-intake.spec.ts
- imports.py
- exports.py
- Coordination - AICTE 26264
- matching.py
- coordination_workflow.py
- json
- package.json
- ImportTests
- compare_fresh_models.py
- train_matching.py
- Institution
- CaseAction
- api.py
- collect_training_data.py
- InstitutionTests
- CoordinationCompletionTests
- commands/benchmark_scale.py
- Phase2Tests
- compilerOptions
- SourceIntakeTests
- monitor_resources.py
- verify_delivery.py
- Backend Python requirements
- CaseSerializer
- Complaint monitoring and cross-bureau coordination prototype
- Fictional independent Bureau inputs
- apps.py
- InstitutionAdmin
- Validation-selected MiniLM contrastive experiments
- compilerOptions
- ReadOnlyAdmin
- Command
- InstitutionAdminForm
- Centralized test commands and result layout
- Checksum-verified public data and non-executing SQL audit
- tests/README.md

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 54 edges
2. `Coordination - AICTE 26264` - 52 edges
3. `WorkflowTests` - 51 edges
4. `Institution` - 47 edges
5. `CaseAction` - 42 edges
6. `role()` - 35 edges
7. `ErrorBox()` - 35 edges
8. `scoped_cases()` - 35 edges
9. `Shell()` - 30 edges
10. `usePoll()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `RolloutTests` --uses--> `Complaint`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `ImportJob`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `ModelRelease`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `OverlapCandidate`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `StagedEmbedding`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (48 total, 20 thin omitted)

### Community 0 - "main.tsx"
Cohesion: 0.05
Nodes (120): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, categories, classifications (+112 more)

### Community 1 - "models.py"
Cohesion: 0.05
Nodes (18): evaluation_dataset(), seed_records(), Command, Migration, Migration, Migration, Migration, Migration (+10 more)

### Community 2 - "WorkflowTests"
Cohesion: 0.05
Nodes (7): Notification, notify_escalation(), send_reminders(), EscalationConcurrencyTests, EscalationTests, submit(), WorkflowTests

### Community 3 - "source-intake.spec.ts"
Cohesion: 0.06
Nodes (31): makeCase(), makeInstitution(), post(), stamp, token(), post(), stamp, token() (+23 more)

### Community 4 - "imports.py"
Cohesion: 0.13
Nodes (36): current_bureau_id(), role(), writable(), actions(), cases(), options(), session(), accessible_jobs() (+28 more)

### Community 5 - "exports.py"
Cohesion: 0.10
Nodes (26): coordination(), filtered_cases(), action_query(), analytics(), Meta, movements(), movements_csv(), chunks() (+18 more)

### Community 6 - "Coordination - AICTE 26264"
Cohesion: 0.05
Nodes (44): Accountable cross-Bureau coordination with designated lead and tasks, Action-first deadline and bureau-coordination dashboard, PostgreSQL dump and private-files backup and restore, Audited case classification with backward-compatible Unclassified default, Coordination - AICTE 26264, Current-membership officer instruction inbox without other-case evidence, Audited responsibility revisions reset acknowledgment, Human overlap review, transfer and independent case histories (+36 more)

### Community 7 - "matching.py"
Cohesion: 0.09
Nodes (19): Command, Command, Command, Command, refresh_active_matches(), swap_release(), baseline_runtime(), cached_encoder() (+11 more)

### Community 8 - "coordination_workflow.py"
Cohesion: 0.11
Nodes (20): audit(), detail(), history(), Meta, OpenInput, ParticipantInput, ParticipantSerializer, records() (+12 more)

### Community 9 - "json"
Cohesion: 0.11
Nodes (8): browser(), main(), request(), simulate(), main(), simulate(), docker(), main()

### Community 10 - "package.json"
Cohesion: 0.06
Nodes (29): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+21 more)

### Community 11 - "ImportTests"
Cohesion: 0.13
Nodes (5): cell(), parse_file(), DashboardTests, ImportTests, RolloutTests

### Community 12 - "compare_fresh_models.py"
Cohesion: 0.14
Nodes (12): education_pairs(), main(), summarize(), unseen(), clean_training(), download(), main(), normalized() (+4 more)

### Community 13 - "train_matching.py"
Cohesion: 0.14
Nodes (17): calibrate(), metrics(), evaluate(), main(), save(), seed(), train_epoch(), vectors() (+9 more)

### Community 14 - "Institution"
Cohesion: 0.15
Nodes (19): institutions(), page(), detail(), history(), institution_cases(), InstitutionHistorySerializer, InstitutionProfileSerializer, InstitutionWriteSerializer (+11 more)

### Community 15 - "CaseAction"
Cohesion: 0.16
Nodes (18): Conflict, overlap_queryset(), case_escalations(), CreateEscalationSerializer, EscalationSerializer, Meta, queue(), records() (+10 more)

### Community 16 - "api.py"
Cohesion: 0.16
Nodes (14): scoped_cases(), case_detail(), download(), notifications(), overlap_data(), overlaps(), report(), chunks() (+6 more)

### Community 17 - "collect_training_data.py"
Cohesion: 0.16
Nodes (8): main(), redact(), sql_values(), main(), download(), main(), synthetic(), main()

### Community 20 - "commands/benchmark_scale.py"
Cohesion: 0.15
Nodes (6): dashboard(), dashboard_data(), Command, simulate(), OverlapCandidate, invalidate_dashboard()

### Community 22 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 24 - "monitor_resources.py"
Cohesion: 0.22
Nodes (3): main(), Memory, ticks()

### Community 25 - "verify_delivery.py"
Cohesion: 0.40
Nodes (7): digest(), main(), run(), shell(), snapshot(), main(), snapshot()

### Community 26 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 27 - "CaseSerializer"
Cohesion: 0.25
Nodes (5): replay(), CaseSerializer, Meta, rows(), RowSerializer

### Community 28 - "Complaint monitoring and cross-bureau coordination prototype"
Cohesion: 0.22
Nodes (9): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Immutable allegations and append-only corrections and audit history, Complaint monitoring and cross-bureau coordination prototype, Private validated evidence uploads and forced downloads, 30-calendar-day demo deadline and reminder bands, Current-bureau access and coordinator-only coordination actions, Separate monthly flows and single-date snapshots (+1 more)

### Community 29 - "Fictional independent Bureau inputs"
Cohesion: 0.33
Nodes (5): Source update conflict without portal overwrite, Synthetic Bureau inputs, not genuine AICTE records, Repeat upload without extra complaints, Repeatable fictional three-Bureau source demonstration, Fictional independent Bureau inputs

### Community 32 - "Validation-selected MiniLM contrastive experiments"
Cohesion: 0.50
Nodes (5): Validation-selected MiniLM contrastive experiments, Incident-separated synthetic matching calibration and evaluation, all-MiniLM-L6-v2 sentence embedding model, Approved model staging, atomic activation and rollback, Institution-scoped semantic matching

### Community 33 - "compilerOptions"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

## Knowledge Gaps
- **130 isolated node(s):** `Meta`, `Meta`, `Meta`, `SourceSerializer`, `Attachment` (+125 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 350 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `process_import()` connect `imports.py` to `api.py`, `CaseAction`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `filtered_cases()` connect `exports.py` to `api.py`, `imports.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `ImportTests` connect `ImportTests` to `WorkflowTests`, `imports.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Meta`, `Meta`, `Meta` to the rest of the system?**
  _130 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05478948336091193 - nodes in this community are weakly interconnected._
- **Should `models.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05225718194254446 - nodes in this community are weakly interconnected._