# B1.5: private public-data evaluation and independent annotation

This is a separate research workflow. It does not import authentic complaints into the SIH portal, use Django/SQL, change model assets or change matching. The B1 synthetic benchmark remains a separate regression reference.

## Source gates

| Source | Intended track | Current gate |
| --- | --- | --- |
| [OIA case summaries](https://www.oiahe.org.uk/resources-and-publications/case-summaries/) | Education-summary transfer test, not original allegations or canonical-institution validation | Reuse permission unverified; the user explicitly requested collection remain pending. No case text collected |
| [CFPB database](https://www.consumerfinance.gov/data-research/consumer-complaints/) and [documented API](https://cfpb.github.io/api/ccdb/) | Published consumer-narrative robustness, optionally within genuinely recorded company identity | Publisher permits public data use/analysis; official API and bulk-export access returned HTTP 403 from this machine. No narrative corpus obtained |
| [NYC 311](https://data.cityofnewyork.us/d/erm2-nwe9) | Structured government workflow/representation probe | Reachable public API; minimal selected fields only. Not an education or narrative substitute |
| Authorized institutional complaints | Genuine institution-scoped incident retrieval | No dataset, permission or independent incident reference labels supplied |

The [OIA publication policy](https://www.oiahe.org.uk/media/nl0nxlte/publication-of-case-summaries-and-public-interest-cases.pdf) explains anonymization, not an identified corpus-reuse grant. NYC use follows its [Open Data policy](https://a860-gpp.nyc.gov/downloads/5712m8144?locale=en) and [NYC.gov terms](https://www.nyc.gov/main/terms-of-use): identify source, snapshot/version and modifications; no accuracy warranty is inferred. CFPB's explicit data-use statement is separate from its [general copyright/privacy notice](https://www.consumerfinance.gov/privacy/website-privacy-policy/); do not assume every consumer's narrative is a US-government-authored public-domain work.

Do not bypass source access controls, disable certificate verification or use unverified mirrors to conceal a blocker. Obtain a permitted official export or access restoration before collecting CFPB narratives. A future OIA permission reference must specify allowed local research processing and redistribution conditions before adding a collector. Nonpublic institution records require a separate authorization/privacy protocol.

## Storage and collection

Use a new ignored `data/research/` workspace. Configure Windows ACLs on its new parent before collection; files inherit the current user's explicit access. Container copies belong in a new root-owned mode-0700 temporary directory. Model assets remain the audit stack's read-only baseline. Do not put research text into the working or audit application databases.

```powershell
$privateParent = Join-Path (Get-Location) ('data/research/b15-' + (Get-Date -Format yyyyMMdd-HHmmss))
New-Item -ItemType Directory -Path $privateParent | Out-Null
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls $privateParent /inheritance:r /grant:r "${identity}:(OI)(CI)F"
if ($LASTEXITCODE -ne 0) { throw 'Private ACL setup failed' }
$corpus = Join-Path $privateParent 'corpus'
.venv/Scripts/python.exe -m tests.research.public_corpus --workspace $corpus --count 500
```

The bounded collector records source URL, collection date, usage conditions, response ETag/Last-Modified where supplied, response checksum, normalized-record checksum and combined corpus checksum. Unavailable dates remain null. Failed/blocked sources remain explicit in the manifest; an exit-0 manifest does not mean all sources were acquired. Use new directories for retries, preserving earlier attempts.

NYC fields are limited to request key, created/closed dates, agency, category, descriptor and status. Addresses, coordinates, contact fields and resolution narratives are not requested. The model representation is a labeled concatenation of structured category/descriptor fields, never described as an original citizen narrative. Company/agency identities are not institutions or Bureaus. Complaint outcomes are never relationship labels.

The CFPB normalizer retains the original published text privately and stores a separate automatically masked model representation with redaction counts. Regex masking is deliberately conservative and incomplete; manual re-identification review remains required. Do not claim the result is anonymous or publish it. Source record IDs, URLs, reviewer notes and annotation text remain private even when publicly retrievable.

## Offline evaluation

Use the isolated audit container, with no database/HTTP code path in the evaluator. Set a new private temporary location, copy the prepared corpus, and run:

```powershell
$audit = Get-Content tests/results/logs/readiness-run.json | ConvertFrom-Json
$env:AUDIT_RESULTS = $audit.directory
$containerCorpus = '/tmp/b15-' + (Get-Date -Format yyyyMMdd-HHmmss)
docker compose -p $audit.project -f compose.audit.yaml exec -T api python -c "from pathlib import Path; Path('$containerCorpus').mkdir(mode=0o700,exist_ok=False)"
docker compose -p $audit.project -f compose.audit.yaml cp "$corpus/." "api:${containerCorpus}"
docker compose -p $audit.project -f compose.audit.yaml exec -T api python -m tests.research.public_evaluation --workspace $containerCorpus --output-name evaluation
docker compose -p $audit.project -f compose.audit.yaml cp "api:${containerCorpus}/evaluation" "$corpus/evaluation"
```

The evaluator checks B1's exact revision, model-weight checksum and frozen calibration. It loads MiniLM locally on CPU with offline/local-files-only settings. Inputs above 256 tokenizer wordpieces are excluded and counted, with no silent truncation or rewritten complaint. It never trains, recalibrates, activates a model, or calls the production matcher.

Queries and references are distinct source records. Exact normalized text groups stay on one side; duplicate query representations are held out rather than counted as independent queries. There is no calibration or model selection. True incident groups and near-duplicate independence remain unknown in these sources, so this split does not establish unbiased incident accuracy. Existing B1 family-leakage tests continue to apply to its separate synthetic corpus.

Scopes differ deliberately: OIA would be an institution-unknown education transfer probe; CFPB uses genuinely published company identity; NYC uses genuinely published agency identity. Neither entity filter is canonical AICTE institution filtering. No dataset scores are pooled.

## Blind human review

Private output contains two separately shuffled reviewer CSVs plus a blank adjudication CSV. They include text, source references and categories, but omit scores, rankings and proposed labels. Generic header-only templates are in `tests/fixtures/annotation/`.

1. Use two distinct pseudonymous reviewer IDs. Each reviewer reads their own file independently, without seeing scores or the other's work. Keep source access and annotation files inside the private workspace.
2. Choose `same_incident` only where independent source evidence establishes the same event. Similar wording, common company/institution, dates or complaint outcomes alone are insufficient.
3. `related_issue` means distinct incidents with a supported common concern; `unrelated` needs a defensible distinction. Use `insufficient_evidence` whenever identity/event details do not establish a relationship. Never force uncertainty into unrelated.
4. Record the judgment, reason and evidence/source references for every pair. Do not copy names, private contact details or identifying source excerpts into a public report.
5. Bring both independent labels into the adjudication CSV. Equal labels use status `agreed` and the same final label. Disagreements require a distinct third reviewer, status `adjudicated`, final label and rationale. The validator rejects duplicate pair IDs, unaffiliated pairs, invalid labels and fake independence.
6. Freeze the corpus and retrieval result. Corrections/new permissions require a new version; do not silently reuse labels with changed input checksums.

Apply completed local adjudications without re-encoding or exposing text:

```powershell
# Example inside the audit container after copying the completed private CSV there.
docker compose -p $audit.project -f compose.audit.yaml exec -T api python -m tests.research.public_evaluation --workspace $containerCorpus --output-name evaluation --dataset nyc311 --adjudications "$containerCorpus/evaluation/nyc311-adjudication.csv"
```

This writes a new UUID-named aggregate result and preserves the initial report, raw inputs and prior judgments. No labels were filled by the coding agent. The annotation workflow is ready; independent review has not occurred.

## Metric rules

- Primary review-worthy Precision@5 is review-worthy returned pairs / all returned suggestions, available only with a nonempty set and 100% usable independent adjudication. `insufficient_evidence` is reviewed but unusable for this denominator. Partial label coverage is reported, never promoted to overall precision.
- With complete labels and at least two query clusters, precision uncertainty uses a fixed-seed 1,000-resample query-cluster bootstrap. This captures sampling uncertainty within this convenience sample, not population representativeness.
- Same-incident Recall@5 remains unavailable without independently established eligible same-incident references. Reviewing only returned suggestions cannot measure misses. Do not create paraphrases and label them independent real complaints.
- False-positive rate remains unavailable without an independently defined and labeled negative candidate population. Known unrelated returned suggestions may be counted without calling that count an FPR.
- Report overall no-suggestion rate separately from no-reference queries and threshold abstention among queries with eligible references.
- Category error rates remain unavailable without judgments; counts, eligibility, scope coverage and timing remain measurable. CPU warm inference and in-memory retrieval timing are not PostgreSQL latency, import performance or model-training estimates.

For genuine institution-scoped validation, obtain authorized, de-identified complaints with real institution identifiers and independently established incident families before designing that benchmark. This public transfer adapter deliberately refuses fabricated institution/incident mappings. See the [current results and blockers](../tests/results/public-evaluation-verification.md).
