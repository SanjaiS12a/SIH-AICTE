# Relationship evidence v1 and decision snapshots

Implemented in Case Intelligence Milestone B1. Evidence explains a suggestion; it is not an incident finding. The original MiniLM encoder, cosine threshold, same-institution exact search and nearest-five policy are unchanged.

## Evidence contract

`OverlapCandidate.evidence` remains the existing JSONField. No migration, new evidence table or historical backfill is required. New semantic suggestions and newly created manual relationships use `schema_version: 1`. Reviewed legacy relationships retain their original evidence unchanged; legacy pending suggestions upgrade only when matching is explicitly rerun.

| Field | Meaning / authoritative source |
| --- | --- |
| `schema_version` | `1` for this contract; absent means legacy |
| `discovery_method` | `same_institution_minilm_top5` or `manual_selection` |
| `matching_policy_revision` | `institution-exact-top5-v1` or `manual-pair-v1`, separate from encoder identity |
| `cosine_score` | Actual stored cosine for semantic discovery; `null` for unscored manual relationships |
| `encoder_revision` | Encoder revision used for semantic discovery; `null` for manual selection |
| `canonical_institution` | Left/right registry UUID, Permanent ID, name, recorded agreement and registry provenance |
| `comparisons` | Source system/reference/identity, category, recorded classification and incident date; each contains `left`, `right`, `state` |
| `provenance` | Complaint UUIDs and optimistic versions at evidence capture; recorded-field source |
| `incident_finding` | `unverified`; only a separate human relationship decision establishes the recorded interpretation |
| `limitations` | Interpretation limits displayed with the evidence |

The legacy `institution`, `shared_reference`, `categories`, `incident_dates` and `scope` keys remain. The original top-level `score`, `origin`, `model_revision`, `decision`, `reason` and `version` response fields keep their meanings.

Comparison states:

- `agrees`: both usable recorded values are equal; this is not independent verification.
- `differs`: both usable values are unequal; this does not automatically reject a relationship.
- `unknown`: at least one usable value is missing. An unclassified classification is unknown, not an affirmative match.
- `unverified`: no factual incident finding is established by this evidence.

Blank, whitespace-only and absent references contribute no shared evidence. Equal nonblank reference strings mean shared text only. `source_identity` compares the established `[source_system, source_reference]` key only when all parts are present; it does not identify an applicant or automatically determine an incident. Intake fingerprints and duplicate/conflict rules are unchanged. Nonblank source values retain their original equality semantics; there is no fuzzy reference matching.

## Review transaction and versioning

Both semantic reviews and manual relationships append one existing `CaseAction(kind='overlap_review')` for each complaint in the existing transaction. `changes.review_snapshot` contains:

```text
evidence                   exact deep copy of the evidence seen for that relationship version
matching_policy_revision   recorded policy, or null for legacy evidence
score / model_revision     original scalar contracts
origin                     semantic or manual
relationship_version       version after this human decision
decision / reason          deliberately recorded human judgment
reviewer                   user ID and display name
reviewed_at                the common review timestamp, ISO 8601
```

Failure to insert either history action rolls back the pair and both histories. Replays retain existing idempotency behavior. A real concurrent update with a stale version returns HTTP 409; no snapshot is written for a rejected update.

Matching reruns never change reviewed decisions, scores or evidence. For pending pairs, a changed score, encoder revision or evidence advances the relationship version, making an old review form stale. An identical rerun is idempotent. This closes the previous gap where evidence could change without invalidating a review version.

The existing append-only CaseAction protections preserve snapshots. They do not claim protection against a database administrator. No missing historical snapshots are invented.

## Read APIs and interface

Existing overlap responses add nullable `review_snapshot`, read from the most recent authoritative review action in a batched page query. `null` means the latest review has no recorded snapshot. Manual-creation responses include their recorded snapshot. No new endpoint or competing history store is introduced.

The comparison separates semantic evidence, metadata captured for the suggestion, current complaint columns and human judgment. A collapsible review-time snapshot is also available in case and institution histories. Legacy evidence is explicitly unversioned, and current metadata is not presented as reconstructed historical evidence.

Cross-Bureau comparison access remains coordinator/auditor only; mutation remains coordinator only. Existing `ActionReadSerializer` redacts every `overlap_review` changes payload and reason for restricted users, including snapshots, across case/institution history and movement JSON/CSV. Membership is recalculated through existing backend authorization. The frontend neither grants permissions nor receives hidden comparison data for officers.

## Safe evaluation

`evaluate_matching` evaluates the active frozen MiniLM threshold. It neither recalibrates production nor selects/promotes a model. The existing pure `calibrate` helper remains available to old offline callers, but the command does not call it.

Reports are new files inside ignored `RESULTS_DIR/runs/`; the command rejects production paths and existing outputs before model loading. Default output uses a unique directory. `--run-dir` identifies a run explicitly; `--output` is retained only for new files within that same safe root. Runtime changes during evaluation abort without publishing a misidentified report.

```powershell
# Isolated stack; use a fresh run name and the mounted evaluation fixture.
docker compose -p <audit-project> -f compose.audit.yaml exec -T api python manage.py evaluate_matching --data /tmp/b1-evaluation.json --run-dir /app/tests/results/runs/<unique-run>/evaluation
```

Family overlap, ambiguous IDs and conflicting labels are rejected. Missing/invalid records and excluded pairs/queries are reported. Exact normalized text shared across partitions is excluded from test. All declared query IDs are excluded from reference pools without relying on naming suffixes. Reference candidates share institution and test partition; explicit same-incident labels establish relevance. Unknown judgments never become unrelated labels. Missing vectors produce reported abstentions/misses.

Pairwise binary threshold precision is distinct from retrieved-suggestion precision. Overall retrieval precision is unavailable if some returned suggestions lack labels. Timing is in-memory exact cosine, not pgvector SQL latency or import/queue performance. The corpus remains explicitly synthetic; neither reported metrics nor performance targets establish actual AICTE accuracy. See the [B1 verification and evaluation report](../tests/results/case-intelligence-b1-verification.md).
