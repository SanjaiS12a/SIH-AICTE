# What this project does

This is an internal working portal for AICTE officials handling institution complaints and regulatory cases.

Example: the Regulation Bureau has a refund case about a college, while the Public Grievance Redressal Cell has another complaint about the same incident. An official can search the college, inspect both cases and their evidence, record the relationship, agree which officer will act, and track the outcome and deadlines.

The institution is the central record. Its profile contains Overview, Cases, History, Coordination and Reports. Each complaint keeps its own identity and history. Similarity suggestions require human review.

## Open the prepared demonstration

The isolated demonstration currently runs at **http://127.0.0.1:5174/**. Its data is separate from the preserved working database.

Sign in as `coordinator` with the local synthetic-audit password `Demo-only-26264!`. Search Institutions for **SIH-26264-DEMO** and open **Lotus Technical Institute**, a fictional institution.

- Coordinator: sees the Bureaus together, registers cases, reviews relationships, assigns responsibility and transfers cases.
- Bureau officer: sees currently authorized Bureau cases and their assigned coordination instructions.
- Auditor: inspects authorized consolidated information and history without changing cases.

The five primary sections are **Home**, **Institutions**, **My Work**, **Data Imports** and **Reports**. Open **My Work** for case queues, approaching deadlines and coordination work. Officers see current-Bureau cases and their own coordination instructions; auditors inspect without changing records. Detailed pages remain available through contextual links: source intake/upload history under Data Imports, and movements/cross-Bureau activity under Reports.

## First test: six understandable complaints

Use [start-here-6-cases.xlsx](tests/fixtures/sih-walkthrough/start-here-6-cases.xlsx). A [CSV copy](tests/fixtures/sih-walkthrough/start-here-6-cases.csv) contains the same rows.

1. Open **Data Imports**. Choose individual complaints and leave Bureau-source upload unchecked for this mixed-Bureau example.
2. Select the workbook and choose **Upload and preview**. The matching column names map automatically. Review the six rows, then **Confirm import**.
3. Open the report. For this import, expect **6 total, 5 open and 1 closed**. Two are under process. Overdue counts depend on the current date; two were overdue when generated on 1 November 2026.
4. Return to the institution profile. It shows its complete authorized history, including the prepared cases and the uploaded cases. Its all-time totals are intentionally larger than one import's report.
5. Inspect Coordination from the institution profile or **My Work → Coordination queue**. The two `TRAIN-REFUND-2026-A` reports describe the same fictional refund in RB and PGRC. Compare them, deliberately select a relationship and record a reason. Pending reviews have no preselected decision. The 2025 hostel-deposit complaint concerns a different applicant and incident; similar wording alone cannot establish a duplicate.
6. Agree responsibilities in the Coordination workspace. Designated officers acknowledge and complete their instructions; the coordinator records the outcome. A transfer changes current case ownership and adds history.
7. Open the report again or export CSV. Re-uploading the identical workbook should identify duplicates rather than create six more cases.

These are fictional demonstration scenarios. Their descriptions are not independently reviewed model-evaluation labels.

## Larger test: 1,000 rows

Use [load-test-1000-cases.xlsx](tests/fixtures/sih-walkthrough/load-test-1000-cases.xlsx) or its [CSV copy](tests/fixtures/sih-walkthrough/load-test-1000-cases.csv). It uses the 30 fictional `DEMO-0001` to `DEMO-0030` institutions prepared by `seed_demo`.

This tests imports, reporting and matching workload. It does not measure accuracy on real AICTE grievances. Stable source references make identical re-uploads retry-safe; changed rows become conflicts rather than overwriting original allegations. Do not regenerate dates and expect existing cases to be overwritten.

On the measured laptop, a separate 1,000-row Excel workload completed in about 53 seconds with ten users. The 10,000-row diagnostic took about 13 minutes while exposing a subsequently corrected reminder bottleneck. Timings vary; see the [readiness evidence](tests/results/readiness-verification.md).

## What runs on the laptop

React displays the portal and charts. It calls a Django API over localhost. PostgreSQL stores institutions, complaints and audit records. A Django Q worker processes imports, MiniLM matching and reminders. MiniLM runs locally on CPU with frozen weights and threshold.

Online preparation downloads dependencies and model assets once. Prepared operation uses those local assets, the database and worker. Docker Desktop must be running. The ordinary start command is `start.bat`; see [README](README.md) for preparation and the separate audit stack.

Physical-network-disconnected cold startup remains a separate verification gate. Absence of a cloud AI API alone does not prove it. The user authorized publication with this physical-offline verification still pending; offline readiness is not certified.
