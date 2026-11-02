# Six complaint records, one reviewed incident

All records in this folder are authored synthetic fixtures, with no real institution, person or independently reviewed incident labels.

1. In the isolated audit portal, register an institution with Permanent ID `CORE-DEMO-001` (any clearly fictional name/region).
2. Import `six-case-rb.csv` under source system `core-demo-rb`, and `six-case-pgrc.csv` under `core-demo-pgrc`. Map the institution permanent ID, source reference, Bureau, category, summary, description, receipt date and status. These are two independent source files, three records each. Existing source-intake status mapping uses `registered` → Registered.
3. Repeat either upload: identical records must be reconciled rather than creating new complaints.
4. Open the institution: six complaint records, current RB/PGRC responsibility and the all-time cross-Bureau notice should appear.
5. Inspect a genuine semantic suggestion. Compare the original descriptions and transaction reference `TX-CORE-DEMO-2026`; explicitly record a Same Incident relationship with a reason. A score alone is not a finding.
6. With `ENABLE_INCIDENT_GROUPS=1` on the **audit stack only**, create an explicit group with all six cases. Explain the source evidence in the reason; optionally attach the reviewed relationship ID.
7. Overview/Reports should show six complaints, one confirmed group and six distinct associated complaints. Pair counts are a separate measure; no complaint was merged.
8. Follow **Coordinate this incident**, use the reviewed group cases, select a lead Bureau and both current officers, and record agreed instructions. Each officer acknowledges and completes only their explicitly shared action. The coordinator records the outcome. Closing coordination must leave complaint statuses unchanged.
9. Inspect the membership timeline, case histories and scoped CSV exports. Correcting membership requires the current version; retirement retains history.

For a changed-year hard negative, use a separate clearly labelled fictional transaction and explain why shared refund wording alone is insufficient. If an extra complaint is registered, the total becomes seven; do not continue presenting it as six.

`representation-diagnostic.json` is a separate 13-record, six-query source-selection diagnostic. Its labels are synthetic and fixed before inference. The first paragraph is intentionally uninformative in query descriptions, with relevant evidence later in the original text. This tests passage coverage; it is not real-world model validation or an approved production retrieval policy.
