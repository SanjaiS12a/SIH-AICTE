# Graph Report - SIH  (2026-10-30)

## Corpus Check
- 65 supported files · approximately 23,844 words. Data, models, uploads and secrets are excluded.

## Summary
- 553 nodes · 1391 edges · 21 communities (10 shown, 11 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 147 edges (avg confidence: 0.94)
- Token accounting: structural AST uses no model tokens; host document-extraction usage is unavailable. No estimated cost is claimed.

## Community Hubs (Navigation)
- imports.py
- matching.py
- main.tsx
- api.py
- package.json
- train_matching.py
- WorkflowTests
- Coordination - AICTE 26264
- collect_training_data.py
- ImportTests
- compilerOptions
- Backend Python requirements
- apps.py
- ReadOnlyAdmin

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 46 edges
2. `WorkflowTests` - 41 edges
3. `Institution` - 29 edges
4. `ImportTests` - 22 edges
5. `Coordination - AICTE 26264` - 22 edges
6. `CaseAction` - 19 edges
7. `Bureau` - 19 edges
8. `role()` - 18 edges
9. `AuditEvent` - 17 edges
10. `OverlapCandidate` - 17 edges

## Surprising Connections (you probably didn't know these)
- `CSRF-protected Coordination sign-in form` --implements--> `Complaint monitoring and cross-bureau coordination prototype`  [INFERRED]
  backend/templates/registration/login.html → README.md
- `Coordination frontend HTML entrypoint` --implements--> `Complaint monitoring and cross-bureau coordination prototype`  [INFERRED]
  frontend/index.html → README.md
- `Django Q2 worker service` --implements--> `Django Q2 durable task worker`  [INFERRED]
  compose.yaml → backend/requirements.txt
- `ImportTests` --uses--> `Complaint`  [INFERRED]
  backend/cases/test_imports.py → backend/cases/models.py
- `ImportTests` --uses--> `ImportJob`  [INFERRED]
  backend/cases/test_imports.py → backend/cases/models.py

## Import Cycles
- None detected.

## Communities (21 total, 11 thin omitted)

### Community 0 - "imports.py"
Cohesion: 0.06
Nodes (35): accessible_jobs(), cell(), imports(), job_data(), parse_file(), process_import(), process_import_matching(), summary_data() (+27 more)

### Community 1 - "matching.py"
Cohesion: 0.05
Nodes (25): Command, Command, refresh_active_matches(), baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch() (+17 more)

### Community 2 - "main.tsx"
Cohesion: 0.07
Nodes (63): api(), Attachment, Case, CaseAction, CaseDetail, categories, csrf(), Dashboard (+55 more)

### Community 3 - "api.py"
Cohesion: 0.07
Nodes (53): coordination(), filtered_cases(), role(), scoped_cases(), writable(), actions(), case_detail(), cases() (+45 more)

### Community 4 - "package.json"
Cohesion: 0.05
Nodes (31): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+23 more)

### Community 5 - "train_matching.py"
Cohesion: 0.08
Nodes (13): evaluation_dataset(), seed_records(), calibrate(), Command, metrics(), EvaluationTests, main(), evaluate() (+5 more)

### Community 7 - "Coordination - AICTE 26264"
Cohesion: 0.08
Nodes (31): CSRF-protected Coordination sign-in form, Coordination frontend HTML entrypoint, Action-first deadline and bureau-coordination dashboard, Immutable allegations and append-only corrections and audit history, PostgreSQL dump and private-files backup and restore, Complaint monitoring and cross-bureau coordination prototype, Coordination - AICTE 26264, Human overlap review, transfer and independent case histories (+23 more)

### Community 8 - "collect_training_data.py"
Cohesion: 0.13
Nodes (8): Migration, main(), redact(), sql_values(), main(), download(), main(), synthetic()

### Community 10 - "compilerOptions"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 11 - "Backend Python requirements"
Cohesion: 0.27
Nodes (10): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Shared local offline MiniLM model files (+2 more)

## Knowledge Gaps
- **66 isolated node(s):** `Migration`, `Migration`, `Migration`, `Attachment`, `CaseAction` (+61 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 187 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `WorkflowTests` to `imports.py`, `api.py`, `train_matching.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ImportTests` (e.g. with `Complaint` and `ImportJob`) actually correct?**
  _`ImportTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _66 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `imports.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06478578892371996 - nodes in this community are weakly interconnected._
- **Should `matching.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0502497796062298 - nodes in this community are weakly interconnected._
- **Should `main.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.07006151742993848 - nodes in this community are weakly interconnected._
## Evidence and health limits

Source lines in README were refreshed for the action-first dashboard and safe report polling. Implementation bridges are INFERRED. The post-build graph has one self-loop and no missing/dangling endpoints; it cannot recover relationships lost before construction. CSS/unsupported configuration files are not fully represented. Source code and tests remain authoritative.
