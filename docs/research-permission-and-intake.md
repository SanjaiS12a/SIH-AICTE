# Research intake and independent review

## ACSS public source audit — 2 November 2026

The [ACSS dataset, DOI 10.7910/DVN/EITGBB](https://doi.org/10.7910/DVN/EITGBB) is now verified as a public AICTE support-text source. Its current released Dataverse version 2.0 specifies **CC BY-NC 4.0**, whereas the [associated article](https://pmc.ncbi.nlm.nih.gov/articles/PMC11617942/) describes CC BY 4.0. Retain that discrepancy; do not describe the data as unrestricted for commercial training or redistribution.

Only the public XLSX was downloaded to an ignored, restricted research directory, using the official API and verifying its publisher checksum. No pickle was loaded, formula evaluated, raw record published, application case created or model trained. The aggregate audit is in `tests/results/core-acss-source-audit.json`; the reproducible collector is `tests/research/acss_audit.py`.

The workbook contains 14,272 nonempty rows, **not 14,272 complaints**. The literal Type label Complaint occurs 585 times. There are 14,265 complete literal subject/description rows, 3,715 repeated normalized text representations, 10,979 formula cells and 3,804 rows with potential identifier patterns. Pattern screening does not establish anonymity; repeated wording does not establish a duplicate incident. Seven subject formulas were excluded from literal narrative analysis.

Keep the source quarantined until privacy, formula handling, field meaning and genuine institution identity are reviewed. Its support/sentiment labels do not establish same-incident relationships. Independent incident-family annotation and a frozen evaluation split remain prerequisites for incident accuracy claims or domain model selection. This discovery updates earlier source availability findings, without retroactively validating earlier experiments.

OIA collection remains pending permission. No OIA corpus has been downloaded. The following is an **unsent draft**, for the project owner to send through the publisher's contact channel.

Subject: Permission request — local academic evaluation using published case summaries

We are developing a fictional demonstration of institution complaint monitoring for Smart India Hackathon problem 26264. May we retain a bounded selection of your published, anonymized education case summaries locally for non-commercial research into complaint similarity? We would retain source URLs and dates, distinguish your official summaries from original allegations, avoid identifying students, and publish only aggregate experimental results. We request permission for local normalization, sentence embeddings and independent human annotation, with no public redistribution of the corpus, no cloud model processing and no model training. Please specify permitted volume, retention, attribution, derivative-data restrictions and deletion requirements. We will not collect until the scope and permission reference are recorded. Please advise whether provider identities may be used or must be omitted.

## Authorized Indian institution intake

Do not upload genuine records into the demonstration database. Use a restricted, separately encrypted research directory and document an accountable institutional contact, authorization reference, collection purpose, permitted uses, retention/deletion date and approved reviewers. Permission for research is separate from permission to redistribute or train. No portal credentials or restricted scraping are accepted.

The institution supplies a minimised UTF-8 record export with its genuine institution identity, source record ID, source date, allegation or official-summary text and explicit text provenance. Keep original and normalized input separate with SHA-256 digests. Remove names, student IDs, contact details, account numbers and unnecessary addresses before transfer; automatic masking requires manual privacy review. Quarantine malformed records and tokenizer-overlength input rather than truncate silently. Preserve missing dates and unknown incident identity.

Document: fields, counts, missingness, duplicate text/source IDs, language, source licence/access conditions, genuine entity identity, exclusions and redaction status. Keep education, consumer and government-request evaluation tracks separate. Never substitute an agency for an AICTE institution or manufacture Permanent IDs.

## Reviewer handoff

The existing private B1.5 packet contains 28 NYC suggestion pairs, source links, independently shuffled reviewer-1/reviewer-2 CSVs and a blank adjudication CSV. Neither reviewer receives scores or the other's judgment. Each records a real identity, one of `same_incident`, `related_issue`, `unrelated`, `insufficient_evidence`, rationale and source evidence. Disagreement requires a third independent adjudicator. `final_labels` rejects self-adjudication and incomplete evidence. No genuine judgments are available yet; model accuracy remains unavailable.

## Recall reference-set protocol

Suggestion annotation alone cannot establish recall. An authorized source custodian must independently identify known same-incident records *before* viewing model output. Supply query/reference IDs, incident-family ID, evidence reference, two independent reviewer IDs, their labels and third-party adjudication when they differ. Preserve insufficient evidence. Include missed known positives, hard negatives, common boilerplate, different students/years/remedies and conflicting dates. Check all IDs exist, are distinct and belong to the same genuine eligible entity, with reference complaints present in the corpus. Split by independently established family and near-duplicate text; freeze calibration and test manifests before scoring. The validator in `tests/research/recall.py` rejects manufactured or incomplete provenance structures; it cannot certify that people actually performed review.

No verified same-incident reference set currently exists for these public records. Empty ground truth produces unavailable recall, not zero or 100%. Current synthetic fixture labels remain synthetic regression evidence. MCP has no approved per-user credential/handling policy and is intentionally absent; UTCP is deferred.
