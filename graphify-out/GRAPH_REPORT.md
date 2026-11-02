# Graph Report - SIH  (2026-11-02)

## Corpus Check
- 171 files · ~90,148 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1575 nodes · 3983 edges · 115 communities (55 shown, 60 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 356 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Independent Research Review
- Import Performance Measurement
- Frozen Model Matching
- Durable Source Intake
- Case Intelligence
- Source Intake Interface
- Escalation Readiness Tests
- Escalation Readiness Tests
- Technical Design Boundaries
- Database Schema Migrations
- Institution Profile Interface
- Import Validation Tests
- Serialization And Escalation
- Case Intelligence
- Case Intelligence
- Serialization And Escalation
- Typed API Components
- Frontend Package Configuration
- Case Intelligence
- Institution Registry Administration
- Case Intelligence
- Complaint Import Interface
- Institution Permission Tests
- Escalation Readiness Tests
- Import Performance Measurement
- Evidence Transaction Tests
- Serialization And Escalation
- Typed API Components
- Institution Profile Interface
- Coordination Completion Tests
- Case Intelligence
- Independent Research Review
- Workflow Regression Tests
- Browser Workflow Coverage
- Frontend Type Configuration
- Case Intelligence
- Serialization And Escalation
- Case Intelligence
- Import Performance Measurement
- Browser Workflow Coverage
- Escalation Readiness Tests
- Import Validation Tests
- Escalation Readiness Tests
- Case Intelligence
- Local Runtime Dependencies
- Browser Workflow Coverage
- Independent Restore Verification
- Case Intelligence
- Public Research Protocol
- Project Operation Guide
- Analytics Cohort Tests
- Analytics Export Tests
- Case Intelligence
- Case Intelligence
- Typed API Components
- Analytics Movement Tests
- Case Intelligence
- Browser Workflow Coverage
- Escalation Readiness Tests
- Analytics Scope Tests
- Analytics Snapshot Tests
- Analytics Reconciliation Tests
- Browser Workflow Coverage
- Browser Workflow Coverage
- Browser Workflow Coverage
- Browser Workflow Coverage
- Independent Restore Verification
- Case Intelligence
- Analytics Authorization Tests
- Browser Workflow Coverage
- Coordination Workflows
- Plain Language Walkthrough
- Escalation Readiness Tests
- Analytics Counting Tests
- Analytics Date Tests
- Test Type Configuration
- Escalation Readiness Tests
- Case Intelligence
- Isolated Audit Stack
- Institution Profile Interface
- Case Intelligence
- Source Navigation
- Institution Concurrency Tests
- Bureau Fixture Documentation
- CSRF-protected Coordination sign-in form
- Coordination frontend HTML entrypoint
- Case Intelligence

## God Nodes (most connected - your core abstractions)
1. `Complaint` - 57 edges
2. `Institution` - 50 edges
3. `WorkflowTests` - 48 edges
4. `CaseAction` - 44 edges
5. `scoped_cases()` - 37 edges
6. `usePoll()` - 34 edges
7. `role()` - 31 edges
8. `IntelligenceTests` - 28 edges
9. `InstitutionTests` - 28 edges
10. `Bureau` - 26 edges

## Surprising Connections (you probably didn't know these)
- `Read APIs and interface` --references--> `ActionReadSerializer`  [INFERRED]
  docs/evidence-v1.md → backend/cases/serializers.py
- `Fresh isolated synthetic source-selection diagnostic` --conceptually_related_to--> `run()`  [INFERRED]
  docs/core-intelligence.md → tests/research/core_retrieval.py
- `Literal source-preserving research representations` --conceptually_related_to--> `representations()`  [INFERRED]
  docs/core-intelligence.md → tests/research/representations.py
- `Versioned group retirement preserves authoritative history` --conceptually_related_to--> `save_group()`  [INFERRED]
  docs/core-intelligence.md → backend/cases/intelligence.py
- `5. Milestone C — source-grounded briefs and incident organization` --references--> `ActionReadSerializer`  [INFERRED]
  docs/plans/case-intelligence-2.0.md → backend/cases/serializers.py

## Import Cycles
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/management.tsx -> frontend/src/imports.tsx`
- 2-file cycle: `frontend/src/imports.tsx -> frontend/src/incident-summary.tsx -> frontend/src/imports.tsx`

## Communities (115 total, 60 thin omitted)

### Community 0 - "Independent Research Review"
Cohesion: 0.06
Nodes (36): evaluation_dataset(), seed_records(), Private provenance and independently shuffled blank review forms, Twenty literal complaint narratives with ten unscored scaffolding pairs, ACSS permission, privacy and annotation handoff, Permission privacy identity reference families and blind review gates, Narrower publisher conditions pending licence clarification, Restricted annotation preparation without evaluation clearance (+28 more)

### Community 1 - "Import Performance Measurement"
Cohesion: 0.07
Nodes (14): Django Q2 polling interval of 0.2 seconds, Four isolated controlled HTTP import workloads, browser(), main(), Memory, request(), simulate(), main() (+6 more)

### Community 2 - "Frozen Model Matching"
Cohesion: 0.07
Nodes (20): Command, Command, eligible_corpus(), Command, refresh_active_matches(), baseline_runtime(), cached_encoder(), cached_tokenizer() (+12 more)

### Community 3 - "Durable Source Intake"
Cohesion: 0.11
Nodes (38): current_bureau_id(), role(), writable(), accessible_jobs(), cell(), digest(), get_job(), import_detail() (+30 more)

### Community 5 - "Case Intelligence"
Cohesion: 0.09
Nodes (26): actions(), Batched overlap complaint serialization, case_detail(), cases(), replay(), Conflict, dashboard(), download() (+18 more)

### Community 6 - "Source Intake Interface"
Cohesion: 0.13
Nodes (35): api(), Case, csrf(), date(), errorText(), Escalation, labels, Page (+27 more)

### Community 7 - "Escalation Readiness Tests"
Cohesion: 0.08
Nodes (6): Notification, notify_escalation(), EscalationTests, MovementExportTests, AccountabilityTests, HomepageTests

### Community 8 - "Escalation Readiness Tests"
Cohesion: 0.10
Nodes (26): dashboard_data(), audit(), awaiting_acknowledgment(), detail(), filtered_records(), history(), Meta, OpenInput (+18 more)

### Community 9 - "Technical Design Boundaries"
Cohesion: 0.05
Nodes (28): Command, Command, Command, Migration, Authentication, files and reporting, Disabled shadow semantic20 FTS20 reference20 discovery, Immutable canonical Permanent ID, Case intelligence (+20 more)

### Community 10 - "Database Schema Migrations"
Cohesion: 0.08
Nodes (13): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+5 more)

### Community 11 - "Institution Profile Interface"
Cohesion: 0.10
Nodes (27): CaseAction, CaseDetail, CoordinationAction(), CoordinationRecordPage(), CoordinationRequests(), CoordinationWorkspace(), Participant, Record (+19 more)

### Community 12 - "Import Validation Tests"
Cohesion: 0.10
Nodes (7): Command, swap_release(), StagedEmbedding, DashboardTests, ImportTests, RolloutTests, HistoricalMigrationTests

### Community 13 - "Serialization And Escalation"
Cohesion: 0.09
Nodes (18): action_query(), Single aggregate for scoped movement event counts, analytics(), Meta, movements(), movements_csv(), MovementSerializer, compute_dashboard() (+10 more)

### Community 14 - "Case Intelligence"
Cohesion: 0.15
Nodes (27): edit_group(), FactInput, facts(), FactSerializer, feature(), flag_supporting_groups(), group_audit(), group_history() (+19 more)

### Community 16 - "Serialization And Escalation"
Cohesion: 0.14
Nodes (22): authorized_actions(), coordination(), scoped_cases(), active_cases(), enrich(), groups(), notices(), case_escalations() (+14 more)

### Community 17 - "Typed API Components"
Cohesion: 0.13
Nodes (24): ApiError, Attachment, categories, classifications, Dashboard, EvidenceComparison, Institution, InstitutionAction (+16 more)

### Community 18 - "Frontend Package Configuration"
Cohesion: 0.07
Nodes (28): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, recharts, devDependencies, @playwright/test (+20 more)

### Community 19 - "Case Intelligence"
Cohesion: 0.12
Nodes (25): usePoll(), InstitutionCases(), change(), InstitutionCoordination(), InstitutionDirectory(), InstitutionHistory(), InstitutionOverview(), InstitutionProfilePage() (+17 more)

### Community 20 - "Institution Registry Administration"
Cohesion: 0.14
Nodes (16): InstitutionAdmin, InstitutionAdminForm, Meta, page(), detail(), history(), institution_cases(), InstitutionHistorySerializer (+8 more)

### Community 22 - "Complaint Import Interface"
Cohesion: 0.18
Nodes (21): Bars(), ErrorNotice(), ExportButton(), start(), Facts, ImportDetail(), Imports(), isExport() (+13 more)

### Community 25 - "Import Performance Measurement"
Cohesion: 0.13
Nodes (5): Independent audit schema files and model restore verification, digest(), main(), run(), snapshot()

### Community 26 - "Evidence Transaction Tests"
Cohesion: 0.18
Nodes (3): ConcurrentEvidenceTests, EvidenceFixture, EvidenceWorkflowTests

### Community 27 - "Serialization And Escalation"
Cohesion: 0.21
Nodes (12): filtered_cases(), build_export(), case_values(), export_detail(), export_download(), exports(), get_export(), query() (+4 more)

### Community 28 - "Typed API Components"
Cohesion: 0.17
Nodes (15): Movement, AgeingPanel(), BureauWorkloadPanel(), ChartRow, CoordinationNotices(), HorizontalDistribution(), InstitutionMonitoringPanel(), InstitutionRow (+7 more)

### Community 29 - "Institution Profile Interface"
Cohesion: 0.13
Nodes (11): IncidentSummary(), Metric, metrics, Row, Summary, validSummary(), MyWork(), Boundary (+3 more)

### Community 31 - "Case Intelligence"
Cohesion: 0.12
Nodes (15): Migration, Migration, Additive migrations, Additive group retirement and literal fact-type schema, API additions, Current-model matching coverage distinct from zero matches, Source evidence and coordination snapshot triggers, Core incident intelligence (+7 more)

### Community 32 - "Independent Research Review"
Cohesion: 0.12
Nodes (16): Private checksum-verified non-executing XLSX intake, ACSS public support-text source audit, ACSS public source audit — 2 November 2026, Quarantined support text pending privacy identity and incident review, Workbook rows and literal complaint labels are separate counts, Authorized Indian institution intake, Separately authorized encrypted institutional research intake, Two blind independent reviewers and third-party adjudication (+8 more)

### Community 35 - "Frontend Type Configuration"
Cohesion: 0.13
Nodes (14): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+6 more)

### Community 36 - "Case Intelligence"
Cohesion: 0.22
Nodes (4): LiteralRepresentationTests, passages(), representations(), span()

### Community 37 - "Serialization And Escalation"
Cohesion: 0.18
Nodes (9): Command, Attachment, ActionReadSerializer, ActionSerializer, AttachmentSerializer, InstitutionSerializer, Meta, ReviewSerializer (+1 more)

### Community 38 - "Case Intelligence"
Cohesion: 0.15
Nodes (12): 10. Order, effort and decisions, 1. Outcome and verified starting point, 2. Requirement-to-code audit, 3. Milestone A — simpler official workspace, 6. Milestone D — optional read-only MCP, 7. File-by-file execution backlog, 8. API and migration compatibility, 9. Verification and delivery gates (+4 more)

### Community 39 - "Import Performance Measurement"
Cohesion: 0.23
Nodes (7): main(), Memory, ticks(), digest(), main(), run(), snapshot()

### Community 40 - "Browser Workflow Coverage"
Cohesion: 0.26
Nodes (10): csv(), ensureRB(), finish(), fixtures, manifest, post(), source(), stamp (+2 more)

### Community 44 - "Case Intelligence"
Cohesion: 0.27
Nodes (5): build_evidence(), compare(), recorded(), Immutable evidence and policy at human decision time, EvidenceContractTests

### Community 45 - "Local Runtime Dependencies"
Cohesion: 0.24
Nodes (12): Backend Python requirements, Django and Django REST Framework, pgvector Python integration, Django Q2 durable task worker, sentence-transformers, Django API service, PostgreSQL 17 with pgvector and persistent volume, Incident groups forwarding defaults off (+4 more)

### Community 46 - "Browser Workflow Coverage"
Cohesion: 0.25
Nodes (5): endpoint, @playwright/test, post(), artifact(), root

### Community 47 - "Independent Restore Verification"
Cohesion: 0.40
Nodes (7): digest(), main(), run(), shell(), snapshot(), main(), snapshot()

### Community 48 - "Case Intelligence"
Cohesion: 0.40
Nodes (3): evaluate(), corpus_fixture(), EvaluationSafetyTests

### Community 49 - "Public Research Protocol"
Cohesion: 0.20
Nodes (8): B1.5: private public-data evaluation and independent annotation, Blind human review, Metric rules, Offline evaluation, Separate education consumer and government research tracks, Source gates, Storage and collection, Tests and results

### Community 50 - "Project Operation Guide"
Cohesion: 0.20
Nodes (10): Separate core incident counts and versioned coordination handoff, Data, permissions and demonstration, AICTE institution monitoring and cross-Bureau coordination — SIH 26264, Reviewed facts and incident groups default off, Movement CSV serializer reuse follow-up, Physical disconnected startup requires separate evidence, Institution-first responsive portal UI follow-up, Prepare once while online (+2 more)

### Community 53 - "Case Intelligence"
Cohesion: 0.25
Nodes (7): calibrate(), metrics(), Output-only frozen-policy synthetic evaluation, Read APIs and interface, Relationship evidence v1 and decision snapshots, Review transaction and versioning, Safe evaluation

### Community 55 - "Typed API Components"
Cohesion: 0.25
Nodes (4): All-time coordination separate from receipt filters, DashboardHome(), Keyboard-submit institution-first home search, monthName()

### Community 57 - "Case Intelligence"
Cohesion: 0.25
Nodes (3): cases, post(), stamp

### Community 58 - "Browser Workflow Coverage"
Cohesion: 0.33
Nodes (3): post(), stamp, token()

### Community 63 - "Browser Workflow Coverage"
Cohesion: 0.43
Nodes (5): makeCase(), makeInstitution(), post(), stamp, token()

### Community 64 - "Browser Workflow Coverage"
Cohesion: 0.43
Nodes (5): createCase(), csrf(), escalate(), post(), stamp

### Community 65 - "Browser Workflow Coverage"
Cohesion: 0.38
Nodes (4): createInstitution(), csrf(), post(), stamp

### Community 66 - "Browser Workflow Coverage"
Cohesion: 0.38
Nodes (4): createCase(), csrf(), post(), stamp

### Community 69 - "Case Intelligence"
Cohesion: 0.33
Nodes (6): score(), Evidence contract, 4. Milestone B — explainable matching, evaluated before activation, Candidate discovery, Evaluation and data, Evidence contract before ranking changes

### Community 72 - "Browser Workflow Coverage"
Cohesion: 0.40
Nodes (3): create(), post(), stamp

### Community 74 - "Plain Language Walkthrough"
Cohesion: 0.40
Nodes (5): What this project does, First test: six understandable complaints, Larger test: 1,000 rows, Open the prepared demonstration, What runs on the laptop

### Community 78 - "Test Type Configuration"
Cohesion: 0.40
Nodes (4): compilerOptions, baseUrl, paths, @playwright/test

### Community 81 - "Isolated Audit Stack"
Cohesion: 0.50
Nodes (3): Audit API bound to localhost port 8001, Isolated persistent audit PostgreSQL, Audit worker sharing isolated storage

### Community 82 - "Institution Profile Interface"
Cohesion: 0.50
Nodes (4): Responsive incident metric cards, Responsive navigation and mobile sign-out, Print layout hides interactive portal controls, Shared responsive government portal presentation

### Community 84 - "Source Navigation"
Cohesion: 0.83
Nodes (4): main(), run(), snapshot(), sql()

## Knowledge Gaps
- **185 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+180 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 559 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **60 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `compute_dashboard()` connect `Serialization And Escalation` to `Case Intelligence`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Why does `dashboard_data()` connect `Escalation Readiness Tests` to `Serialization And Escalation`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _185 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Independent Research Review` be split into smaller, more focused modules?**
  _Cohesion score 0.05821917808219178 - nodes in this community are weakly interconnected._
- **Should `Import Performance Measurement` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._
- **Should `Frozen Model Matching` be split into smaller, more focused modules?**
  _Cohesion score 0.07337662337662337 - nodes in this community are weakly interconnected._
- **Should `Durable Source Intake` be split into smaller, more focused modules?**
  _Cohesion score 0.11294117647058824 - nodes in this community are weakly interconnected._
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
nodes: 1575
unverified_code_nodes: 0
raw_edges: 3983
valid_candidate_edges: 3983
missing_endpoint_edges: 0
dangling_endpoint_edges: 0
external_reference_edges: 0
self_loop_edges: 16
exact_duplicate_edges: 0
directed_unique_endpoint_pairs: 3983
directed_same_endpoint_collapsed_edges: 0
undirected_unique_endpoint_pairs: 3981
undirected_same_endpoint_collapsed_edges: 2
same_endpoint_group_count: 0
relation_variant_groups: 0
source_file_variant_groups: 0
source_location_variant_groups: 0
context_variant_groups: 0
post_build_graph_type: DiGraph
post_build_edges: 3983
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

Final code-only refresh at `967c1a5` includes the deterministic cancellation-response handshake in `tests/browser/dashboard.spec.ts`. No supported changes/deletions remain; source digests are in `GRAPH_HEALTH.json`. This confirms source navigation freshness, not test or release acceptance.
