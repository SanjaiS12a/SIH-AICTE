# Core incident intelligence

The application retains every independently received complaint. Semantic suggestions, reviewed pair decisions, explicit incident groups and agreed Bureau work are separate records.

## Scope and counts

The management-only incident summary uses the existing complaint filters and authorization. Both relationship endpoints must be inside the selected complaint scope. This intentionally differs from the legacy pending-pair review preview, whose either-endpoint scope is now named in Reports.

- `complaints`: distinct complaint IDs, never reduced by grouping.
- `pending_pairs`: distinct stored pairs awaiting review; not an exhaustive similarity count.
- `suggested_cases`: distinct union of those pairs' endpoint IDs.
- `same_incident_pairs` / `related_issue_pairs`: reviewed pair records in scope.
- `confirmed_groups`: active groups with no review flag, at least two active members, and either no supporting pair or a currently Same Incident supporting pair; each group must touch the selected scope.
- `grouped_cases`: distinct complaint IDs in scope belonging to any qualifying group. Overlapping membership is counted once.
- `ungrouped_cases`: scoped complaints outside those qualifying groups, including complaints with retired or provisional memberships only.
- `matching_complete`: complete state plus an embedding from the current model revision. Pending/failed/not-processed counts partition the remaining complaints; a missing or obsolete vector is not a confirmed zero-match result.

Institution overview and embedded institution Reports explicitly pass the institution filter alone and remain all-time. Management Reports pass their selected receipt filters. Group list rows distinguish scoped member count from all-time membership. A group touching two date cohorts can appear in both reports, so their group totals must not be added as a unique institutional total.

## API additions

All are session-authenticated. Group/intelligence endpoints require `ENABLE_INCIDENT_GROUPS=1`; defaults remain disabled. Coordinators can mutate, auditors can read, and officers cannot access group metadata, counts or exports.

| Endpoint | Behavior |
|---|---|
| `GET /api/incident-summary?<case filters>` | Count definitions, coverage, model revision and refresh timestamp |
| `GET /api/incident-summary/records?metric=<key>&page=N` | Authoritative server pagination for the selected metric |
| `GET /api/incident-summary.csv?metric=<key>` | Scoped streaming CSV, explicit complaint/relationship/group row types, formula escaping and export audit |
| `GET /api/incident-groups/{id}` | Current explicit membership, current Bureau/status/deadline and group version/state |
| `PATCH /api/incident-groups/{id}` | Existing full version-checked correction; `state=retired` retires the group |
| `GET /api/incident-groups/{id}/history?page=N` | Existing protected CaseAction rows, including complete before/after membership |
| `GET /api/cases?incident_group={id}` | Management-only membership filtering |
| `POST /api/coordination-records` | Optional `incident_group` and `expected_group_version`; all current group members must be explicitly selected |
| `GET /api/coordination-records?incident_group={id}` | Coordination records created from that group |

Existing lookup, case creation, report/export, relationship and coordination contracts are preserved; new fields are additive. Coordinator reason text supplies the supporting evidence narrative; an optional reviewed Same Incident pair provides a versioned relationship reference. Related Issue does not establish identical incident membership.

## Mutation and history

Group edits, retirement and member correction lock the institution, relevant relationship, group and cases inside the existing transaction pattern. Expected versions protect concurrent drafts with HTTP 409. CaseAction records remain authoritative and append-only; no new history store exists. A retired group cannot be reactivated silently: create a new justified group instead.

Changing a supporting relationship flags its groups for re-review. Provisional and retired groups are excluded from confirmed totals without deleting members. No automatic graph/transitive clustering, complaint merging, reassignment, disposal or case deadline changes occur.

Coordination stores the originating group ID/version. Later membership corrections do not silently alter that agreed record's case set or lifecycle. The constructor's case list is checked against the current group version and members under the institution lock. Officers see only their addressed instructions through the existing inbox, without restricted group metadata.

## Additive migrations

`0016_core_incident_counts` adds active/retired state and retirement timestamp, a validity index/constraint, nullable coordination group/version snapshots with a shape constraint, and literal fact-type choices for academic year/batch, allegation and topic. Existing groups default to active; their evidence/review flags and historical records are preserved.

`0017_core_evidence_protection` extends the existing source-span protection function without weakening immutable evidence checks and adds a coordination group snapshot trigger. It enforces same-institution source groups, current version/state at insertion and immutable group/version identity thereafter. Existing unknown Bureau-at-action snapshots and all append-only CaseAction protections remain unchanged.

## Source-preserving research

`tests/research/representations.py` creates separately versioned literal inputs: original summary, summary plus a declared selected original passage, and bounded paragraph/token passages. Each part retains field name, exact code-point offsets and source digest. Missing/over-limit inputs are explicit; no dates, facts, identity or remedies are inferred.

`tests/research/core_retrieval.py` refuses existing or working/demo databases and runs only in a fresh `coordination_core_research_*` database with the declared synthetic fixture. It reuses disabled `shadow.py` through a local settings override, records channel provenance, real cosine/ranks, bounds, SQL plans and timing, and stores experimental arrays separately. The production summary vectors, model revision, threshold and retrieval policy are unchanged.

The source-selection diagnostic is not permission to promote a model or policy. Its small authored labels cannot establish real AICTE accuracy. Independent authorized education labels, reviewer adjudication and known-positive reference families remain required before domain training or a meaningful model selection. No fine-tuning or external model/API dependency is introduced.

Use the [six-case walkthrough](../tests/fixtures/core-intelligence/README.md) and the consolidated implementation report under `tests/results/` for current executed evidence and remaining gates.
