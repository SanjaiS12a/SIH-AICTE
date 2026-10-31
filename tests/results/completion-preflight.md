# Completion preflight — 31 October 2026

Starting source `61f9d3e`, clean working tree; accepted implementation `266bd67` inspected. Continuation branch `feature/phase2-coordination-and-management`; recovery branch `checkpoint/pre-coordination-61f9d3e`. Main stays `5fba35f`.

| Requirement | Code evidence | Action |
|---|---|---|
| Institution registry/profiles/history | institutions.py, institutions.tsx; passing Phase 1 suites | Reuse |
| Classification/next actions | api.actions, models, migration 0008 | Reuse |
| Escalations/notifications | escalations.py, tasks.py, migration 0009 | Reuse/verify restart |
| Manual relationships | Existing OverlapCandidate/review and officer redaction; score currently required | Modify existing pair infrastructure |
| Cross-Bureau notices | api.compute_dashboard currently uses filtered receipt cohort and top ten | Modify to all-time current ownership; paginate detail |
| Management analytics | Existing scoped aggregates, charts, cache and shared filters | Extend; retain officer home |
| Imports/reports/exports | imports.py, exports.py, existing async/streamed paths | Reuse/audit |
| Recovery | New current backup fully restored to separate database; eight core table checksums match | Verify forward migrations/assets |
| Scale/worker/offline | Existing benchmark and recovery scripts; physical offline unverified | Update for current schema, measure isolated data; document actual limits |

No architecture rewrite, new model training, production model activation or existing-vector backfill is authorized by this increment. Source/tests remain authoritative where Graphify extraction is incomplete.
