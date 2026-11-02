# Graph Report - SIH  (2026-11-02)

## Corpus Check
- 177 files · ~94,273 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1640 nodes · 4235 edges · 123 communities (57 shown, 66 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 406 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Independent Research Review
- Case Intelligence
- Import Performance Measurement
- Case Intelligence
- Case Intelligence
- Typed API Components
- Case Intelligence
- Frozen Model Matching
- Import Performance Measurement
- Typed API Components
- Database Schema Migrations
- Source Intake Interface
- Import Validation Tests
- Case Intelligence
- Evidence Transaction Tests
- Case Intelligence
- Frontend Package Configuration
- Case Intelligence
- Escalation Readiness Tests
- Durable Source Intake
- Complaint Import Interface
- Case Intelligence
- Durable Source Intake
- Serialization And Escalation
- Institution Registry Administration
- Institution Permission Tests
- Escalation Readiness Tests
- Import Validation Tests
- Technical Design Boundaries
- Escalation Readiness Tests
- Serialization And Escalation
- Serialization And Escalation
- Escalation Readiness Tests
- Coordination Completion Tests
- Independent Research Review
- Workflow Regression Tests
- Institution Registry Administration
- Institution Profile Interface
- Source Navigation
- Source Intake Interface
- Frontend Type Configuration
- Serialization And Escalation
- Import Performance Measurement
- Browser Workflow Coverage
- Case Intelligence
- Escalation Readiness Tests
- Escalation Readiness Tests
- Local Runtime Dependencies
- Browser Workflow Coverage
- Independent Restore Verification
- Independent Restore Verification
- Technical Design Boundaries
- Public Research Protocol
- Import Performance Measurement
- Project Operation Guide
- Case Intelligence
- Analytics Cohort Tests
- Analytics Export Tests
- Browser Workflow Coverage
- Analytics Movement Tests
- Case Intelligence
- Independent Research Review
- Browser Workflow Coverage
- Escalation Readiness Tests
- Analytics Scope Tests
- Analytics Snapshot Tests
- Analytics Reconciliation Tests
- Browser Workflow Coverage
- Browser Workflow Coverage
- Browser Workflow Coverage
- Browser Workflow Coverage
- Escalation Readiness Tests
- Institution Profile Interface
- Analytics Authorization Tests
- Browser Workflow Coverage
- Browser Workflow Coverage
- Coordination Workflows
- Institution Registry Administration
- Technical Design Boundaries
- Case Intelligence
- Plain Language Walkthrough
- Escalation Readiness Tests
- Analytics Counting Tests
- Analytics Date Tests
- Case Intelligence
- Source Navigation
- Test Type Configuration
- Case Intelligence
- Technical Design Boundaries
- Shadow Retrieval
- Isolated Audit Stack
- Institution Profile Interface
- Case Intelligence
- Bureau Fixture Documentation
- CSRF-protected Coordination sign-in form
- Coordination frontend HTML entrypoint
- Case Intelligence

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 66 edges
2. `Institution` - 56 edges
3. `CaseAction` - 51 edges
4. `WorkflowTests` - 48 edges
5. `ErrorBox()` - 37 edges
6. `usePoll()` - 35 edges
7. `scoped_cases()` - 31 edges
8. `api()` - 31 edges
9. `Loading()` - 31 edges
10. `Bureau` - 29 edges

## Surprising Connections (you probably didn't know these)
- `5. Milestone C — source-grounded briefs and incident organization` --references--> `ActionReadSerializer`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → backend/cases/serializers.py
- `2. Requirement-to-code audit` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `Review screen` --references--> `PairReview()`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → frontend/src/main.tsx
- `Read APIs and interface` --references--> `ActionReadSerializer`  [INFERRED]
  docs/evidence-v1.md → backend/cases/serializers.py
- `Twenty literal complaint narratives with ten unscored scaffolding pairs` --conceptually_related_to--> `candidate_rows()`  [INFERRED]
  docs/acss-annotation-handoff.md → tests/research/acss_packet.py

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/incident-summary.tsx -> frontend/src/imports.tsx`

## Communities (123 total, 66 thin omitted)

### Community 0 - "Independent Research Review"
Cohesion: 0.08
Nodes (26): evaluation_dataset(), seed_records(), Independent same-incident reference set before retrieval, manifest(), PublicEvaluationTests, RecallTests, collect(), digest() (+18 more)

### Community 1 - "Case Intelligence"
Cohesion: 0.06
Nodes (28): confirmed_groups(), Database count over distinct pending-pair endpoint union, export(), chunks(), records(), scope(), selected(), summary() (+20 more)

### Community 3 - "Import Performance Measurement"
Cohesion: 0.10
Nodes (7): browser(), Memory, main(), main(), simulate(), docker(), main()

### Community 4 - "Case Intelligence"
Cohesion: 0.06
Nodes (31): calibrate(), Command, eligible_corpus(), evaluate(), score(), metrics(), Immutable evidence and policy at human decision time, Evidence contract (+23 more)

### Community 5 - "Case Intelligence"
Cohesion: 0.10
Nodes (23): actions(), case_detail(), cases(), replay(), dashboard(), download(), institutions(), notifications() (+15 more)

### Community 6 - "Typed API Components"
Cohesion: 0.09
Nodes (34): ApiError, Attachment, CaseAction, CaseDetail, categories, categoryLabels, classifications, Dashboard (+26 more)

### Community 7 - "Case Intelligence"
Cohesion: 0.14
Nodes (34): CaseEscalations(), EscalationList(), EscalationQueue(), validEscalations(), usePoll(), InstitutionCases(), change(), InstitutionCoordination() (+26 more)

### Community 8 - "Frozen Model Matching"
Cohesion: 0.10
Nodes (18): Command, Command, refresh_active_matches(), baseline_runtime(), cached_encoder(), cached_tokenizer(), encoder(), match_batch() (+10 more)

### Community 9 - "Import Performance Measurement"
Cohesion: 0.07
Nodes (9): Django Q2 polling interval of 0.2 seconds, Independent audit schema files and model restore verification, digest(), main(), run(), snapshot(), SourceWorkbookAuditTests, candidate_rows() (+1 more)

### Community 10 - "Typed API Components"
Cohesion: 0.11
Nodes (31): categoryLabel(), csrf(), date(), Overlap, All-time coordination separate from receipt filters, DashboardHome(), cases(), Keyboard-submit institution-first home search (+23 more)

### Community 11 - "Database Schema Migrations"
Cohesion: 0.08
Nodes (13): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+5 more)

### Community 12 - "Source Intake Interface"
Cohesion: 0.10
Nodes (25): Case, labels, Page, User, IncidentSummary(), Metric, metrics, Row (+17 more)

### Community 15 - "Evidence Transaction Tests"
Cohesion: 0.11
Nodes (7): build_evidence(), compare(), recorded(), ConcurrentEvidenceTests, EvidenceContractTests, EvidenceFixture, EvidenceWorkflowTests

### Community 16 - "Case Intelligence"
Cohesion: 0.17
Nodes (24): edit_group(), FactInput, facts(), FactSerializer, feature(), flag_supporting_groups(), group_audit(), group_history() (+16 more)

### Community 17 - "Frontend Package Configuration"
Cohesion: 0.07
Nodes (28): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+20 more)

### Community 19 - "Escalation Readiness Tests"
Cohesion: 0.20
Nodes (20): audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput, ParticipantInput (+12 more)

### Community 20 - "Durable Source Intake"
Cohesion: 0.15
Nodes (16): accessible_jobs(), get_job(), ImportJob, ImportRow, configuration(), differences(), jobs(), Meta (+8 more)

### Community 21 - "Complaint Import Interface"
Cohesion: 0.18
Nodes (24): Bars(), categoryMap(), CategoryMapping(), CategoryPair, ErrorNotice(), ExportButton(), Facts, ImportDetail() (+16 more)

### Community 22 - "Case Intelligence"
Cohesion: 0.14
Nodes (14): Batched overlap complaint serialization, overlap_data(), overlap_queryset(), overlaps(), review_snapshots(), decision_snapshot(), CaseAction, OverlapCandidate (+6 more)

### Community 23 - "Durable Source Intake"
Cohesion: 0.19
Nodes (19): category_mapping(), cell(), digest(), import_detail(), import_errors(), import_report(), import_summary_csv(), imports() (+11 more)

### Community 24 - "Serialization And Escalation"
Cohesion: 0.18
Nodes (13): authorized_actions(), coordination(), current_bureau_id(), scoped_cases(), active_cases(), enrich(), groups(), notices() (+5 more)

### Community 25 - "Institution Registry Administration"
Cohesion: 0.09
Nodes (11): InstitutionAdminForm, Meta, compute_dashboard(), dashboard_data(), Command, simulate(), Command, Command (+3 more)

### Community 28 - "Import Validation Tests"
Cohesion: 0.14
Nodes (10): ReadOnlyAdmin, Command, swap_release(), Complaint, Meta, ModelRelease, Notification, StagedEmbedding (+2 more)

### Community 29 - "Technical Design Boundaries"
Cohesion: 0.10
Nodes (21): Migration, Authentication, files and reporting, Immutable canonical Permanent ID, Case intelligence, Complaint lifecycle, Authorized current-state brief and paginated history, Database relationships, SIH 26264 — implementation design (+13 more)

### Community 31 - "Serialization And Escalation"
Cohesion: 0.13
Nodes (7): action_query(), Single aggregate for scoped movement event counts, analytics(), Meta, movements(), movements_csv(), MovementSerializer

### Community 32 - "Serialization And Escalation"
Cohesion: 0.21
Nodes (12): filtered_cases(), build_export(), case_values(), export_detail(), export_download(), exports(), get_export(), query() (+4 more)

### Community 33 - "Escalation Readiness Tests"
Cohesion: 0.14
Nodes (3): MovementExportTests, AccountabilityTests, HomepageTests

### Community 35 - "Independent Research Review"
Cohesion: 0.12
Nodes (16): Private checksum-verified non-executing XLSX intake, ACSS public support-text source audit, ACSS public source audit — 2 November 2026, Quarantined support text pending privacy identity and incident review, Workbook rows and literal complaint labels are separate counts, Authorized Indian institution intake, Separately authorized encrypted institutional research intake, Two blind independent reviewers and third-party adjudication (+8 more)

### Community 37 - "Institution Registry Administration"
Cohesion: 0.30
Nodes (12): role(), page(), detail(), history(), institution_cases(), InstitutionHistorySerializer, InstitutionProfileSerializer, InstitutionWriteSerializer (+4 more)

### Community 38 - "Institution Profile Interface"
Cohesion: 0.23
Nodes (13): CoordinationAction(), CoordinationRecordPage(), CoordinationRequests(), CoordinationWorkspace(), Participant, Record, Request, validHistory() (+5 more)

### Community 39 - "Source Navigation"
Cohesion: 0.13
Nodes (14): Migration, Approve selected source changes, Categories and source provenance, Other and Needs categorization preserve unknown source labels, Bounded persisted source category mapping, Demonstration and limits, Scripted coordination scenario is not measured staff productivity, Operational workflow and isolated demonstration (+6 more)

### Community 40 - "Source Intake Interface"
Cohesion: 0.16
Nodes (14): api(), errorText(), ResolutionForm(), submit(), start(), Explicit conflict reload controls and retained drafts, FactReview(), review() (+6 more)

### Community 41 - "Frontend Type Configuration"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 42 - "Serialization And Escalation"
Cohesion: 0.31
Nodes (11): writable(), Conflict, case_escalations(), CreateEscalationSerializer, EscalationSerializer, Meta, queue(), records() (+3 more)

### Community 43 - "Import Performance Measurement"
Cohesion: 0.23
Nodes (7): main(), Memory, ticks(), digest(), main(), run(), snapshot()

### Community 48 - "Local Runtime Dependencies"
Cohesion: 0.24
Nodes (12): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Incident groups forwarding defaults off (+4 more)

### Community 49 - "Browser Workflow Coverage"
Cohesion: 0.29
Nodes (10): csv(), ensureRB(), finish(), fixtures, manifest, post(), source(), stamp (+2 more)

### Community 51 - "Independent Restore Verification"
Cohesion: 0.40
Nodes (7): digest(), main(), run(), shell(), snapshot(), main(), snapshot()

### Community 52 - "Technical Design Boundaries"
Cohesion: 0.20
Nodes (3): Audit-only demonstration bootstrap with scoped feature flags, Current-container worker initialization and detached Vite stdin, Wait-Worker()

### Community 53 - "Public Research Protocol"
Cohesion: 0.20
Nodes (8): B1.5: private public-data evaluation and independent annotation, Blind human review, Metric rules, Offline evaluation, Separate education consumer and government research tracks, Source gates, Storage and collection, Tests and results

### Community 54 - "Import Performance Measurement"
Cohesion: 0.24
Nodes (7): Four isolated controlled HTTP import workloads, main(), signature(), request(), simulate(), main(), main()

### Community 55 - "Project Operation Guide"
Cohesion: 0.20
Nodes (10): Separate core incident counts and versioned coordination handoff, Data, permissions and demonstration, AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Reviewed facts and incident groups default off, Movement CSV serializer reuse follow-up, Physical disconnected startup requires separate evidence, Institution-first responsive portal UI follow-up, Prepare once while online (+2 more)

### Community 59 - "Browser Workflow Coverage"
Cohesion: 0.36
Nodes (4): endpoint, @playwright/test, artifact(), root

### Community 61 - "Case Intelligence"
Cohesion: 0.25
Nodes (3): cases, post(), stamp

### Community 62 - "Independent Research Review"
Cohesion: 0.29
Nodes (7): Private provenance and independently shuffled blank review forms, Twenty literal complaint narratives with ten unscored scaffolding pairs, ACSS permission, privacy and annotation handoff, Permission privacy identity reference families and blind review gates, Narrower publisher conditions pending licence clarification, Restricted annotation preparation without evaluation clearance, Zero independent labels blocks model selection and accuracy claims

### Community 63 - "Browser Workflow Coverage"
Cohesion: 0.33
Nodes (3): post(), stamp, upload()

### Community 68 - "Browser Workflow Coverage"
Cohesion: 0.43
Nodes (5): makeCase(), makeInstitution(), post(), stamp, token()

### Community 69 - "Browser Workflow Coverage"
Cohesion: 0.43
Nodes (5): createCase(), csrf(), escalate(), post(), stamp

### Community 70 - "Browser Workflow Coverage"
Cohesion: 0.38
Nodes (4): createInstitution(), csrf(), post(), stamp

### Community 71 - "Browser Workflow Coverage"
Cohesion: 0.38
Nodes (4): createCase(), csrf(), post(), stamp

### Community 76 - "Browser Workflow Coverage"
Cohesion: 0.40
Nodes (3): post(), stamp, token()

### Community 77 - "Browser Workflow Coverage"
Cohesion: 0.40
Nodes (3): create(), post(), stamp

### Community 82 - "Plain Language Walkthrough"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, Open the prepared demonstration, What runs on the laptop

### Community 87 - "Source Navigation"
Cohesion: 0.80
Nodes (5): main(), columns(), run(), snapshot(), sql()

### Community 88 - "Test Type Configuration"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

### Community 93 - "Isolated Audit Stack"
Cohesion: 0.50
Nodes (3): Audit API bound to localhost port 8001, Isolated persistent audit PostgreSQL, Audit worker sharing isolated storage

### Community 94 - "Institution Profile Interface"
Cohesion: 0.50
Nodes (4): Responsive incident metric cards, Responsive navigation and mobile sign-out, Print layout hides interactive portal controls, Shared responsive government portal presentation

## Knowledge Gaps
- **194 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+189 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 579 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **66 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WorkflowTests` connect `Escalation Readiness Tests` to `Escalation Readiness Tests`, `Case Intelligence`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `_Base` connect `Analytics Export Tests` to `Case Intelligence`, `Analytics Filter Tests`, `Escalation Readiness Tests`, `Institution Registry Administration`, `Import Validation Tests`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _194 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Independent Research Review` be split into smaller, more focused modules?**
  _Cohesion score 0.07948568088836938 - nodes in this community are weakly interconnected._
- **Should `Case Intelligence` be split into smaller, more focused modules?**
  _Cohesion score 0.06183574879227053 - nodes in this community are weakly interconnected._
- **Should `Import Performance Measurement` be split into smaller, more focused modules?**
  _Cohesion score 0.09634551495016612 - nodes in this community are weakly interconnected._
- **Should `Case Intelligence` be split into smaller, more focused modules?**
  _Cohesion score 0.059800664451827246 - nodes in this community are weakly interconnected._
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
nodes: 1640
unverified_code_nodes: 0
raw_edges: 4235
valid_candidate_edges: 4235
missing_endpoint_edges: 0
dangling_endpoint_edges: 0
external_reference_edges: 0
self_loop_edges: 17
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 4235
directed_same_endpoint_collapsed_edges: 0
undirected_unique_endpoint_pairs: 4233
undirected_same_endpoint_collapsed_edges: 2
same_endpoint_group_count: 0
relation_variant_groups: 0
source_file_variant_groups: 0
source_location_variant_groups: 0
context_variant_groups: 0
post_build_graph_type: DiGraph
post_build_edges: 4235
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

## Operational workflow refresh provenance

Source checkpoint 99f77af on codex/operational-workflow. The cached incremental pass refreshed 27 code sources plus README, audit Compose and docs/operational-workflow.md. Changed-file AST produced 347 nodes and 1,230 edges; host semantics produced 39 nodes and 43 edges. No API, model, test, worker, controller or benchmark command was executed for this graph refresh.

New coverage includes category labels and bounded persisted ImportJob.category_mapping; additive migration 0018; coordinator-selected validated source changes; server-computed comparisons; institution-first version checks and CaseAction evidence; replay acknowledgment/idempotency without silently reapplying old source snapshots; Help/guide navigation; Audit-Demo bootstrap, scoped flags and dependency guards; duplicate replay instrumentation; related operational test implementations. Source status approval, assignment, incident grouping and agreed Bureau work remain independent. Human decisions remain authoritative and MiniLM policy stays frozen.

Current graph: 1,640 nodes / 4,235 directed edges / 123 communities, representing 176 source files. Supported corpus: 177 files plus supplemental portal.css. Follow-up detection found zero changed/deleted supported files. SHA-256 digests of all 30 refreshed sources are stored in GRAPH_HEALTH.json; supplemental CSS digest is separately recorded. Every node source path is repository-relative. Health: zero missing/dangling endpoints, duplicate edges or directed collapses; 17 AST self-loops remain disclosed.

The graph documents implementation and test coverage without claiming tests passed, benchmark throughput, staff productivity, model accuracy, privacy/licence clearance, brand-new-machine installation or physically disconnected startup. Running benchmark/result content was not inspected. Raw/private data, models, logs, synthetic fixture datasets, experiment outputs and all tests/results remain excluded. Caches, untracked work and prior backups were preserved; pre-refresh backup is refresh-backup-20261102-232207. No app/test source edits, commits or external APIs were performed. Token measurements remain unavailable with zero placeholders.
