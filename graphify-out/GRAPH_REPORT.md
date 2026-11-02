# Graph Report - SIH  (2026-11-02)

## Corpus Check
- 149 files · ~82,072 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1413 nodes · 3554 edges · 93 communities (42 shown, 51 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 317 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Browser Workflow Coverage
- Case Intelligence
- Independent Research Review
- Case Intelligence
- Frozen Model Matching
- Escalation Readiness Tests
- Coordination Workflows
- Typed API Components
- Independent Restore Verification
- Import Performance Measurement
- Source Intake Interface
- Technical Design Boundaries
- Database Schema Migrations
- Case Intelligence
- Import Validation Tests
- Frontend Package Configuration
- Institution Profile Interface
- Durable Source Intake
- Pinned Model Release
- Institution Registry Administration
- Institution Permission Tests
- Escalation Readiness Tests
- Complaint Import Interface
- Coordination Workflows
- Evidence Transaction Tests
- Durable Source Intake
- Escalation Readiness Tests
- Case Intelligence
- Coordination Completion Tests
- Serialization And Escalation
- Serialization And Escalation
- Pending Matching Worker
- Coordination Responsibility Interface
- Institution Profile Interface
- Workflow Regression Tests
- Case Intelligence
- Scoped Export Delivery
- Management Reporting Interface
- Frontend Type Configuration
- Serialization And Escalation
- Serialization And Escalation
- Local Runtime Dependencies
- Relationship Evidence Design
- Public Research Protocol
- Analytics Cohort Tests
- Analytics Export Tests
- Project Operation Guide
- Analytics Movement Tests
- Analytics Scope Tests
- Analytics Snapshot Tests
- Analytics Reconciliation Tests
- Coordination Workflows
- Analytics Authorization Tests
- Coordination Workflows
- Administrative Registry Editing
- Plain Language Walkthrough
- Import Validation Tests
- Analytics Counting Tests
- Analytics Date Tests
- Test Type Configuration
- Isolated Audit Stack
- Institution Concurrency Tests
- Bureau Fixture Documentation
- CSRF-protected Coordination sign-in form
- Coordination frontend HTML entrypoint

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 57 edges
2. `WorkflowTests` - 51 edges
3. `Institution` - 48 edges
4. `CaseAction` - 40 edges
5. `scoped_cases()` - 30 edges
6. `Bureau` - 28 edges
7. `Membership` - 28 edges
8. `InstitutionTests` - 28 edges
9. `role()` - 28 edges
10. `IntelligenceTests` - 27 edges

## Surprising Connections (you probably didn't know these)
- `2. Requirement-to-code audit` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `Review screen` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `Read APIs and interface` --references--> `ActionReadSerializer`  [INFERRED]
  docs/evidence-v1.md → backend/cases/serializers.py
- `5. Milestone C — source-grounded briefs and incident organization` --references--> `ActionReadSerializer`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → backend/cases/serializers.py
- `Safe evaluation` --references--> `calibrate()`  [INFERRED]
  docs/evidence-v1.md → backend/cases/management/commands/evaluate_matching.py

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`

## Communities (93 total, 51 thin omitted)

### Community 0 - "Browser Workflow Coverage"
Cohesion: 0.05
Nodes (43): endpoint, @playwright/test, post(), stamp, makeCase(), makeInstitution(), post(), stamp (+35 more)

### Community 1 - "Case Intelligence"
Cohesion: 0.06
Nodes (53): Single aggregate for scoped movement event counts, analytics(), actions(), Batched overlap complaint serialization, case_detail(), cases(), replay(), compute_dashboard() (+45 more)

### Community 2 - "Independent Research Review"
Cohesion: 0.07
Nodes (33): Authorized Indian institution intake, Separately authorized encrypted institutional research intake, Two blind independent reviewers and third-party adjudication, Research intake and independent review, Independent same-incident reference set before retrieval, OIA collection pending permission and unsent owner draft, Minimized records with preserved provenance and digests, Recall reference-set protocol (+25 more)

### Community 3 - "Case Intelligence"
Cohesion: 0.06
Nodes (29): build_evidence(), compare(), recorded(), score(), Immutable evidence and policy at human decision time, Evidence contract, Output-only frozen-policy synthetic evaluation, Relationship evidence v1 and decision snapshots (+21 more)

### Community 4 - "Frozen Model Matching"
Cohesion: 0.09
Nodes (15): Command, Command, refresh_active_matches(), baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch() (+7 more)

### Community 5 - "Escalation Readiness Tests"
Cohesion: 0.07
Nodes (5): send_reminders(), EscalationConcurrencyTests, submit(), EvaluationTests, WorkflowTests

### Community 6 - "Coordination Workflows"
Cohesion: 0.10
Nodes (21): audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput, ParticipantInput (+13 more)

### Community 7 - "Typed API Components"
Cohesion: 0.08
Nodes (32): api(), ApiError, Attachment, CaseDetail, categories, classifications, csrf(), Dashboard (+24 more)

### Community 8 - "Independent Restore Verification"
Cohesion: 0.08
Nodes (20): Independent audit schema files and model restore verification, main(), Memory, ticks(), digest(), main(), run(), shell() (+12 more)

### Community 9 - "Import Performance Measurement"
Cohesion: 0.10
Nodes (11): Four isolated controlled HTTP import workloads, browser(), main(), Memory, request(), simulate(), main(), simulate() (+3 more)

### Community 11 - "Source Intake Interface"
Cohesion: 0.16
Nodes (27): labels, CaseEscalations(), EscalationList(), EscalationQueue(), ResolutionForm(), validEscalations(), usePoll(), ManualRelationship() (+19 more)

### Community 12 - "Technical Design Boundaries"
Cohesion: 0.06
Nodes (24): Command, Migration, Authentication, files and reporting, Immutable canonical Permanent ID, Case intelligence, Complaint lifecycle, Database relationships, SIH 26264 — implementation design (+16 more)

### Community 13 - "Database Schema Migrations"
Cohesion: 0.09
Nodes (13): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+5 more)

### Community 16 - "Frontend Package Configuration"
Cohesion: 0.07
Nodes (28): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+20 more)

### Community 17 - "Institution Profile Interface"
Cohesion: 0.13
Nodes (16): User, App(), Registration searches canonical institution registry, Coordination(), Detail(), emptyOptions, GovernmentHeader(), NewCase() (+8 more)

### Community 18 - "Durable Source Intake"
Cohesion: 0.19
Nodes (21): writable(), cell(), digest(), get_job(), import_detail(), import_errors(), import_report(), import_summary_csv() (+13 more)

### Community 19 - "Pinned Model Release"
Cohesion: 0.13
Nodes (14): InstitutionAdminForm, Meta, ReadOnlyAdmin, Command, swap_release(), IncidentGroup, IncidentMembership, Meta (+6 more)

### Community 20 - "Institution Registry Administration"
Cohesion: 0.22
Nodes (15): authorized_actions(), coordination(), filtered_cases(), role(), scoped_cases(), detail(), history(), institution_cases() (+7 more)

### Community 23 - "Complaint Import Interface"
Cohesion: 0.20
Nodes (19): Bars(), ErrorNotice(), ExportButton(), Facts, ImportDetail(), Imports(), isExport(), isJob() (+11 more)

### Community 24 - "Coordination Workflows"
Cohesion: 0.15
Nodes (9): Command, Command, Command, Bureau, Escalation, Institution, Membership, Disabled shadow semantic20 FTS20 reference20 discovery (+1 more)

### Community 25 - "Evidence Transaction Tests"
Cohesion: 0.18
Nodes (3): ConcurrentEvidenceTests, EvidenceFixture, EvidenceWorkflowTests

### Community 26 - "Durable Source Intake"
Cohesion: 0.21
Nodes (14): current_bureau_id(), accessible_jobs(), ImportRow, configuration(), jobs(), Meta, Resolution, resolve() (+6 more)

### Community 27 - "Escalation Readiness Tests"
Cohesion: 0.14
Nodes (3): MovementExportTests, AccountabilityTests, HomepageTests

### Community 28 - "Case Intelligence"
Cohesion: 0.16
Nodes (14): Page, Brief, BriefContent(), CaseIntelligence(), Explicit conflict reload controls and retained drafts, Fact, FactReview(), Group (+6 more)

### Community 30 - "Serialization And Escalation"
Cohesion: 0.15
Nodes (5): action_query(), Meta, movements(), movements_csv(), MovementSerializer

### Community 31 - "Serialization And Escalation"
Cohesion: 0.16
Nodes (6): active_cases(), enrich(), groups(), notices(), CaseSerializer, FilterSerializer

### Community 32 - "Pending Matching Worker"
Cohesion: 0.12
Nodes (6): Command, Command, Command, Complaint, Seed only an empty designated demo database, Phase2MigrationTests

### Community 33 - "Coordination Responsibility Interface"
Cohesion: 0.20
Nodes (15): Case, CaseAction, CoordinationAction(), submit(), CoordinationRecordPage(), CoordinationRequests(), CoordinationWorkspace(), Participant (+7 more)

### Community 34 - "Institution Profile Interface"
Cohesion: 0.21
Nodes (14): InstitutionAction, InstitutionProfile, statuses, InstitutionCases(), change(), InstitutionCoordination(), InstitutionDirectory(), InstitutionEditor() (+6 more)

### Community 36 - "Case Intelligence"
Cohesion: 0.18
Nodes (5): evaluation_dataset(), seed_records(), Command, CaseAction, HistoricalMigrationTests

### Community 37 - "Scoped Export Delivery"
Cohesion: 0.25
Nodes (11): authorized_file(), build_export(), case_values(), export_detail(), export_download(), exports(), get_export(), query() (+3 more)

### Community 38 - "Management Reporting Interface"
Cohesion: 0.21
Nodes (13): Movement, AgeingPanel(), BureauWorkloadPanel(), ChartRow, CoordinationNotices(), HorizontalDistribution(), InstitutionMonitoringPanel(), InstitutionRow (+5 more)

### Community 39 - "Frontend Type Configuration"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 40 - "Serialization And Escalation"
Cohesion: 0.18
Nodes (10): Attachment, ActionReadSerializer, ActionSerializer, AttachmentSerializer, CreateCaseSerializer, InstitutionSerializer, Meta, ReviewSerializer (+2 more)

### Community 41 - "Serialization And Escalation"
Cohesion: 0.28
Nodes (9): page(), case_escalations(), CreateEscalationSerializer, EscalationSerializer, Meta, queue(), records(), resolve() (+1 more)

### Community 42 - "Local Runtime Dependencies"
Cohesion: 0.24
Nodes (12): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Incident groups forwarding defaults off (+4 more)

### Community 43 - "Relationship Evidence Design"
Cohesion: 0.27
Nodes (5): calibrate(), Command, eligible_corpus(), evaluate(), metrics()

### Community 44 - "Public Research Protocol"
Cohesion: 0.20
Nodes (8): B1.5: private public-data evaluation and independent annotation, Blind human review, Metric rules, Offline evaluation, Separate education consumer and government research tracks, Source gates, Storage and collection, Tests and results

### Community 47 - "Project Operation Guide"
Cohesion: 0.25
Nodes (8): Data, permissions and demonstration, AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Reviewed facts and incident groups default off, Movement CSV serializer reuse follow-up, Physical disconnected startup requires separate evidence, Prepare once while online, Start or stop a prepared demo, Verification and recovery

### Community 58 - "Plain Language Walkthrough"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, Open the prepared demonstration, What runs on the laptop

### Community 62 - "Test Type Configuration"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

### Community 64 - "Isolated Audit Stack"
Cohesion: 0.50
Nodes (3): Audit API bound to localhost port 8001, Isolated persistent audit PostgreSQL, Audit worker sharing isolated storage

## Knowledge Gaps
- **154 isolated node(s):** `Attachment`, `EvidenceComparison`, `Meta`, `ReviewSerializer`, `Facts` (+149 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 487 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **51 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `Escalation Readiness Tests` to `Pending Matching Worker`, `Case Intelligence`, `Serialization And Escalation`, `Durable Source Intake`, `Pinned Model Release`, `Coordination Workflows`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `scoped_cases()` connect `Institution Registry Administration` to `Pending Matching Worker`, `Coordination Workflows`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `EscalationTests` connect `Escalation Readiness Tests` to `Coordination Workflows`, `Pinned Model Release`, `Escalation Readiness Tests`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Attachment`, `EvidenceComparison`, `Meta` to the rest of the system?**
  _154 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Browser Workflow Coverage` be split into smaller, more focused modules?**
  _Cohesion score 0.050140056022408966 - nodes in this community are weakly interconnected._
- **Should `Case Intelligence` be split into smaller, more focused modules?**
  _Cohesion score 0.055905220288781934 - nodes in this community are weakly interconnected._
## Refresh scope and limitations

Refreshed source/document navigation for final-readiness work, including deterministic briefs, reviewed source spans, manual incident groups, migrations 0014/0015, disabled shadow discovery, technical design and research intake, canonical registration search, explicit conflict reload controls, batched API serialization, scoped aggregate queries, worker/stdin readiness, controlled HTTP workloads and pinned encoder timing. Sources and test implementations describe behavior; this graph does not establish that tests passed or that release gates passed.

Private datasets, uploads, secrets, model weights, artifacts, backups and all tests/results content were excluded from extraction. Test source code is included structurally. Historical graph outputs and caches are preserved, with a timestamped pre-refresh backup. No application code, tests, model policy or calibration was changed by this refresh.

Token accounting: measured host-agent token usage is unavailable. Numeric input/output counts are zero placeholders, not a claim of zero token use or free semantic extraction. No cloud provider or API key was used.

Independent real-data review, same-incident recall evidence and physical-network-disconnected startup remain external verification gates. Shadow retrieval is experimental and does not activate production expansion. Reviewed-fact and incident-group controls default off.

The final technical readiness report exists but remains excluded under tests/results; it was not read or indexed. Its existence is not release sign-off; external validation gates remain distinct.

## Extraction health

```text
[graphify] MultiDiGraph edge-collapse diagnostic
input: <in-memory>
input_stage: provided JSON (normal graph.json is post-build)
effective_directed: <direct-call>
nodes: 1413
unverified_code_nodes: 0
raw_edges: 3554
valid_candidate_edges: 3554
missing_endpoint_edges: 0
dangling_endpoint_edges: 0
external_reference_edges: 0
self_loop_edges: 15
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 3554
directed_same_endpoint_collapsed_edges: 0
undirected_unique_endpoint_pairs: 3553
undirected_same_endpoint_collapsed_edges: 1
same_endpoint_group_count: 0
relation_variant_groups: 0
source_file_variant_groups: 0
source_location_variant_groups: 0
context_variant_groups: 0
post_build_graph_type: DiGraph
post_build_edges: 3554
producer_suppression_sites: 12
producer_suppression_examples:
  - L1676 seen_ids arity=unknown
  - L2209 seen_ids arity=unknown
  - L2211 seen_doc_refs arity=unknown
  - L2628 seen_ids arity=unknown
  - L2775 seen_ids arity=unknown
  - L3501 seen_keys arity=unknown
  - L3670 seen_keys arity=unknown
  - L5777 seen_ids arity=unknown
note: normal graph.json is post-build; raw producer loss must be measured earlier.
```

## Movement export refresh provenance

The cached manifest found eight changed permitted files: backend/cases/analytics.py, backend/cases/matching.py, backend/cases/migrations/0014_case_intelligence.py, frontend/src/institutions.tsx, frontend/src/intelligence.tsx, frontend/src/main.tsx, tests/backend/test_movement_exports.py, and README.md. The prior graph was stale against these permitted sources; all eight were refreshed without changing application source. The current movement exporter constructs one request-scoped restricted serializer before streaming rows. The new movement-export test source is structurally covered. README's linked results report remains excluded and was not read; test outcomes are not inferred from graph coverage.

Previous graph: 1,405 nodes / 3,559 directed edges / 101 communities. Refreshed graph: 1,413 nodes / 3,554 directed edges / 93 communities. Replacement removed stale source relationships; no missing/dangling endpoints or directed edge collapses remain. Fifteen AST self-loops remain disclosed. Follow-up detection found zero changed/deleted permitted files. All graph node source paths are portable repository-relative paths.
