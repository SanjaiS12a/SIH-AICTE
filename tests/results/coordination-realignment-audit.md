# AICTE 26264 — coordination correction audit

31 October 2026. Examined the working continuation branch after `2af2ddf`, not only the older `61f9d3e` snapshot referenced by the supplied reviews. Source code and tests are authoritative; the existing Graphify map was queried for callers before changes.

| Requirement | Verified implementation | Decision |
|---|---|---|
| Canonical institution identity, profiles and complete case histories | `backend/cases/institutions.py`, `models.Institution`, `frontend/src/institutions.tsx`; institution backend/browser regressions | Reuse |
| Current, simultaneous multi-Bureau activity without AI | `coordination.active_cases/groups/notices`; `test_coordination_completion.py` tests all-time scope, transfers, closure/reopening | Reuse; already corrected since the reviewed snapshot |
| Manual relationship labels without semantic scores | `relationships.manual/decide`, migration 0010, `relationships.tsx`; completion tests | Reuse; relationships do not assign administrative work |
| Shared lead, responsibilities, acknowledgment and completion | Previously absent from relationships, escalation and case-next-action models | Implement `CoordinationRecord` and unique per-Bureau `CoordinationParticipant`, migration 0011 |
| Safe officer participation | Existing strict case scopes must remain; granting access to all linked evidence would leak data | Separate explicitly addressed instruction inbox; current membership and designated officer checked on every request |
| Authoritative institutional history | Existing protected, append-only `CaseAction`; institution history reads authorized actions | Record each coordination event on every linked case transactionally; no second event/history store |
| Transfer, escalation, disposal and next-action dates | Existing case operations | Reuse independently; coordination never changes these implicitly |
| Management measures and movement reports | `analytics.py`, `management.tsx`, `/api/movements(.csv)` added since snapshot | Retain; add coordination event filter; defer further presentation redesign |
| Bureau-source update reconciliation and freshness | Existing import identity/conflict logic, but no complete three-source synchronization demonstration reviewed in this milestone | Next milestone; do not claim live AICTE integration |
| Full offline and asset recovery | Database and archive checks recorded in `completion-delivery.json`; isolated host-access rehearsal failed | Unverified end-to-end; physical disconnection not tested |

## Scope and contracts

The current corrective milestone completes administrative coordination first. Original MiniLM, existing stack, institution lookup contract, independent complaints, ownership and protected histories remain intact. No training, model replacement, new scale run or further dashboard redesign is part of this correction.

- `GET/POST /api/coordination-records`: coordinator creation; coordinator/auditor paginated list, optional institution/state filters.
- `GET /api/coordination-records/{uuid}`: consolidated management view, linked cases and participants.
- `GET /api/coordination-records/{uuid}/history`: paginated authoritative case actions. An event linked to N cases creates N case actions, explicitly labelled in the interface.
- `POST /api/coordination-records/{uuid}/actions`: optimistic version checking; designated current officers acknowledge/complete, coordinators revise responsibilities or close with an outcome.
- `GET /api/coordination-requests`: paginated officer-specific instructions only. No institution, other-case reference, relationship label, evidence, score or other participant metadata.

Opening requires at least two participating Bureaus, one or more independent cases from one canonical institution, all current case owners represented, a designated current officer per Bureau and a lead selected from those participants. Coordinator-authored instructions are explicitly shared with their recipient. The reason and other evidence are management-only. At most 50 cases may be linked to one record; this explicit input limit does not truncate institution case/history endpoints or their pagination.

Creation uses a submission UUID and payload fingerprint. Different reuse conflicts; identical retries return the recorded result. A record row lock serializes versioned mutations. Revision preserves prior actions and resets acknowledgment/completion of the changed task. Closure requires every task completed plus an outcome; closing coordination does not close complaints. The prototype uses `in_coordination` and `closed`, without inventing official AICTE approval stages. No implicit merge, automatic acknowledgment or automatic dispute resolution exists.

Existing cases, semantic evidence and reviewed relationships are not backfilled or rewritten. Migration 0011 creates new tables and constraints. A recovery branch `checkpoint/pre-accountable-coordination-2af2ddf` and ignored database backup `backups/before-coordination-workflow-20261031.dump` precede the working database migration. A full restore of this particular new backup has not yet been exercised.

## Demonstration

1. As coordinator, search an institution with RB and PGRC cases. Its all-time activity notice works independently of semantic matching and receipt-date filters.
2. Review or create a manual relationship with a reason, if the matters warrant it. An unrelated relationship remains unrelated.
3. Follow **Agreed responsibilities and follow-up** in the institution Coordination section. Select cases across server pages, participating Bureaus, officers, lead and shared instructions.
4. As each designated officer, open **Coordination actions**, acknowledge the addressed instruction, then complete it with a note. Other-Bureau evidence is unavailable.
5. As coordinator, inspect both completions and close coordination with an outcome. Read the events through the coordination record, institution history and movement report. Case status and ownership remain independent and can continue through existing operations.

Remaining delivery gates: separate multi-source consolidation demonstration, any further monitoring reorganization, full offline deployment rehearsal and final SIH sign-off. This milestone alone does not establish real AICTE workflow compliance.
