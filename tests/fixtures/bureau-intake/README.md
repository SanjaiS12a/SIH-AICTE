# Fictional independent Bureau inputs

These are synthetic demonstration files, not AICTE exports or genuine complaint data. No external Bureau connection is implied. `manifest.json` records source identifiers, explicit column mappings and status translations for repeatable tests.

1. As coordinator, search the institution registry for `SIH-BUREAU-DEMO`. If absent, register **Sahaya Technical Institute (fictional)**, region **Southern**, district **Demonstration district**, using that Permanent ID.
2. Open **Import data**, select **Individual complaints**, enable **This is a Bureau source upload** and choose the source below. Keep its Source ID unchanged for future uploads.

| File | Source ID | Source Bureau | Status translations |
|---|---|---|---|
| `rb.csv` | `fictional-rb` | RB | Received → Registered; Scrutiny → Under review |
| `pgrc.csv` | `fictional-pgrc` | PGRC | Pending → Registered |
| `other.csv` | `fictional-other` | DEMO | Open file → Awaiting response |

3. Upload each file separately. Map its independently named columns to source reference, institution Permanent ID, Bureau, category, summary, description, receipt date and status, using the mapping in the manifest. Validate, inspect and confirm. Registration finishes separately from semantic matching.
4. Search the common institution. Its four cases retain three source systems and their original references. Original source statuses appear in case detail and CSV alongside the current portal status. All three current Bureaus produce an all-time coordination notice even without model inference.
5. Upload `rb.csv` again with the same configuration. Both rows are unchanged duplicates and there are still four cases. Portal workflow changes made since the first upload remain intact.
6. Upload `rb-changed.csv` as the same RB source. It proposes a source status change for `RB-2026-001`. Confirm the intake, follow **View all rows and source conflicts**, and review the incoming row against the current case. Keeping the portal record requires a reason, records an audit action and does not apply the incoming status or allegation. Any authorized portal correction uses the existing case workflow separately.
7. Upload `rb-unknown-institution.csv` using the RB configuration. The unknown Permanent ID is rejected; the importer must not guess or create the institution. The existing cases remain unchanged.
8. Open **Bureau-source uploads and reconciliation**. Inspect upload and acceptance times and unresolved conflict-row counts. These are local portal processing times, not upstream synchronization timestamps. A batch containing rejected, conflicting or disputed rows never advances the last fully successful acceptance time.

Continue through the institution's **Coordination → Agreed responsibilities and follow-up** link. Use the existing lead/participant, officer acknowledgment/completion and coordinator outcome workflow. A source status translation never transfers ownership, escalates or disposes of another case automatically.

Browser tests replace the common Permanent ID with a unique fixture ID to keep repeated test runs independent. Real source formats, authority rules and production integration still require validation.
