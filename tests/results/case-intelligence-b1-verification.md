# Case Intelligence 2.0 — Milestone B1 verification

Date: 1 November 2026 (Asia/Calcutta). Scope: explainable matching evidence and safe evaluation only. Status: **B1 complete and verified on the feature branch; not merged or published**.

## Repository and isolation

- Starting local/remote `main`: `55f3804819b3d453fdaa07c8e4e25cb5442618a3`; clean worktree verified before branching.
- Feature branch: `codex/case-intelligence-b1`; recovery: `checkpoint/pre-case-intelligence-b1-55f3804`.
- Existing branches, ignored datasets/models/private assets/backups and Graphify artifacts were preserved. Previous graph outputs were copied into the ignored run directory before refresh.
- Audit project: `sih-readiness-115600`, API `8001`, bundled frontend preview `5174`, independent `coordination_audit` database/private volumes. Full Django tests use their separate test database. Browser fixtures write only to this isolated stack.
- Working demonstration database was not altered or reset. No training, embedding backfill, threshold/model promotion, lexical discovery, migrations, OCR, incident groups, MCP or UTCP was performed.

## Changes and compatibility

| File | Correction |
| --- | --- |
| `backend/cases/evidence.py` | Shared recorded-value comparison and versioned evidence builder for semantic/manual paths; exact decision snapshot helper |
| `backend/cases/matching.py` | Retain original candidate query, limit and threshold; produce evidence v1; advance pending-pair version only when evidence actually changes; preserve reviewed pairs |
| `backend/cases/relationships.py` | Snapshot exact evidence/policy/reviewer/time in both existing case actions transactionally, including manual creation; retain replay/version semantics |
| `backend/cases/api.py` | Batched latest snapshot lookup and additive nullable `review_snapshot` in authorized overlap responses |
| `backend/cases/management/commands/evaluate_matching.py` | Frozen-policy evaluation, safe new-file outputs, eligibility/metric denominators, explicit missing judgments, model-switch guard; no calibration writes |
| `frontend/src/api.ts`, `evidence.tsx` | Backward-compatible evidence/snapshot types; recorded metadata, provenance and historical snapshot presentation |
| `frontend/src/main.tsx`, `institutions.tsx`, `style.css` | Reuse PairReview and current case/institution timelines; avoid displaying nested snapshots as bogus before/after values; keyboard/mobile styles |
| `tests/backend/test_evidence.py` | Sixteen tests for source rules, unchanged selection, preservation, rollback, concurrency, redaction and evaluator safety |
| `tests/browser/evidence.spec.ts` | Five tests using real semantic/manual records plus controlled legacy presentation fixtures |
| `tests/browser/case-intelligence.spec.ts` | Existing long-text/missing-field presentation fixture explicitly represents legacy evidence; all assertions retained |
| `docs/evidence-v1.md`, test documentation and selected artifacts | Contract, reproduction, measured results and screenshots |

No database model or schema change. Existing top-level overlap fields retain their contracts; only `review_snapshot` is added. Legacy evidence remains valid, not retroactively rewritten. Decision snapshots use CaseAction, with no parallel history table. [Full evidence contract](../../docs/evidence-v1.md).

### Matching before versus after

| Behavior | Before B1 | After B1 |
| --- | --- | --- |
| Encoder | MiniLM revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | Unchanged |
| Threshold | `0.603080153465271` | Unchanged |
| Candidates | Exact pgvector cosine, same institution, nearest five, then threshold; closed cases included | Unchanged query/filter/order/limit |
| Blank reference equality | Could surface as shared evidence | Unknown, no shared evidence |
| Equal reference across different source systems | Undifferentiated shared reference | Shared textual value; source identity explicitly differs |
| Evidence provenance | Unversioned JSON | Schema 1; separate discovery/policy/encoder and recorded-field provenance |
| Human review | Decision and before/after audit | Same workflow plus exact immutable decision-time snapshot for both cases |
| Pending rerun | Evidence could change without a version change | Changed evidence advances version; identical rerun does not |
| Reviewed rerun | Preserve decision | Preserve decision, score, evidence and audit snapshot |
| Routine evaluation | Could overwrite active calibration | New ignored report only; protected paths/existing files rejected |

Candidate-selection regression compares all returned IDs with the original exact query on eight eligible/foreign fixtures, including a closed case and the top-five cap. It is a controlled policy regression, not a claim that millions of records were replayed. No all-pairs retrieval or new ranking was introduced.

## Evaluation: unchanged production model/policy

Raw synthetic fixture: `data/evaluation.json`, SHA256 `69f634af01869e7e98d2e95ca050ae795a893865d8415ae4cf1a68084fa37bab`. Labels: authored synthetic scenarios, independent human review pending. The fixture was not changed.

The audit found **38 exact normalized text groups shared across calibration/test**. Their 38 test records were excluded in memory. Raw partitions: 160 calibration / 240 test records. Eligible: 160 / 202, totaling 362. Raw 300 labeled pairs become 262 eligible pairs; test includes **60 same-incident, 60 related-issue, 22 unrelated pairs** (142 total). Excluding repeated negative endpoints changes the class mix; these filtered results are not directly comparable to historical full-fixture scores. Near-duplicate leakage and real-world validity remain unaudited.

| Metric | Measured result | Denominator / meaning |
| --- | --- | --- |
| Same-incident Recall@5 after threshold | **54/60 = 90%** | Explicitly relevant eligible query/reference pairs; six misses |
| Same-incident candidate recall before threshold | **60/60 = 100%** | Relevant pairs present in nearest five before cutoff |
| Query candidate coverage | **60/60 = 100%** | Queries with an eligible reference pool |
| Queries returning suggestions | **54/60 = 90%** | Six queries abstain because every candidate is below cutoff |
| Returned suggestions | **162** | Nearest-five results surviving frozen cutoff |
| Judgment coverage | **54/162 = 33.33%** | Suggestions with an explicit pair label |
| Precision on judged suggestions only | **54/54 = 100%** | Partial, same-incident-only judged subset; not overall precision |
| Overall suggestion precision | **Unavailable** | 108 returned suggestions are unjudged, not assumed negative |
| Pairwise binary threshold precision | **114/117 = 97.44%** | Explicitly labeled eligible pairs; same/related positive, unrelated negative; not retrieval precision |
| Pairwise binary recall / F1 | **114/120 = 95% / 96.20%** | Same binary rule, no three-class incident classification |
| Pairwise confusion matrix | **TP 114, FP 3, FN 6, TN 19** | 142 eligible test pairs |
| Unavailable vectors / embedding abstentions | **0 / 0** | All 362 eligible records encoded; all 60 query embeddings available |
| Three-class confusion matrix | **Unavailable** | Cosine threshold does not predict same incident versus related issue |

False-positive labeled pairs: `4-a/4-n` (0.753485), `22-a/22-n` (0.755852), `84-a/84-n` (0.620112). Missed same-incident pairs: families **18, 29, 47, 54, 72, 83**; each query's relevant reference was in the nearest five but below the frozen cutoff. Full ID-level scores and returned candidates are in the selected JSON report.

References exclude every declared query ID, share the query institution and test partition, and have explicit same-incident relevance labels. No threshold was chosen from held-out results; even calibration metrics use the frozen production threshold. Neither the 85% precision objective nor real AICTE accuracy is certified by this sparse synthetic corpus. B1 makes no candidate-policy activation.

Final guarded evaluation ran on CPU in a fresh process while browser regression was running: model load **15.763 seconds**, 362-record embedding **3.981 seconds**, in-memory exact retrieval total **3.512 ms**, query retrieval p95 **0.0809 ms**. These are evaluation timings, not isolated laptop benchmarks, PostgreSQL latency, upload/queue time or fine-tuning estimates. SQL latency is reported unavailable. The earlier preserved run measured 10.735/3.045 seconds; it is not substituted for the final run.

## Verification and security

| Check | Actual result |
| --- | --- |
| Final Django suite | **164 passed**, 66.853 seconds; exit 0 |
| Migration check | **No changes detected**, exit 0 |
| Final production build | **Passed**, 5,183 modules; 32.66-second Vite build; exit 0 |
| Focused B1 Edge suite | **5 passed**, 48.5 seconds; exit 0 |
| Complete Edge suite on final bundled assets | **68 passed**, 8.1 minutes; exit 0; all 63 existing regressions plus five B1 tests |
| Model/calibration/dataset byte checks | **Unchanged**, all three SHA256 hashes equal before/after |

Backend tests include two real concurrent reviews (one winner/one 409), identical snapshots in both actions, rollback if the second insertion fails, idempotent replay, preserved reviewed reruns, manual unscored evidence and rejected production/existing evaluation paths. Injected model failures in the broader suite are expected fault tests, not test failures.

Coordinator review, auditor read-only and officer denial are exercised against actual APIs. Officer snapshots/reasons are redacted through case detail, institution history, movements and CSV. Membership revocation takes effect on subsequent requests. Evidence renders only through existing authorized routes; no complaint text is sent to a new external service. Local model loading uses the audit stack's offline environment. This is not physically disconnected startup verification.

## Reproduction and artifacts

Run: `tests/results/runs/case-intelligence-b1-20261101-191019/` (ignored). Metadata: `tests/results/logs/case-intelligence-b1-run.json`. Logs and machine-readable exit codes are retained for focused/final backend, migrations, build, evaluation and browser checks. Earlier runs remain preserved.

```powershell
$audit = Get-Content tests/results/logs/readiness-run.json | ConvertFrom-Json
$env:AUDIT_RESULTS = $audit.directory
docker compose -p $audit.project -f compose.audit.yaml exec -T api python manage.py test cases --noinput
docker compose -p $audit.project -f compose.audit.yaml exec -T api python manage.py makemigrations --check --dry-run
docker compose -p $audit.project -f compose.audit.yaml cp data/evaluation.json api:/tmp/b1-evaluation.json
$evaluationName = 'b1-' + (Get-Date -Format yyyyMMdd-HHmmss)
$evaluationDir = "/app/tests/results/runs/$evaluationName/evaluation"
docker compose -p $audit.project -f compose.audit.yaml exec -T api python manage.py evaluate_matching --data /tmp/b1-evaluation.json --run-dir $evaluationDir
$env:API_PROXY_TARGET = 'http://127.0.0.1:8001'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5174'
$env:AUDIT_ARTIFACT_DIR = Join-Path (Get-Location) ('tests/results/runs/b1-browser-' + (Get-Date -Format yyyyMMdd-HHmmss))
Push-Location frontend
npm run build
npx playwright test
Pop-Location
```

The API/worker must be restarted in the isolated project after backend source changes; the prepared preview serves built assets on 5174. Audit container `/app/tests/results` is bound to the older run directory named by `$audit.directory`; the command prints its exact report path. Copy selected evidence into the new run without overwriting older artifacts.

Selected results: [evaluation JSON](case-intelligence-b1-evaluation.json), [desktop evidence/snapshot](case-intelligence-b1/desktop.png), [390px evidence/snapshot](case-intelligence-b1/mobile.png). The browser fixtures are fictional and the semantic example is genuinely scored by the frozen local worker. Legacy display edge cases use clearly intercepted synthetic responses.

## Handoff and limits

Graphify was refreshed from the feature working tree: **1,168 nodes, 3,231 edges, 86 communities**. Diagnostics report zero unverified code nodes, zero dangling endpoints and zero exact duplicate edges; 14 self-loops are retained. Its commit label refers to parent baseline `55f3804`, before the feature checkpoint. Source locations, extracted/inferred distinctions and directed edges are retained; community names use hub fallbacks and code extraction made no LLM calls. Nine unsupported CSS/batch/extensionless files remain outside symbol extraction. Source/tests are authoritative. Graph health is retained alongside the map.

The commit containing this report on `codex/case-intelligence-b1` is the final verified checkpoint, also retained as `checkpoint/case-intelligence-b1-verified`; the final delivery message records its hash. `main` remains at `55f3804`. No merge or push to main was performed.

Protected hashes: calibration `ec0e112d0dbef30765c2f9d3ae000617288c95ee159eec33ebb09741c6eb14b0`; weights `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`; dataset hash above. Exact command exit codes and before/after hash manifests remain in the ignored run directory.

B2 candidate expansion, training, OCR, extracted facts/groups and protocol integration are intentionally excluded. Physical offline readiness, production compliance, independent real complaint accuracy, million-record capacity and a clean larger-scale performance benchmark remain unverified. The sparse synthetic evaluation cannot establish overall suggestion precision or justify a production-policy change.
