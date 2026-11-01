# Graph Report - SIH  (2026-11-02)

## Corpus Check
- 148 files · ~81,864 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1405 nodes · 3559 edges · 101 communities (44 shown, 57 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 322 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Browser Workflow Coverage
- Coordination Workflows
- Independent Research Review
- Durable Source Intake
- Case Mutation API
- Technical Design Boundaries
- Escalation Readiness Tests
- Database Schema Migrations
- Source Intake Interface
- Import Validation Tests
- Case Intelligence
- Institution Profile Interface
- Serialization And Escalation
- Frontend Package Configuration
- Import Performance Measurement
- Case Intelligence
- Typed API Components
- Institution Profile Interface
- Frozen Model Matching
- Serialization And Escalation
- Institution Permission Tests
- Complaint Import Interface
- Institution Registry Administration
- Pinned Model Release
- Evidence Transaction Tests
- Escalation Readiness Tests
- Independent Restore Verification
- Coordination Completion Tests
- Coordination Responsibility Interface
- Case Intelligence
- Workflow Regression Tests
- Management Reporting Interface
- Frontend Type Configuration
- Scoped Export Delivery
- Case Intelligence
- Relationship Evidence Design
- Escalation Readiness Tests
- Relationship Evidence Design
- Pending Matching Worker
- Local Runtime Dependencies
- Root URL Configuration
- Import Validation Tests
- Delivery Verification Scripts
- Public Research Protocol
- Analytics Cohort Tests
- Analytics Export Tests
- Case Intelligence
- Case Intelligence
- Analytics Movement Tests
- Project Operation Guide
- Escalation Readiness Tests
- Analytics Scope Tests
- Analytics Snapshot Tests
- Analytics Reconciliation Tests
- Case Intelligence
- Case Intelligence
- Independent Restore Verification
- Analytics Authorization Tests
- Startup Safety Tests
- Administrative Registry Editing
- Plain Language Walkthrough
- Analytics Counting Tests
- Analytics Date Tests
- Test Type Configuration
- Model Admin Registration
- Shadow Retrieval
- Isolated Audit Stack
- Relationship Evidence Design
- Institution Concurrency Tests
- Readiness Concurrency Tests
- Escalation Readiness Tests
- Bureau Fixture Documentation
- CSRF-protected Coordination sign-in form
- Coordination frontend HTML entrypoint

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 60 edges
2. `WorkflowTests` - 51 edges
3. `Institution` - 50 edges
4. `CaseAction` - 40 edges
5. `usePoll()` - 31 edges
6. `scoped_cases()` - 30 edges
7. `InstitutionTests` - 28 edges
8. `Bureau` - 28 edges
9. `Membership` - 28 edges
10. `role()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `Versioned exact-span reviewed facts` --conceptually_related_to--> `Migration`  [INFERRED]
  docs/technical-design.md → backend/cases/migrations/0015_intelligence_protection.py
- `Read APIs and interface` --references--> `ActionReadSerializer`  [INFERRED]
  docs/evidence-v1.md → backend/cases/serializers.py
- `2. Requirement-to-code audit` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `5. Milestone C — source-grounded briefs and incident organization` --references--> `ActionReadSerializer`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → backend/cases/serializers.py
- `Review screen` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`

## Communities (101 total, 57 thin omitted)

### Community 0 - "Browser Workflow Coverage"
Cohesion: 0.05
Nodes (43): endpoint, @playwright/test, post(), stamp, makeCase(), makeInstitution(), post(), stamp (+35 more)

### Community 1 - "Coordination Workflows"
Cohesion: 0.06
Nodes (29): CasesConfig, audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput (+21 more)

### Community 2 - "Independent Research Review"
Cohesion: 0.07
Nodes (33): Authorized Indian institution intake, Separately authorized encrypted institutional research intake, Two blind independent reviewers and third-party adjudication, Research intake and independent review, Independent same-incident reference set before retrieval, OIA collection pending permission and unsent owner draft, Minimized records with preserved provenance and digests, Recall reference-set protocol (+25 more)

### Community 3 - "Durable Source Intake"
Cohesion: 0.12
Nodes (37): current_bureau_id(), role(), writable(), accessible_jobs(), cell(), digest(), get_job(), import_detail() (+29 more)

### Community 4 - "Case Mutation API"
Cohesion: 0.09
Nodes (28): actions(), Batched overlap complaint serialization, case_detail(), cases(), replay(), compute_dashboard(), Conflict, dashboard() (+20 more)

### Community 5 - "Technical Design Boundaries"
Cohesion: 0.05
Nodes (26): Command, Command, Migration, Authentication, files and reporting, Immutable canonical Permanent ID, Case intelligence, Complaint lifecycle, Database relationships (+18 more)

### Community 6 - "Escalation Readiness Tests"
Cohesion: 0.09
Nodes (5): Notification, notify_escalation(), EscalationTests, AccountabilityTests, HomepageTests

### Community 7 - "Database Schema Migrations"
Cohesion: 0.07
Nodes (14): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+6 more)

### Community 8 - "Source Intake Interface"
Cohesion: 0.16
Nodes (27): Page, CaseEscalations(), EscalationList(), EscalationQueue(), ResolutionForm(), validEscalations(), usePoll(), ManualRelationship() (+19 more)

### Community 13 - "Institution Profile Interface"
Cohesion: 0.12
Nodes (27): date(), Institution, InstitutionAction, InstitutionProfile, labels, MatchingEvidence, Overlap, ReviewSnapshot (+19 more)

### Community 14 - "Serialization And Escalation"
Cohesion: 0.10
Nodes (13): action_query(), Single aggregate for scoped movement event counts, analytics(), Meta, movements(), movements_csv(), chunks(), MovementSerializer (+5 more)

### Community 15 - "Frontend Package Configuration"
Cohesion: 0.07
Nodes (28): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+20 more)

### Community 16 - "Import Performance Measurement"
Cohesion: 0.12
Nodes (11): Four isolated controlled HTTP import workloads, browser(), main(), Memory, request(), simulate(), main(), simulate() (+3 more)

### Community 17 - "Case Intelligence"
Cohesion: 0.16
Nodes (23): actions_for(), brief(), edit_group(), FactInput, facts(), FactSerializer, feature(), flag_supporting_groups() (+15 more)

### Community 18 - "Typed API Components"
Cohesion: 0.11
Nodes (20): api(), ApiError, Attachment, CaseDetail, categories, classifications, csrf(), Dashboard (+12 more)

### Community 19 - "Institution Profile Interface"
Cohesion: 0.13
Nodes (16): User, App(), Registration searches canonical institution registry, Coordination(), Detail(), emptyOptions, GovernmentHeader(), NewCase() (+8 more)

### Community 20 - "Frozen Model Matching"
Cohesion: 0.15
Nodes (13): Command, baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch(), match_case(), ModelUnavailable (+5 more)

### Community 21 - "Serialization And Escalation"
Cohesion: 0.17
Nodes (16): page(), case_escalations(), CreateEscalationSerializer, EscalationSerializer, Meta, queue(), records(), resolve() (+8 more)

### Community 23 - "Complaint Import Interface"
Cohesion: 0.20
Nodes (19): Bars(), ErrorNotice(), ExportButton(), Facts, ImportDetail(), Imports(), isExport(), isJob() (+11 more)

### Community 24 - "Institution Registry Administration"
Cohesion: 0.27
Nodes (15): authorized_actions(), coordination(), filtered_cases(), scoped_cases(), detail(), history(), institution_cases(), InstitutionHistorySerializer (+7 more)

### Community 25 - "Pinned Model Release"
Cohesion: 0.17
Nodes (11): Command, refresh_active_matches(), swap_release(), Complaint, IncidentGroup, IncidentMembership, Meta, ModelRelease (+3 more)

### Community 26 - "Evidence Transaction Tests"
Cohesion: 0.18
Nodes (3): ConcurrentEvidenceTests, EvidenceFixture, EvidenceWorkflowTests

### Community 28 - "Independent Restore Verification"
Cohesion: 0.18
Nodes (9): Independent audit schema files and model restore verification, digest(), main(), run(), snapshot(), digest(), main(), run() (+1 more)

### Community 30 - "Coordination Responsibility Interface"
Cohesion: 0.20
Nodes (15): Case, CaseAction, CoordinationAction(), submit(), CoordinationRecordPage(), CoordinationRequests(), CoordinationWorkspace(), Participant (+7 more)

### Community 31 - "Case Intelligence"
Cohesion: 0.18
Nodes (13): Brief, BriefContent(), CaseIntelligence(), Explicit conflict reload controls and retained drafts, Fact, FactReview(), Group, IncidentGroups() (+5 more)

### Community 33 - "Management Reporting Interface"
Cohesion: 0.20
Nodes (13): Movement, AgeingPanel(), BureauWorkloadPanel(), ChartRow, HorizontalDistribution(), InstitutionMonitoringPanel(), InstitutionRow, ManagementHome() (+5 more)

### Community 34 - "Frontend Type Configuration"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 35 - "Scoped Export Delivery"
Cohesion: 0.27
Nodes (11): authorized_file(), build_export(), case_values(), export_detail(), export_download(), exports(), get_export(), query() (+3 more)

### Community 36 - "Case Intelligence"
Cohesion: 0.15
Nodes (12): 10. Order, effort and decisions, 1. Outcome and verified starting point, 2. Requirement-to-code audit, 3. Milestone A — simpler official workspace, 6. Milestone D — optional read-only MCP, 7. File-by-file execution backlog, 8. API and migration compatibility, 9. Verification and delivery gates (+4 more)

### Community 37 - "Relationship Evidence Design"
Cohesion: 0.24
Nodes (5): build_evidence(), compare(), recorded(), Immutable evidence and policy at human decision time, EvidenceContractTests

### Community 39 - "Relationship Evidence Design"
Cohesion: 0.33
Nodes (4): eligible_corpus(), evaluate(), corpus_fixture(), EvaluationSafetyTests

### Community 40 - "Pending Matching Worker"
Cohesion: 0.14
Nodes (3): Command, Command, Phase2MigrationTests

### Community 41 - "Local Runtime Dependencies"
Cohesion: 0.24
Nodes (12): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Incident groups forwarding defaults off (+4 more)

### Community 43 - "Import Validation Tests"
Cohesion: 0.18
Nodes (3): Command, OverlapCandidate, DashboardTests

### Community 44 - "Delivery Verification Scripts"
Cohesion: 0.40
Nodes (7): digest(), main(), run(), shell(), snapshot(), main(), snapshot()

### Community 45 - "Public Research Protocol"
Cohesion: 0.20
Nodes (8): B1.5: private public-data evaluation and independent annotation, Blind human review, Metric rules, Offline evaluation, Separate education consumer and government research tracks, Source gates, Storage and collection, Tests and results

### Community 49 - "Case Intelligence"
Cohesion: 0.25
Nodes (6): ActionReadSerializer, Output-only frozen-policy synthetic evaluation, Read APIs and interface, Relationship evidence v1 and decision snapshots, Review transaction and versioning, 5. Milestone C — source-grounded briefs and incident organization

### Community 51 - "Project Operation Guide"
Cohesion: 0.29
Nodes (7): Data, permissions and demonstration, AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Reviewed facts and incident groups default off, Physical disconnected startup requires separate evidence, Prepare once while online, Start or stop a prepared demo, Verification and recovery

### Community 56 - "Case Intelligence"
Cohesion: 0.33
Nodes (4): calibrate(), metrics(), Safe evaluation, EvaluationTests

### Community 57 - "Case Intelligence"
Cohesion: 0.33
Nodes (6): score(), Evidence contract, 4. Milestone B — explainable matching, evaluated before activation, Candidate discovery, Evaluation and data, Evidence contract before ranking changes

### Community 58 - "Independent Restore Verification"
Cohesion: 0.47
Nodes (3): main(), Memory, ticks()

### Community 64 - "Plain Language Walkthrough"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, Open the prepared demonstration, What runs on the laptop

### Community 67 - "Test Type Configuration"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

### Community 70 - "Isolated Audit Stack"
Cohesion: 0.50
Nodes (3): Audit API bound to localhost port 8001, Isolated persistent audit PostgreSQL, Audit worker sharing isolated storage

## Knowledge Gaps
- **153 isolated node(s):** `Row`, `Source`, `SourceJob`, `Attachment`, `EvidenceComparison` (+148 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 485 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **57 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `Escalation Readiness Tests` to `Coordination Workflows`, `Durable Source Intake`, `Case Mutation API`, `Escalation Readiness Tests`, `Escalation Readiness Tests`, `Import Validation Tests`, `Escalation Readiness Tests`, `Serialization And Escalation`, `Institution Registry Administration`, `Pinned Model Release`, `Case Intelligence`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `Relationship evidence v1 and decision snapshots` connect `Case Intelligence` to `Case Intelligence`, `Case Intelligence`, `Relationship Evidence Design`?**
  _High betweenness centrality (0.001) - this node is a cross-community bridge._
- **Why does `Output-only frozen-policy synthetic evaluation` connect `Case Intelligence` to `Benchmark Runtime Utilities`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Row`, `Source`, `SourceJob` to the rest of the system?**
  _153 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Browser Workflow Coverage` be split into smaller, more focused modules?**
  _Cohesion score 0.050140056022408966 - nodes in this community are weakly interconnected._
- **Should `Coordination Workflows` be split into smaller, more focused modules?**
  _Cohesion score 0.05501165501165501 - nodes in this community are weakly interconnected._
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
nodes: 1405
unverified_code_nodes: 0
raw_edges: 3559
valid_candidate_edges: 3559
missing_endpoint_edges: 0
dangling_endpoint_edges: 0
external_reference_edges: 0
self_loop_edges: 15
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 3559
directed_same_endpoint_collapsed_edges: 0
undirected_unique_endpoint_pairs: 3558
undirected_same_endpoint_collapsed_edges: 1
same_endpoint_group_count: 0
relation_variant_groups: 0
source_file_variant_groups: 0
source_location_variant_groups: 0
context_variant_groups: 0
post_build_graph_type: DiGraph
post_build_edges: 3559
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

Final configuration-only pass: refreshed compose.yaml, including standard API/worker forwarding of reviewed-facts and incident-groups controls with defaults 0. .env* remains excluded and was not inspected. Existing application/document semantics and caches were preserved. Follow-up detection found zero changed or deleted permitted files.
