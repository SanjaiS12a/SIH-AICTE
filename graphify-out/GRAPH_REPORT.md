# Graph Report - SIH  (2026-10-31)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 966 nodes · 2722 edges · 56 communities (33 shown, 23 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 277 edges (avg confidence: 0.93)
- Token cost: structural extraction 0; host semantic extraction usage unavailable.

## Graph Freshness
- Built from commit: `b992600f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main.tsx
- imports.py
- WorkflowTests
- django_db
- completion.spec.ts
- Coordination - AICTE 26264
- api.py
- pathlib
- models.py
- package.json
- matching.py
- analytics.py
- CaseAction
- InstitutionTests
- EscalationTests
- coordination_workflow.py
- Institution
- train_matching.py
- CoordinationCompletionTests
- collect_training_data.py
- Phase2Tests
- exports.py
- prepare_public_pairs.py
- compilerOptions
- django_conf
- demo_data.py
- model_release.py
- serializers.py
- evaluate
- Backend Python requirements
- train_public_paraphrase.py
- main
- sys
- Complaint monitoring and cross-bureau coordination prototype
- verify_delivery.py
- monitor_resources.py
- apps.py
- InstitutionAdmin
- Validation-selected MiniLM contrastive experiments
- compilerOptions
- ReadOnlyAdmin
- Command
- InstitutionAdminForm
- InstitutionMigrationTests
- Centralized test commands and result layout
- Checksum-verified public data and non-executing SQL audit
- README.md

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 53 edges
2. `WorkflowTests` - 51 edges
3. `Institution` - 47 edges
4. `Coordination - AICTE 26264` - 45 edges
5. `CaseAction` - 38 edges
6. `role()` - 32 edges
7. `scoped_cases()` - 32 edges
8. `ErrorBox()` - 31 edges
9. `InstitutionTests` - 28 edges
10. `Shell()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `RolloutTests` --uses--> `Complaint`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `ModelRelease`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `OverlapCandidate`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `RolloutTests` --uses--> `StagedEmbedding`  [INFERRED]
  tests/backend/test_imports.py → backend/cases/models.py
- `Phase2MigrationTests` --uses--> `CaseAction`  [INFERRED]
  tests/backend/test_phase2.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (56 total, 23 thin omitted)

### Community 0 - "main.tsx"
Cohesion: 0.06
Nodes (110): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, categories, classifications (+102 more)

### Community 1 - "imports.py"
Cohesion: 0.08
Nodes (29): chunks(), safe(), accessible_jobs(), cell(), digest(), get_job(), import_detail(), import_errors() (+21 more)

### Community 2 - "WorkflowTests"
Cohesion: 0.05
Nodes (5): CoordinationConcurrencyTests, CoordinationWorkflowTests, EscalationConcurrencyTests, submit(), WorkflowTests

### Community 3 - "django_db"
Cohesion: 0.11
Nodes (8): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration

### Community 4 - "completion.spec.ts"
Cohesion: 0.08
Nodes (21): makeCase(), makeInstitution(), post(), stamp, token(), post(), stamp, token() (+13 more)

### Community 5 - "Coordination - AICTE 26264"
Cohesion: 0.05
Nodes (38): Accountable cross-Bureau coordination with designated lead and tasks, Action-first deadline and bureau-coordination dashboard, PostgreSQL dump and private-files backup and restore, Audited case classification with backward-compatible Unclassified default, Coordination - AICTE 26264, Current-membership officer instruction inbox without other-case evidence, Audited responsibility revisions reset acknowledgment, Human overlap review, transfer and independent case histories (+30 more)

### Community 6 - "api.py"
Cohesion: 0.12
Nodes (13): current_bureau_id(), dashboard(), download(), notifications(), overlap_data(), overlap_queryset(), overlaps(), report() (+5 more)

### Community 7 - "pathlib"
Cohesion: 0.11
Nodes (8): browser(), main(), request(), simulate(), main(), simulate(), docker(), main()

### Community 8 - "models.py"
Cohesion: 0.12
Nodes (13): Command, Command, Command, Bureau, Complaint, Membership, Meta, ModelRelease (+5 more)

### Community 9 - "package.json"
Cohesion: 0.06
Nodes (29): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+21 more)

### Community 10 - "matching.py"
Cohesion: 0.14
Nodes (13): Command, Command, baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch(), match_case() (+5 more)

### Community 11 - "analytics.py"
Cohesion: 0.13
Nodes (15): filtered_cases(), action_query(), analytics(), Meta, movements(), movements_csv(), chunks(), MovementSerializer (+7 more)

### Community 12 - "CaseAction"
Cohesion: 0.21
Nodes (18): scoped_cases(), writable(), actions(), cases(), replay(), Conflict, upload(), case_escalations() (+10 more)

### Community 15 - "coordination_workflow.py"
Cohesion: 0.23
Nodes (18): page(), audit(), detail(), history(), Meta, OpenInput, ParticipantInput, ParticipantSerializer (+10 more)

### Community 16 - "Institution"
Cohesion: 0.26
Nodes (14): institutions(), detail(), history(), institution_cases(), InstitutionHistorySerializer, InstitutionProfileSerializer, InstitutionWriteSerializer, Meta (+6 more)

### Community 17 - "train_matching.py"
Cohesion: 0.18
Nodes (5): main(), save(), seed(), train_epoch(), vectors()

### Community 19 - "collect_training_data.py"
Cohesion: 0.22
Nodes (8): main(), redact(), sql_values(), main(), download(), main(), synthetic(), main()

### Community 21 - "exports.py"
Cohesion: 0.25
Nodes (12): coordination(), role(), options(), authorized_file(), build_export(), export_detail(), export_download(), exports() (+4 more)

### Community 22 - "prepare_public_pairs.py"
Cohesion: 0.28
Nodes (7): clean_training(), download(), main(), normalized(), split_dev(), texts(), PublicDataTests

### Community 23 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 24 - "django_conf"
Cohesion: 0.13
Nodes (4): Command, Migration, Migration, Phase2MigrationTests

### Community 25 - "demo_data.py"
Cohesion: 0.20
Nodes (3): evaluation_dataset(), seed_records(), EvaluationTests

### Community 26 - "model_release.py"
Cohesion: 0.25
Nodes (4): Command, refresh_active_matches(), swap_release(), StagedEmbedding

### Community 27 - "serializers.py"
Cohesion: 0.27
Nodes (7): case_detail(), Attachment, ActionReadSerializer, ActionSerializer, AttachmentSerializer, Meta, ReviewSerializer

### Community 28 - "evaluate"
Cohesion: 0.27
Nodes (6): calibrate(), Command, metrics(), evaluate(), measured(), main()

### Community 29 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

### Community 30 - "train_public_paraphrase.py"
Cohesion: 0.36
Nodes (7): epoch(), export(), load(), main(), pair_scores(), save(), seed()

### Community 31 - "main"
Cohesion: 0.31
Nodes (5): education_pairs(), main(), summarize(), unseen(), FreshComparisonTests

### Community 33 - "Complaint monitoring and cross-bureau coordination prototype"
Cohesion: 0.22
Nodes (9): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Immutable allegations and append-only corrections and audit history, Complaint monitoring and cross-bureau coordination prototype, Private validated evidence uploads and forced downloads, 30-calendar-day demo deadline and reminder bands, Current-bureau access and coordinator-only coordination actions, Separate monthly flows and single-date snapshots (+1 more)

### Community 34 - "verify_delivery.py"
Cohesion: 0.46
Nodes (5): digest(), main(), run(), shell(), snapshot()

### Community 35 - "monitor_resources.py"
Cohesion: 0.38
Nodes (3): main(), Memory, ticks()

### Community 38 - "Validation-selected MiniLM contrastive experiments"
Cohesion: 0.50
Nodes (5): Validation-selected MiniLM contrastive experiments, Incident-separated synthetic matching calibration and evaluation, all-MiniLM-L6-v2 sentence embedding model, Approved model staging, atomic activation and rollback, Institution-scoped semantic matching

### Community 39 - "compilerOptions"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

## Knowledge Gaps
- **113 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+108 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 323 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `imports.py`, `models.py`, `CaseAction`, `Institution`, `demo_data.py`, `serializers.py`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `filtered_cases()` connect `analytics.py` to `Institution`, `imports.py`, `CaseAction`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _113 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.0579647917561185 - nodes in this community are weakly interconnected._
- **Should `imports.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0777323202805377 - nodes in this community are weakly interconnected._
- **Should `WorkflowTests` be split into smaller, more focused modules?**
  _Cohesion score 0.05200501253132832 - nodes in this community are weakly interconnected._