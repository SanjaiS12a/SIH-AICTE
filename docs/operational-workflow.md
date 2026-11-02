# Operational workflow and isolated demonstration

The portal consolidates institutions by Permanent ID, retains independent complaints and records accountable cross-Bureau work. MiniLM suggests related summaries; officials decide relationships, categories and outcomes. Neither a similarity score nor a source upload proves an allegation or authorizes automatic disposal.

## Prepare and run

With Docker Desktop and the supported Node installation available:

```powershell
.\scripts\start.ps1 -Audit -Demo -Action Prepare
.\scripts\start.ps1 -Audit -Demo -Action Start
```

Open `http://127.0.0.1:5174/guide` and sign in using the configured demo account. Five primary sections remain unchanged; Help explains the workflow and bundles the existing fictional RB/PGRC CSVs. A coordinator registers `CORE-DEMO-001` when absent. Statistics come from authorized APIs, not example constants. Repeating a demonstration preserves previous decisions; it does not reset or reopen records.

`-Demo` requires `-Audit`. Missing audit metadata is initialized in ignored result storage with an isolated Docker project; existing metadata and volumes are preserved. Demo invocation scopes `DEMO_MODE`, reviewed facts and incident-group flags to its child services and restores the caller's environment. Normal defaults remain disabled. Preparation can build a missing local image and download only the pinned baseline when weights are absent; existing weights are verified, never silently repaired. Ordinary startup does not install dependencies or download models. Audit model mounts remain read-only outside explicit online preparation. Initial installation on a brand-new machine and physically disconnected startup are separate verification claims.

## Categories and source provenance

The existing six prototype categories gain `other` and `needs_categorization`. Missing/blank individual-complaint categories use Needs categorization; unknown nonblank labels require explicit mapping. Summary templates retain their required category. `GET /api/options` exposes `categories` and `category_labels`; authenticated session features add read-only `demo_mode`.

Uploads accept an optional `category_mapping` dictionary (or JSON in multipart requests). Keys are distinct, nonempty source labels of at most 80 characters; at most 50 mappings may target canonical choices. Unconfirmed previews can update that mapping. Original labels remain in ImportRow.raw, while the job stores its mapping. An additive migration adds ImportJob.category_mapping and updates category choices; no old case values are rewritten. Coordinators correct categories through the existing versioned case action endpoint using `kind=category` and a required reason. Embeddings and original text remain unchanged.

## Approve selected source changes

The existing `POST /api/imports/{job}/rows/{number}/resolve` retains `keep_portal_record`. Coordinators may additionally submit:

```json
{
  "decision": "apply_selected_updates",
  "fields": ["status"],
  "expected_version": 1,
  "expected_case_version": 3,
  "retain_unselected": true,
  "confirm_reopen": false,
  "reason": "Reviewed source evidence; retain original allegations and other case metadata."
}
```

Allowed logical fields are `status`, `category`, `classification` and `due_at`. Status includes source disposal date and resolution note. Closing validates that evidence against the existing case receipt and clears next actions; reopening requires explicit confirmation. Derived intake defaults cannot replace an existing deadline or classification. Bureau transfers and officer assignment remain separate authorized case actions. Unknown fields are never used as replacement values: values come from the validated stored source row.

Row responses add server-computed `differences` (before/after, eligibility and explanation) and `resolution`. The interface preserves drafts after HTTP 409 and requires explicit reload. Coordinator authority and current access are rechecked server-side. The institution is locked first, then the job, row and case. One transaction increments the case version, records selected changes and retained differences in the append-only CaseAction, resolves the row and adds an audit event. Only that complaint changes; group membership, other cases and coordination outcomes remain independent. The result is labelled Reviewed - selected changes applied, not fully synchronized.

The original submission fingerprint is preserved. Exactly repeated, previously reviewed source snapshots are acknowledged from CaseAction evidence, batch-fetched during preview, and never reapplied after later official actions. A new source fingerprint requires new review. Identical request retries return the prior result; different decisions against a resolved row conflict. Keeping the portal record remains available under the existing import permissions and does not apply incoming fields.

## Demonstration and limits

Demonstrate six independent Bureau complaints, one deliberately reviewed incident, accurate counts/list/CSV, a shared evidence request, two Bureau instructions and acknowledgments, and one approved source closure leaving five cases open. A separate controlled comparison uses two scripted independent requests versus one recorded simulated shared request. It measures scenario counts, not actual AICTE staff productivity.

Matching continues to use the original summary, the existing MiniLM revision and frozen threshold, exact same-institution search and at most five neighbors. It does not classify truth, assign legal authority, train automatically or implement a full regulatory adjudication process. Live AICTE integration, real-world incident accuracy, privacy/licence clearance and physical-offline verification remain separate gates.
