# Graph Report - SIH  (2026-11-02)

## Corpus Check
- 150 files · ~82,686 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1423 nodes · 3561 edges · 100 communities (45 shown, 55 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 317 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Browser Workflow Coverage
- Independent Research Review
- Escalation Readiness Tests
- Import Performance Measurement
- Durable Source Intake
- Serialization And Escalation
- Typed API Components
- Fixture Identity Utilities
- Frozen Model Matching
- Source Intake Interface
- Import Validation Tests
- Institution Profile Interface
- Database Schema Migrations
- Case Intelligence
- Pending Matching Worker
- Case Intelligence
- Escalation Readiness Tests
- Frontend Package Configuration
- Typed API Components
- Case Intelligence
- Coordination Workflows
- Serialization And Escalation
- Institution Permission Tests
- Complaint Import Interface
- Technical Design Boundaries
- Evidence Transaction Tests
- Institution Registry Administration
- Escalation Readiness Tests
- Case Intelligence
- Independent Restore Verification
- Coordination Completion Tests
- Institution Profile Interface
- Workflow Regression Tests
- Case Intelligence
- Frontend Type Configuration
- Case Intelligence
- Import Validation Tests
- Serialization And Escalation
- Local Runtime Dependencies
- Coordination Workflows
- Case Intelligence
- Case Intelligence
- Public Research Protocol
- Project Operation Guide
- Case Intelligence
- Analytics Cohort Tests
- Analytics Export Tests
- Case Intelligence
- Independent Restore Verification
- Technical Design Boundaries
- Analytics Movement Tests
- Case Intelligence
- Analytics Scope Tests
- Analytics Snapshot Tests
- Analytics Reconciliation Tests
- Case Intelligence
- Analytics Authorization Tests
- Independent Restore Verification
- Case Intelligence
- Case Intelligence
- Technical Design Boundaries
- Plain Language Walkthrough
- Analytics Counting Tests
- Analytics Date Tests
- Test Type Configuration
- Pending Matching Worker
- Serialization And Escalation
- Isolated Audit Stack
- Institution Concurrency Tests
- Case Intelligence
- Bureau Fixture Documentation
- CSRF-protected Coordination sign-in form
- Coordination frontend HTML entrypoint

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 57 edges
2. `WorkflowTests` - 51 edges
3. `Institution` - 48 edges
4. `CaseAction` - 40 edges
5. `scoped_cases()` - 30 edges
6. `InstitutionTests` - 28 edges
7. `Bureau` - 28 edges
8. `Membership` - 28 edges
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
- `Authorized current-state brief and paginated history` --conceptually_related_to--> `CaseIntelligence()`  [INFERRED]
  docs/technical-design.md → frontend/src/intelligence.tsx

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`

## Communities (100 total, 55 thin omitted)

### Community 0 - "Browser Workflow Coverage"
Cohesion: 0.05
Nodes (42): endpoint, post(), stamp, makeCase(), makeInstitution(), post(), stamp, token() (+34 more)

### Community 1 - "Independent Research Review"
Cohesion: 0.07
Nodes (33): Authorized Indian institution intake, Separately authorized encrypted institutional research intake, Two blind independent reviewers and third-party adjudication, Research intake and independent review, Independent same-incident reference set before retrieval, OIA collection pending permission and unsent owner draft, Minimized records with preserved provenance and digests, Recall reference-set protocol (+25 more)

### Community 2 - "Escalation Readiness Tests"
Cohesion: 0.05
Nodes (6): send_reminders(), CoordinationConcurrencyTests, CoordinationWorkflowTests, EscalationConcurrencyTests, submit(), WorkflowTests

### Community 3 - "Import Performance Measurement"
Cohesion: 0.08
Nodes (14): Four isolated controlled HTTP import workloads, browser(), main(), Memory, request(), simulate(), main(), simulate() (+6 more)

### Community 4 - "Durable Source Intake"
Cohesion: 0.11
Nodes (37): current_bureau_id(), writable(), accessible_jobs(), cell(), digest(), get_job(), import_detail(), import_errors() (+29 more)

### Community 5 - "Serialization And Escalation"
Cohesion: 0.09
Nodes (17): filtered_cases(), active_cases(), enrich(), groups(), notices(), authorized_file(), build_export(), case_values() (+9 more)

### Community 6 - "Typed API Components"
Cohesion: 0.08
Nodes (38): api(), ApiError, Attachment, Case, CaseAction, CaseDetail, csrf(), date() (+30 more)

### Community 8 - "Frozen Model Matching"
Cohesion: 0.10
Nodes (20): Command, Command, eligible_corpus(), evaluate(), metrics(), refresh_active_matches(), Command, baseline_runtime() (+12 more)

### Community 9 - "Source Intake Interface"
Cohesion: 0.16
Nodes (27): Page, CaseEscalations(), EscalationList(), EscalationQueue(), ResolutionForm(), validEscalations(), usePoll(), ManualRelationship() (+19 more)

### Community 10 - "Import Validation Tests"
Cohesion: 0.11
Nodes (6): Command, swap_release(), StagedEmbedding, DashboardTests, ImportTests, RolloutTests

### Community 11 - "Institution Profile Interface"
Cohesion: 0.10
Nodes (22): User, App(), Registration searches canonical institution registry, Coordination(), Detail(), emptyOptions, GovernmentHeader(), Mobile shell retains session sign-out (+14 more)

### Community 12 - "Database Schema Migrations"
Cohesion: 0.09
Nodes (13): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+5 more)

### Community 13 - "Case Intelligence"
Cohesion: 0.10
Nodes (22): InstitutionAdminForm, Meta, Batched overlap complaint serialization, overlap_data(), overlap_queryset(), overlaps(), review_snapshots(), decision_snapshot() (+14 more)

### Community 14 - "Pending Matching Worker"
Cohesion: 0.08
Nodes (6): Command, Command, Command, Command, Complaint, Phase2MigrationTests

### Community 16 - "Escalation Readiness Tests"
Cohesion: 0.10
Nodes (4): InstitutionAdmin, ReadOnlyAdmin, notify_escalation(), EscalationTests

### Community 17 - "Frontend Package Configuration"
Cohesion: 0.07
Nodes (29): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+21 more)

### Community 18 - "Typed API Components"
Cohesion: 0.10
Nodes (22): categories, classifications, Dashboard, Movement, Options, All-time coordination separate from receipt filters, DashboardHome(), validDashboard() (+14 more)

### Community 19 - "Case Intelligence"
Cohesion: 0.11
Nodes (17): actions(), case_detail(), cases(), replay(), Conflict, dashboard(), dashboard_data(), download() (+9 more)

### Community 20 - "Coordination Workflows"
Cohesion: 0.20
Nodes (21): page(), audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput (+13 more)

### Community 21 - "Serialization And Escalation"
Cohesion: 0.15
Nodes (16): scoped_cases(), case_escalations(), CreateEscalationSerializer, EscalationSerializer, Meta, queue(), records(), resolve() (+8 more)

### Community 23 - "Complaint Import Interface"
Cohesion: 0.20
Nodes (19): Bars(), ErrorNotice(), ExportButton(), Facts, ImportDetail(), Imports(), isExport(), isJob() (+11 more)

### Community 24 - "Technical Design Boundaries"
Cohesion: 0.10
Nodes (20): Migration, Authentication, files and reporting, Immutable canonical Permanent ID, Case intelligence, Complaint lifecycle, Database relationships, SIH 26264 — implementation design, Five-minute fictional demonstration (+12 more)

### Community 25 - "Evidence Transaction Tests"
Cohesion: 0.18
Nodes (3): ConcurrentEvidenceTests, EvidenceFixture, EvidenceWorkflowTests

### Community 26 - "Institution Registry Administration"
Cohesion: 0.28
Nodes (14): authorized_actions(), coordination(), role(), detail(), history(), institution_cases(), InstitutionHistorySerializer, InstitutionProfileSerializer (+6 more)

### Community 27 - "Escalation Readiness Tests"
Cohesion: 0.14
Nodes (3): MovementExportTests, AccountabilityTests, HomepageTests

### Community 28 - "Case Intelligence"
Cohesion: 0.16
Nodes (14): labels, Brief, BriefContent(), CaseIntelligence(), Explicit conflict reload controls and retained drafts, Fact, FactReview(), Group (+6 more)

### Community 29 - "Independent Restore Verification"
Cohesion: 0.22
Nodes (11): digest(), main(), run(), shell(), snapshot(), digest(), main(), run() (+3 more)

### Community 31 - "Institution Profile Interface"
Cohesion: 0.21
Nodes (14): Institution, InstitutionAction, InstitutionProfile, InstitutionCases(), change(), InstitutionCoordination(), InstitutionDirectory(), InstitutionEditor() (+6 more)

### Community 33 - "Case Intelligence"
Cohesion: 0.25
Nodes (11): edit_group(), feature(), flag_supporting_groups(), group_audit(), group_profile(), group_query(), GroupInput, groups() (+3 more)

### Community 34 - "Frontend Type Configuration"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 35 - "Case Intelligence"
Cohesion: 0.15
Nodes (12): 10. Order, effort and decisions, 1. Outcome and verified starting point, 2. Requirement-to-code audit, 3. Milestone A — simpler official workspace, 6. Milestone D — optional read-only MCP, 7. File-by-file execution backlog, 8. API and migration compatibility, 9. Verification and delivery gates (+4 more)

### Community 37 - "Serialization And Escalation"
Cohesion: 0.20
Nodes (8): action_query(), Single aggregate for scoped movement event counts, analytics(), Meta, movements(), movements_csv(), MovementSerializer, compute_dashboard()

### Community 38 - "Local Runtime Dependencies"
Cohesion: 0.24
Nodes (12): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Incident groups forwarding defaults off (+4 more)

### Community 40 - "Case Intelligence"
Cohesion: 0.22
Nodes (3): evaluation_dataset(), seed_records(), EvaluationTests

### Community 41 - "Case Intelligence"
Cohesion: 0.27
Nodes (9): FactInput, facts(), FactSerializer, Meta, review_fact(), ReviewInput, validate_span(), Migration (+1 more)

### Community 42 - "Public Research Protocol"
Cohesion: 0.20
Nodes (8): B1.5: private public-data evaluation and independent annotation, Blind human review, Metric rules, Offline evaluation, Separate education consumer and government research tracks, Source gates, Storage and collection, Tests and results

### Community 43 - "Project Operation Guide"
Cohesion: 0.22
Nodes (9): Data, permissions and demonstration, AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Reviewed facts and incident groups default off, Movement CSV serializer reuse follow-up, Physical disconnected startup requires separate evidence, Institution-first responsive portal UI follow-up, Prepare once while online, Start or stop a prepared demo (+1 more)

### Community 47 - "Case Intelligence"
Cohesion: 0.25
Nodes (6): calibrate(), Immutable evidence and policy at human decision time, Output-only frozen-policy synthetic evaluation, Relationship evidence v1 and decision snapshots, Review transaction and versioning, Safe evaluation

### Community 48 - "Independent Restore Verification"
Cohesion: 0.39
Nodes (5): Independent audit schema files and model restore verification, digest(), main(), run(), snapshot()

### Community 55 - "Case Intelligence"
Cohesion: 0.33
Nodes (6): score(), Evidence contract, 4. Milestone B — explainable matching, evaluated before activation, Candidate discovery, Evaluation and data, Evidence contract before ranking changes

### Community 60 - "Case Intelligence"
Cohesion: 0.60
Nodes (4): actions_for(), brief(), history(), Authorized current-state brief and paginated history

### Community 63 - "Plain Language Walkthrough"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, Open the prepared demonstration, What runs on the laptop

### Community 66 - "Test Type Configuration"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

### Community 68 - "Serialization And Escalation"
Cohesion: 0.50
Nodes (3): ActionReadSerializer, Read APIs and interface, 5. Milestone C — source-grounded briefs and incident organization

### Community 69 - "Isolated Audit Stack"
Cohesion: 0.50
Nodes (3): Audit API bound to localhost port 8001, Isolated persistent audit PostgreSQL, Audit worker sharing isolated storage

## Knowledge Gaps
- **160 isolated node(s):** `Row`, `Source`, `SourceJob`, `Migration`, `Migration` (+155 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 495 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `process_import()` connect `Durable Source Intake` to `Institution Registry Administration`, `Case Intelligence`, `Serialization And Escalation`, `Pending Matching Worker`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `_Base` connect `Analytics Export Tests` to `Durable Source Intake`, `Pending Matching Worker`, `Coordination Workflows`, `Analytics Filter Tests`, `Institution Registry Administration`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `AgeingFilterBandTests` connect `Analytics Authorization Tests` to `Analytics Filter Tests`, `Analytics Export Tests`, `Pending Matching Worker`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Row`, `Source`, `SourceJob` to the rest of the system?**
  _160 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Browser Workflow Coverage` be split into smaller, more focused modules?**
  _Cohesion score 0.05034199726402189 - nodes in this community are weakly interconnected._
- **Should `Independent Research Review` be split into smaller, more focused modules?**
  _Cohesion score 0.07043650793650794 - nodes in this community are weakly interconnected._
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
nodes: 1423
unverified_code_nodes: 0
raw_edges: 3561
valid_candidate_edges: 3561
missing_endpoint_edges: 0
dangling_endpoint_edges: 0
external_reference_edges: 0
self_loop_edges: 15
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 3561
directed_same_endpoint_collapsed_edges: 0
undirected_unique_endpoint_pairs: 3560
undirected_same_endpoint_collapsed_edges: 1
same_endpoint_group_count: 0
relation_variant_groups: 0
source_file_variant_groups: 0
source_location_variant_groups: 0
context_variant_groups: 0
post_build_graph_type: DiGraph
post_build_edges: 3561
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

## Portal UI refresh provenance

Source checkpoint: 60b13d5 on codex/portal-ui, plus the stable working README report link. Refreshed four AST sources (main.tsx, dashboard.tsx, management.tsx, portal-ui.spec.ts) and changed README semantics. These map the shared portal stylesheet import, institution-first keyboard search, receipt-scope controls, all-time coordination actions, KPI descriptions, responsive shell and mobile sign-out. The new browser test source is covered; its four tests and the separate running regression suite are not claimed passed by this graph. Linked tests/results evidence was not read.

Graphify detects 150 supported source/document files. frontend/src/portal.css is a supplemental explicitly indexed source because this detector omits CSS. Its shared presentation, 900px responsive rule and print rule are mapped; future CSS-only changes require an explicit stylesheet check. The supplemental stylesheet SHA-256 is recorded in ignored REFRESH_SUMMARY.json. Follow-up supported-file detection found zero changed/deleted files; current stylesheet bytes match the recorded digest.

Previous graph: 1,413 nodes / 3,554 directed edges / 93 communities. Current graph: 1,423 nodes / 3,561 directed edges / 100 communities across 149 represented source files. All node source paths are repository-relative; zero missing/dangling endpoints, duplicates or directed collapses. Fifteen AST self-loops remain disclosed. Historical caches/backups were preserved; no application/test edits or external APIs were used.
