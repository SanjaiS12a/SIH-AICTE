# Graph Report - SIH  (2026-11-02)

## Corpus Check
- 166 files · ~88,660 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1545 nodes · 3945 edges · 115 communities (58 shown, 57 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 373 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Escalation Readiness Tests
- Escalation Readiness Tests
- Case Intelligence
- Independent Research Review
- Durable Source Intake
- Technical Design Boundaries
- Source Intake Interface
- Import Performance Measurement
- Institution Profile Interface
- Frozen Model Matching
- Serialization And Escalation
- Import Validation Tests
- Serialization And Escalation
- Case Intelligence
- Case Intelligence
- Frontend Package Configuration
- Typed API Components
- Case Intelligence
- Frozen Model Matching
- Case Intelligence
- Case Intelligence
- Browser Workflow Coverage
- Complaint Import Interface
- Import Performance Measurement
- Institution Permission Tests
- Escalation Readiness Tests
- Database Schema Migrations
- Evidence Transaction Tests
- Institution Registry Administration
- Independent Research Review
- Serialization And Escalation
- Typed API Components
- Institution Profile Interface
- Coordination Completion Tests
- Workflow Regression Tests
- Case Intelligence
- Frontend Type Configuration
- Serialization And Escalation
- Import Validation Tests
- Local Runtime Dependencies
- Browser Workflow Coverage
- Case Intelligence
- Independent Restore Verification
- Public Research Protocol
- Project Operation Guide
- Case Intelligence
- Case Intelligence
- Analytics Cohort Tests
- Analytics Export Tests
- Case Intelligence
- Typed API Components
- Analytics Movement Tests
- Case Intelligence
- Case Intelligence
- Browser Workflow Coverage
- Analytics Scope Tests
- Analytics Snapshot Tests
- Analytics Reconciliation Tests
- Browser Workflow Coverage
- Browser Workflow Coverage
- Browser Workflow Coverage
- Browser Workflow Coverage
- Case Intelligence
- Case Intelligence
- Frozen Model Matching
- Import Performance Measurement
- Analytics Authorization Tests
- Browser Workflow Coverage
- Independent Restore Verification
- Coordination Workflows
- Plain Language Walkthrough
- Analytics Counting Tests
- Analytics Date Tests
- Test Type Configuration
- Case Intelligence
- Isolated Audit Stack
- Institution Profile Interface
- Source Navigation
- Database Schema Migrations
- Institution Concurrency Tests
- Case Intelligence
- Database Schema Migrations
- Database Schema Migrations
- Database Schema Migrations
- Case Intelligence
- Bureau Fixture Documentation
- CSRF-protected Coordination sign-in form
- Coordination frontend HTML entrypoint
- Case Intelligence

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 61 edges
2. `Institution` - 53 edges
3. `WorkflowTests` - 51 edges
4. `CaseAction` - 46 edges
5. `scoped_cases()` - 37 edges
6. `usePoll()` - 34 edges
7. `role()` - 31 edges
8. `Membership` - 29 edges
9. `Bureau` - 29 edges
10. `InstitutionTests` - 28 edges

## Surprising Connections (you probably didn't know these)
- `5. Milestone C — source-grounded briefs and incident organization` --references--> `ActionReadSerializer`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → backend/cases/serializers.py
- `Read APIs and interface` --references--> `ActionReadSerializer`  [INFERRED]
  docs/evidence-v1.md → backend/cases/serializers.py
- `Versioned group retirement preserves authoritative history` --conceptually_related_to--> `save_group()`  [INFERRED]
  docs/core-intelligence.md → backend/cases/intelligence.py
- `Versioned exact-span reviewed facts` --conceptually_related_to--> `Migration`  [INFERRED]
  docs/technical-design.md → backend/cases/migrations/0015_intelligence_protection.py
- `2. Requirement-to-code audit` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/incident-summary.tsx -> frontend/src/imports.tsx`
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`

## Communities (115 total, 57 thin omitted)

### Community 0 - "Escalation Readiness Tests"
Cohesion: 0.05
Nodes (7): Notification, notify_escalation(), send_reminders(), EscalationConcurrencyTests, EscalationTests, submit(), WorkflowTests

### Community 1 - "Escalation Readiness Tests"
Cohesion: 0.06
Nodes (25): audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput, ParticipantInput (+17 more)

### Community 2 - "Case Intelligence"
Cohesion: 0.08
Nodes (4): CoreIncidentTests, IncidentConcurrencyTests, IntelligenceConcurrencyTests, IntelligenceTests

### Community 3 - "Independent Research Review"
Cohesion: 0.09
Nodes (24): Independent same-incident reference set before retrieval, manifest(), PublicEvaluationTests, RecallTests, collect(), digest(), fetch(), normalize_cfpb() (+16 more)

### Community 4 - "Durable Source Intake"
Cohesion: 0.11
Nodes (39): current_bureau_id(), role(), writable(), accessible_jobs(), cell(), digest(), get_job(), import_detail() (+31 more)

### Community 5 - "Technical Design Boundaries"
Cohesion: 0.05
Nodes (30): Command, Command, Command, Migration, Authentication, files and reporting, Disabled shadow semantic20 FTS20 reference20 discovery, Immutable canonical Permanent ID, Case intelligence (+22 more)

### Community 6 - "Source Intake Interface"
Cohesion: 0.13
Nodes (35): api(), Case, csrf(), date(), errorText(), Escalation, labels, Page (+27 more)

### Community 8 - "Import Performance Measurement"
Cohesion: 0.09
Nodes (14): browser(), main(), Memory, request(), simulate(), main(), main(), simulate() (+6 more)

### Community 9 - "Institution Profile Interface"
Cohesion: 0.10
Nodes (27): CaseAction, CaseDetail, CoordinationAction(), CoordinationRecordPage(), CoordinationRequests(), CoordinationWorkspace(), Participant, Record (+19 more)

### Community 10 - "Frozen Model Matching"
Cohesion: 0.12
Nodes (3): Migration, Migration, main()

### Community 11 - "Serialization And Escalation"
Cohesion: 0.10
Nodes (14): action_query(), Meta, movements(), movements_csv(), MovementSerializer, confirmed_groups(), export(), chunks() (+6 more)

### Community 12 - "Import Validation Tests"
Cohesion: 0.11
Nodes (7): Command, swap_release(), ModelRelease, StagedEmbedding, DashboardTests, ImportTests, RolloutTests

### Community 13 - "Serialization And Escalation"
Cohesion: 0.12
Nodes (23): authorized_actions(), coordination(), scoped_cases(), active_cases(), enrich(), groups(), notices(), case_escalations() (+15 more)

### Community 14 - "Case Intelligence"
Cohesion: 0.08
Nodes (20): Migration, Migration, Additive migrations, Additive group retirement and literal fact-type schema, API additions, Current-model matching coverage distinct from zero matches, Source evidence and coordination snapshot triggers, Core incident intelligence (+12 more)

### Community 15 - "Case Intelligence"
Cohesion: 0.10
Nodes (20): Single aggregate for scoped movement event counts, analytics(), actions(), case_detail(), cases(), replay(), compute_dashboard(), Conflict (+12 more)

### Community 16 - "Frontend Package Configuration"
Cohesion: 0.07
Nodes (29): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+21 more)

### Community 17 - "Typed API Components"
Cohesion: 0.13
Nodes (24): ApiError, Attachment, categories, classifications, Dashboard, EvidenceComparison, Institution, InstitutionAction (+16 more)

### Community 18 - "Case Intelligence"
Cohesion: 0.12
Nodes (25): usePoll(), InstitutionCases(), change(), InstitutionCoordination(), InstitutionDirectory(), InstitutionHistory(), InstitutionOverview(), InstitutionProfilePage() (+17 more)

### Community 19 - "Frozen Model Matching"
Cohesion: 0.12
Nodes (14): Command, Command, refresh_active_matches(), baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch() (+6 more)

### Community 20 - "Case Intelligence"
Cohesion: 0.19
Nodes (23): edit_group(), FactInput, facts(), FactSerializer, feature(), flag_supporting_groups(), group_audit(), group_history() (+15 more)

### Community 21 - "Case Intelligence"
Cohesion: 0.13
Nodes (15): Batched overlap complaint serialization, overlap_data(), overlap_queryset(), overlaps(), review_snapshots(), decision_snapshot(), CaseAction, Meta (+7 more)

### Community 22 - "Browser Workflow Coverage"
Cohesion: 0.17
Nodes (6): endpoint, post(), stamp, post(), artifact(), root

### Community 23 - "Complaint Import Interface"
Cohesion: 0.18
Nodes (21): Bars(), ErrorNotice(), ExportButton(), start(), Facts, ImportDetail(), Imports(), isExport() (+13 more)

### Community 24 - "Import Performance Measurement"
Cohesion: 0.11
Nodes (5): Independent audit schema files and model restore verification, digest(), main(), run(), snapshot()

### Community 26 - "Escalation Readiness Tests"
Cohesion: 0.07
Nodes (6): InstitutionAdmin, InstitutionAdminForm, Meta, ReadOnlyAdmin, Command, Phase2MigrationTests

### Community 27 - "Database Schema Migrations"
Cohesion: 0.12
Nodes (7): Migration, Migration, Migration, Migration, Migration, Migration, Migration

### Community 28 - "Evidence Transaction Tests"
Cohesion: 0.18
Nodes (3): ConcurrentEvidenceTests, EvidenceFixture, EvidenceWorkflowTests

### Community 29 - "Institution Registry Administration"
Cohesion: 0.25
Nodes (13): page(), detail(), history(), institution_cases(), InstitutionHistorySerializer, InstitutionProfileSerializer, InstitutionWriteSerializer, Meta (+5 more)

### Community 30 - "Independent Research Review"
Cohesion: 0.11
Nodes (17): Private checksum-verified non-executing XLSX intake, ACSS public support-text source audit, ACSS public source audit — 2 November 2026, Quarantined support text pending privacy identity and incident review, Workbook rows and literal complaint labels are separate counts, Authorized Indian institution intake, Separately authorized encrypted institutional research intake, Two blind independent reviewers and third-party adjudication (+9 more)

### Community 31 - "Serialization And Escalation"
Cohesion: 0.21
Nodes (12): filtered_cases(), build_export(), case_values(), export_detail(), export_download(), exports(), get_export(), query() (+4 more)

### Community 32 - "Typed API Components"
Cohesion: 0.17
Nodes (15): Movement, AgeingPanel(), BureauWorkloadPanel(), ChartRow, CoordinationNotices(), HorizontalDistribution(), InstitutionMonitoringPanel(), InstitutionRow (+7 more)

### Community 33 - "Institution Profile Interface"
Cohesion: 0.13
Nodes (11): IncidentSummary(), Metric, metrics, Row, Summary, validSummary(), MyWork(), Boundary (+3 more)

### Community 36 - "Case Intelligence"
Cohesion: 0.14
Nodes (13): 10. Order, effort and decisions, 1. Outcome and verified starting point, 2. Requirement-to-code audit, 3. Milestone A — simpler official workspace, 5. Milestone C — source-grounded briefs and incident organization, 6. Milestone D — optional read-only MCP, 7. File-by-file execution backlog, 8. API and migration compatibility (+5 more)

### Community 37 - "Frontend Type Configuration"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 38 - "Serialization And Escalation"
Cohesion: 0.18
Nodes (8): Command, Attachment, ActionReadSerializer, ActionSerializer, AttachmentSerializer, InstitutionSerializer, Meta, ReviewSerializer

### Community 40 - "Local Runtime Dependencies"
Cohesion: 0.24
Nodes (12): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Incident groups forwarding defaults off (+4 more)

### Community 41 - "Browser Workflow Coverage"
Cohesion: 0.29
Nodes (10): csv(), ensureRB(), finish(), fixtures, manifest, post(), source(), stamp (+2 more)

### Community 42 - "Case Intelligence"
Cohesion: 0.18
Nodes (10): score(), Evidence contract, Output-only frozen-policy synthetic evaluation, Read APIs and interface, Relationship evidence v1 and decision snapshots, Review transaction and versioning, 4. Milestone B — explainable matching, evaluated before activation, Candidate discovery (+2 more)

### Community 43 - "Independent Restore Verification"
Cohesion: 0.40
Nodes (7): digest(), main(), run(), shell(), snapshot(), main(), snapshot()

### Community 44 - "Public Research Protocol"
Cohesion: 0.20
Nodes (8): B1.5: private public-data evaluation and independent annotation, Blind human review, Metric rules, Offline evaluation, Separate education consumer and government research tracks, Source gates, Storage and collection, Tests and results

### Community 45 - "Project Operation Guide"
Cohesion: 0.20
Nodes (10): Separate core incident counts and versioned coordination handoff, Data, permissions and demonstration, AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Reviewed facts and incident groups default off, Movement CSV serializer reuse follow-up, Physical disconnected startup requires separate evidence, Institution-first responsive portal UI follow-up, Prepare once while online (+2 more)

### Community 51 - "Typed API Components"
Cohesion: 0.25
Nodes (4): All-time coordination separate from receipt filters, DashboardHome(), Keyboard-submit institution-first home search, monthName()

### Community 53 - "Case Intelligence"
Cohesion: 0.25
Nodes (3): cases, post(), stamp

### Community 55 - "Browser Workflow Coverage"
Cohesion: 0.33
Nodes (3): post(), stamp, token()

### Community 59 - "Browser Workflow Coverage"
Cohesion: 0.43
Nodes (5): makeCase(), makeInstitution(), post(), stamp, token()

### Community 60 - "Browser Workflow Coverage"
Cohesion: 0.43
Nodes (5): createCase(), csrf(), escalate(), post(), stamp

### Community 61 - "Browser Workflow Coverage"
Cohesion: 0.38
Nodes (4): createInstitution(), csrf(), post(), stamp

### Community 62 - "Browser Workflow Coverage"
Cohesion: 0.38
Nodes (4): createCase(), csrf(), post(), stamp

### Community 63 - "Case Intelligence"
Cohesion: 0.40
Nodes (3): compare(), recorded(), Immutable evidence and policy at human decision time

### Community 64 - "Case Intelligence"
Cohesion: 0.33
Nodes (4): calibrate(), metrics(), Safe evaluation, EvaluationTests

### Community 65 - "Frozen Model Matching"
Cohesion: 0.40
Nodes (3): Command, eligible_corpus(), evaluate()

### Community 66 - "Import Performance Measurement"
Cohesion: 0.47
Nodes (3): main(), Memory, ticks()

### Community 69 - "Browser Workflow Coverage"
Cohesion: 0.40
Nodes (3): create(), post(), stamp

### Community 72 - "Plain Language Walkthrough"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, Open the prepared demonstration, What runs on the laptop

### Community 75 - "Test Type Configuration"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

### Community 77 - "Isolated Audit Stack"
Cohesion: 0.50
Nodes (3): Audit API bound to localhost port 8001, Isolated persistent audit PostgreSQL, Audit worker sharing isolated storage

### Community 78 - "Institution Profile Interface"
Cohesion: 0.50
Nodes (4): Responsive incident metric cards, Responsive navigation and mobile sign-out, Print layout hides interactive portal controls, Shared responsive government portal presentation

### Community 79 - "Source Navigation"
Cohesion: 0.83
Nodes (4): main(), run(), snapshot(), sql()

## Knowledge Gaps
- **178 isolated node(s):** `Participant`, `Record`, `Request`, `Meta`, `Attachment` (+173 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 536 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **57 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `save_group()` connect `Case Intelligence` to `Institution Registry Administration`, `Case Intelligence`, `Serialization And Escalation`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `_Base` connect `Analytics Export Tests` to `Escalation Readiness Tests`, `Analytics Filter Tests`, `Durable Source Intake`, `Institution Registry Administration`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `compute_dashboard()` connect `Case Intelligence` to `Case Intelligence`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `WorkflowTests` (e.g. with `Attachment` and `AuditEvent`) actually correct?**
  _`WorkflowTests` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Participant`, `Record`, `Request` to the rest of the system?**
  _178 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Escalation Readiness Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.051715309779825906 - nodes in this community are weakly interconnected._
- **Should `Escalation Readiness Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.06284153005464481 - nodes in this community are weakly interconnected._
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
nodes: 1545
unverified_code_nodes: 0
raw_edges: 3945
valid_candidate_edges: 3945
missing_endpoint_edges: 0
dangling_endpoint_edges: 0
external_reference_edges: 0
self_loop_edges: 16
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 3945
directed_same_endpoint_collapsed_edges: 0
undirected_unique_endpoint_pairs: 3943
undirected_same_endpoint_collapsed_edges: 2
same_endpoint_group_count: 0
relation_variant_groups: 0
source_file_variant_groups: 0
source_location_variant_groups: 0
context_variant_groups: 0
post_build_graph_type: DiGraph
post_build_edges: 3945
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

## Final source audit and worker recovery refresh

Source checkpoint 2dde701. Cached incremental extraction refreshed tests/research/acss_audit.py, tests/backend/test_source_audit.py, tests/operations/verify_core_worker.py, additions to tests/backend/test_core_incidents.py, and docs/research-permission-and-intake.md. The four code sources produced 38 AST nodes and 99 AST edges; updated documentation produced 15 semantic nodes and 17 semantic edges. Existing unrelated sources and supplemental CSS semantics were preserved.

ACSS is represented as documentation of a public support-text source audit, not as an independently validated complaint/incident corpus. The graph records quarantine, data/article licence discrepancy, non-executing checksum-verified intake and the distinction between workbook rows, literal labels, duplicate text and incident truth. Neither the collector nor network requests were executed during graph extraction. Curated reports/JSON/screenshots, raw datasets and source records remain excluded. Test and recovery helper coverage does not itself establish passing execution or model accuracy.

Current graph: 1,545 nodes / 3,945 directed edges / 115 communities, representing 165 source files. Supported corpus: 166 files, plus unchanged supplemental portal.css. Follow-up detection found zero changed/deleted permitted files. SHA-256 digests for every refreshed source are recorded in GRAPH_HEALTH.json; the supplemental stylesheet digest matches its prior recorded value. All graph node source paths are repository-relative. Integrity: zero missing/dangling endpoints, duplicates or directed collapses; 16 AST self-loops remain disclosed.

Historical cache/backups and untracked files were preserved; pre-refresh backup is refresh-backup-20261102-182747. No app/test source edits, commits, cloud APIs, raw private content or excluded tests/results content were used. Token measurements remain unavailable with zero placeholders. External acceptance, licensing/privacy review and independent incident-family annotation are not inferred from graph structure.
