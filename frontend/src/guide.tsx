import { Link } from 'react-router-dom';
import type { User } from './api';
import { Heading } from './ui';
import rb from '../../tests/fixtures/core-intelligence/six-case-rb.csv?url';
import pgrc from '../../tests/fixtures/core-intelligence/six-case-pgrc.csv?url';

export function Guide({user}:{user:User}) {
  const manager=['coordinator','auditor'].includes(user.role);
  return <>
    <Heading eyebrow="HELP" title="How this portal works" subtitle="Find the institution, understand the recorded evidence, coordinate the next action and retain accountability." />
    {user.features?.demo_mode && <p className="scope-note">Isolated fictional demonstration. Reviewed groups are enabled here; normal deployment defaults are unchanged.</p>}
    <section className="panel"><h2>One institution, independent complaints</h2>
      <p>The Permanent ID connects complaints even when their wording, category or Bureau differs. <Link to="/institutions">Search an institution</Link> to see its authorized cases and complete history.</p>
      <p>Automatic monitoring notices mean several Bureaus currently own open cases at the same institution. They do not prove duplicate incidents.</p>
      <p>The portal helps officers see earlier work, agree who collects evidence, assign instructions and record acknowledgments and outcomes. It does not decide whether an allegation is true.</p>
    </section>
    <section className="panel"><h2>What is automatic, and who decides?</h2><div className="table-scroll" tabIndex={0} role="region" aria-label="Decision responsibilities">
      <table><thead><tr><th>Information</th><th>How it is determined</th></tr></thead><tbody>
        <tr><td>Institution</td><td>Canonical Permanent ID lookup, never a guessed name match.</td></tr>
        <tr><td>Category</td><td>Structured input or explicit source mapping. Missing labels become Needs categorization; a coordinator records corrections.</td></tr>
        <tr><td>Administrative classification</td><td>Grievance, Regulatory / Compliance or Unclassified. This is a separate structured field corrected by a coordinator, not a MiniLM prediction.</td></tr>
        <tr><td>Matching progress</td><td>Background worker: pending, complete or failed. Failed does not mean no related cases.</td></tr>
        <tr><td>Possible relationship</td><td>MiniLM encodes the original summary into 384 numbers. Exact search returns up to five nearest summaries at the same institution above the frozen threshold. Cosine is not truth or duplicate probability.</td></tr>
        <tr><td>Confirmed incident</td><td>A coordinator reviews evidence and explicitly selects members. Related wording, different students or different years can describe distinct incidents.</td></tr>
        <tr><td>Status and Bureau</td><td>Authorized actions, not AI. Transfer, escalation, deadline and coordination are separate operations.</td></tr>
        <tr><td>Coordination outcome</td><td>Participants acknowledge and complete agreed instructions; the coordinator records an outcome. Cases remain independent.</td></tr>
      </tbody></table></div>
      <p>There is no automatic retraining, truth classification, legal Bureau routing or group-wide closure. Original descriptions and reviewed history remain available.</p>
      <p>Categories are prototype choices, not a verified official AICTE taxonomy. Matching uses only the original summary (limited to 256 model wordpieces), not the full description. Five retrieved candidates are not an exhaustive count of similar complaints.</p>
    </section>
    <section className="panel"><h2>Follow a complaint through the portal</h2><ol>
      <li><Link to="/imports">Inspect CSV/XLSX intake</Link> or {user.role==='auditor'?'ask an authorized officer to register a complaint':<Link to="/cases/new">register a complaint</Link>}. Validation checks dates, source identity, categories and your permissions.</li>
      <li>Preview records and correct unknown institution IDs. Summary datasets remain separate from complaint records. PostgreSQL becomes the case store, not the spreadsheet.</li>
      <li>Open the institution profile. Read current ownership, original allegations, previous actions and due dates. Statistics do not need to wait for matching.</li>
      <li>{manager ? <Link to="/coordination">Inspect suggestions and cross-Bureau work</Link> : <Link to="/work">Open your authorized work</Link>}. Compare summaries and full original descriptions before recording any relationship.</li>
      <li>A coordinator can create a reviewed incident group, then agree a lead and Bureau instructions. Each officer acknowledges their own instruction in My Work.</li>
      <li><Link to="/imports/sources">Review later source uploads</Link>. Changed records do not silently overwrite a case. Coordinators explicitly choose permitted metadata updates; transfers and assignment use the case workflow.</li>
      <li>Check <Link to="/reports">filtered reports and exports</Link> and the case history. Closing one member does not close the other complaints.</li>
    </ol><p><Link to="/cases?category=needs_categorization">Find cases needing categorization</Link>. Officers see only currently authorized cases; auditors inspect without modifying.</p></section>
    <section className="panel"><h2>Try the six-complaint demonstration</h2>
      <p>These files contain only fictional data. A coordinator registers fictional institution Permanent ID <code>CORE-DEMO-001</code>, then authorized officials import three records from each Bureau under source IDs <code>core-demo-rb</code> and <code>core-demo-pgrc</code>.</p>
      <p><a className="button secondary" href={rb} download="six-case-rb.csv">Download fictional RB CSV</a> <a className="button secondary" href={pgrc} download="six-case-pgrc.csv">Download fictional PGRC CSV</a></p>
      <p>Repeat an upload to check duplicates. Review a relationship, explicitly create one supported group containing the six records, then open coordination from that group. Inspect the actual institution counts and CSV; the example does not merge records.</p>
      <p>Approve a later source closure for one case. The other five remain independent. An extra unrelated or uncategorized complaint increases the actual total; do not continue calling that a six-record dataset.</p>
      {!user.features?.incident_groups && <p>Group controls require coordinator/auditor access and an enabled environment. The isolated demo startup command is <code>.\scripts\start.ps1 -Audit -Demo -Action Start</code>; first prepare with <code>-Action Prepare</code>. This page grants no permissions.</p>}
    </section>
    <section className="panel"><h2>Freshness, speed and Docker</h2>
      <p>The data comes from manual entry and successful Bureau uploads. There is no verified live AICTE integration. Visible dashboards poll approximately every five seconds; imports poll approximately every two seconds while visible.</p>
      <p>Historical synthetic laptop measurements (2 November 2026, about 16 GB RAM, CPU MiniLM): 1,000 rows completed matching/reporting in 39.6 seconds; 10,000 in 595.2 seconds after confirmation. Preview time is additional. These are measured examples, not promises or automatic category-classification timings.</p>
      <p>Docker runs PostgreSQL/pgvector, the Django API and one background worker consistently. The frontend runs locally. It adds Windows/WSL overhead, but the database and model also need memory outside Docker. This milestone retains the tested setup.</p>
      <p>Docker packages services; it is not the complaint algorithm. Native services are possible but require separate installation and process management.</p>
      <p>Pending/closed counts, source claims, evidence findings and official decisions are different concepts. Real-world model accuracy, official workflow compliance and physically disconnected startup remain unverified. The 30-day deadline is a demonstration policy, not an AICTE rule.</p>
    </section>
  </>;
}
