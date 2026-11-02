import { date, labels, classifications, categoryLabel } from "./api";
import type { MatchingEvidence, Overlap, ReviewSnapshot } from "./api";

const fields: Record<string, string> = {
  source_system: "Source system", source_reference: "Source reference", source_identity: "Source identity",
  category: "Category", classification: "Classification", incident_date: "Incident date",
};
const states: Record<string, string> = { agrees: "Agrees", differs: "Differs", unknown: "Unknown", unverified: "Unverified" };
function value(input: unknown, field: string) {
  if (input === null || input === undefined || input === "") return "Not recorded";
  if (Array.isArray(input)) return input.map(String).join(" / ");
  if (typeof input !== "string") return "Not recorded";
  return field === "incident_date" ? date(input) : field === 'category' ? categoryLabel(input) : field === "classification" ? classifications[input] || input : input;
}

function CapturedMetadata({ evidence, historical = false }: { evidence: MatchingEvidence; historical?: boolean }) {
  const comparisons = evidence.comparisons;
  return <>
    <p>Metadata captured for this evidence; current case details may have changed. Agreement is not proof of a common incident. Differences are review cues.</p>
    {evidence.provenance && <p>{evidence.provenance.source} · Captured case versions: A {evidence.provenance.left_case_version}, B {evidence.provenance.right_case_version}.</p>}
    {evidence.canonical_institution && <p>{evidence.canonical_institution.source}: {evidence.canonical_institution.left.name} · {evidence.canonical_institution.left.permanent_id}</p>}
    {comparisons && <div className="table-scroll" role="region" aria-label={historical ? "Review-time metadata" : "Metadata comparison"} tabIndex={0}>
      <table className="captured-evidence-table">
        <caption className="sr-only">Captured metadata values and comparison states; not verified incident findings</caption>
        <thead><tr><th scope="col">Field</th><th scope="col">Complaint A</th><th scope="col">Complaint B</th><th scope="col">State</th></tr></thead>
        <tbody>{Object.entries(fields).map(([key, label]) => {
          const comparison = comparisons[key];
          return <tr key={key}><th scope="row">{label}</th><td>{value(comparison?.left, key)}</td><td>{value(comparison?.right, key)}</td><td>{states[comparison?.state || "unknown"] || "Unknown"}</td></tr>;
        })}</tbody>
      </table>
    </div>}
    <p>Source identity means the recorded source-system/reference key. Equal reference text from different systems does not establish duplication.</p>
  </>;
}

export function PairEvidence({ pair: p }: { pair: Overlap }) {
  const e = p.evidence;
  const versioned = e.schema_version === 1;
  return <div className="evidence" aria-label="Matching evidence">
    <h3>Similarity signal</h3>
    <p>{typeof p.score === "number" ? `Cosine similarity: ${p.score.toFixed(3)}` : "Not model-scored"}</p>
    <p>Cosine similarity compares allegation wording. It is not a confidence percentage or duplicate probability.</p>
    <p>Encoder revision: {p.model_revision || "Not model-scored"}</p>
    {versioned ? <>
      <p>Evidence schema 1 · Discovery: {e.discovery_method === "manual_selection" ? "Manual selection" : e.discovery_method === "same_institution_minilm_top5" ? "Same-institution MiniLM top five" : "Not recorded"}</p>
      <p>Matching-policy revision: {e.matching_policy_revision || "Not recorded"}</p>
      <p>Evidence-stage finding: {states[e.incident_finding?.state || "unknown"] || "Unknown"}. The human judgment is recorded separately.</p>
    </> : <p className="policy-note">Legacy evidence (unversioned). Discovery and policy revision were not recorded; no historical provenance has been inferred.</p>}
    <small>{e.scope || "Evidence scope not recorded."}</small>
    <h3>Recorded metadata</h3>
    <p>Both cases belong to the same canonical institution. This does not confirm that they concern the same incident.</p>
    {versioned ? <CapturedMetadata evidence={e} /> : <>
      <p>Current recorded values below are not a reconstructed review-time snapshot.</p>
      <div className="table-scroll" role="region" aria-label="Metadata comparison" tabIndex={0}>
        <table><caption className="sr-only">Current metadata agreement or difference; not verified findings</caption>
          <thead><tr><th scope="col">Field</th><th scope="col">Comparison</th></tr></thead>
          <tbody>{[
            ["Category", p.left.category, p.right.category], ["Classification", p.left.classification === "unclassified" ? "" : p.left.classification, p.right.classification === "unclassified" ? "" : p.right.classification],
            ["Incident date", p.left.incident_date, p.right.incident_date], ["Source system", p.left.source_system, p.right.source_system], ["Source reference", p.left.source_reference, p.right.source_reference],
          ].map(([label, a, b]) => <tr key={label}><th scope="row">{label}</th><td>{!a?.trim() || !b?.trim() ? "Not recorded on one or both cases" : a === b ? "Same recorded value" : "Different recorded values"}</td></tr>)}</tbody>
        </table>
      </div>
    </>}
    {Array.isArray(e.limitations) && <ul className="evidence-limits">{e.limitations.filter(item => typeof item === "string").map(item => <li key={item}>{item}</li>)}</ul>}
  </div>;
}

export function ReviewEvidence({ snapshot }: { snapshot: unknown }) {
  if (!snapshot || typeof snapshot !== "object" || !("evidence" in snapshot) || !snapshot.evidence || typeof snapshot.evidence !== "object") return null;
  const s = snapshot as ReviewSnapshot;
  return <details className="review-snapshot">
    <summary>Review-time evidence snapshot</summary>
    <p>{labels[s.decision] || "Recorded decision"} · {s.reviewer?.name || "Reviewer not recorded"} · {s.reviewed_at ? new Date(s.reviewed_at).toLocaleString("en-IN") : "Review time not recorded"}</p>
    <p>{s.reason}</p>
    <p>Review-time cosine: {typeof s.score === "number" ? s.score.toFixed(3) : "Not model-scored"}</p>
    <p>Encoder revision: {s.model_revision || "Not model-scored"}</p>
    <p>Review-time matching policy: {s.matching_policy_revision || "Not recorded (legacy evidence)"}</p>
    {s.evidence.schema_version === 1 ? <CapturedMetadata evidence={s.evidence} historical /> : <p>Legacy evidence captured without a versioned metadata contract. {s.evidence.scope}</p>}
    <p className="muted">Immutable CaseAction evidence for relationship version {s.relationship_version}; current case metadata may differ.</p>
  </details>;
}
