import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError, labels } from "./api";
import type { Page, User, Case } from "./api";
import { usePoll } from "./imports";
import { Heading, ErrorBox, Empty, Loading, Pagination, Badge } from "./ui";

type Source = {
  source_system: string;
  source_bureau__code: string;
  source_bureau__name: string;
  uploads: number;
  last_uploaded_at: string;
  last_registered_at: string | null;
  last_success_at: string | null;
  unresolved_conflict_rows: number;
  latest_job: string;
};
type Row = {
  differences?: {field:string;before:unknown;after:unknown;eligible:boolean;explanation:string}[];
  resolution?: {decision?:string;applied_fields?:string[]}|null;
  number: number;
  raw: Record<string, string>;
  data: Record<string, unknown>;
  state: string;
  error: string;
  version: number;
  current_case: Case | null;
  resolution_reason: string;
  resolved_at: string | null;
  resolved_by_name: string | null;
};
type SourceJob = {
  id: string; filename: string; source_system: string; source_bureau: string;
  state: string; created_at: string; registered_at: string | null;
  unresolved_conflicts: number; total_rows: number;
};

export function SourceJobs() {
  const [params, setParams] = useSearchParams();
  const { data, error } = usePoll<Page<SourceJob>>(`/api/source-intake/jobs?${params}`, 5000, 0, validSourceJobs);
  function change(key: string, value: string) {
    const p = new URLSearchParams(params); p.delete('page');
    if (value) p.set(key, value); else p.delete(key);
    setParams(p);
  }
  return <>
    <Heading eyebrow="SOURCE HISTORY" title="All Bureau-source uploads" subtitle="Complete upload history within your current import permissions, including older unresolved conflicts." />
    <div className="home-filterbar">
      <label>Source ID<input value={params.get('source') || ''} onChange={e => change('source', e.target.value)} maxLength={40} /></label>
      <label>Bureau code<input value={params.get('bureau') || ''} onChange={e => change('bureau', e.target.value)} maxLength={20} /></label>
      <label><input type="checkbox" checked={params.get('conflicts') === 'true'} onChange={e => change('conflicts', e.target.checked ? 'true' : '')} />Unresolved conflicts only</label>
    </div>
    <ErrorBox message={error} />
    {!data && !error && <Loading />}
    {data && <section className="panel card-body">{data.results.length ? <div className="table-scroll" role="region" aria-label="Source upload history" tabIndex={0}><table>
      <thead><tr><th>Upload</th><th>Source / Bureau</th><th>Uploaded</th><th>State</th><th>Rows</th><th>Unresolved conflicts</th></tr></thead>
      <tbody>{data.results.map(j => <tr key={j.id}>
        <td><Link to={`/imports/${j.id}`}>{j.filename}</Link></td><td>{j.source_system} / {j.source_bureau}</td>
        <td>{time(j.created_at)}</td><td>{j.state.replaceAll('_', ' ')}</td><td>{j.total_rows}</td>
        <td><Link to={`/imports/${j.id}/rows?state=conflict`}>{j.unresolved_conflicts}</Link></td>
      </tr>)}</tbody></table></div> : <Empty>No source uploads match these filters.</Empty>}
      <Pagination data={data} params={params} setParams={setParams} />
    </section>}
  </>;
}

function validSourceJobs(value: unknown) {
  const p = value as Page<SourceJob> | null;
  return !!p && Number.isSafeInteger(p.count) && p.count >= 0 && Array.isArray(p.results) && p.results.every(j => !!j &&
    ['id','filename','source_system','source_bureau','state','created_at'].every(k => typeof j[k as keyof SourceJob] === 'string') &&
    Number.isSafeInteger(j.total_rows) && j.total_rows >= 0 && Number.isSafeInteger(j.unresolved_conflicts) && j.unresolved_conflicts >= 0);
}
function time(value: string | null) {
  return value ? new Date(value).toLocaleString() : "Not recorded";
}
function validSources(value: unknown) {
  const p = value as Page<Source> | null;
  return (
    !!p &&
    Number.isInteger(p.count) &&
    Array.isArray(p.results) &&
    p.results.every(
      (s) =>
        !!s &&
        typeof s.source_system === "string" &&
        typeof s.source_bureau__name === "string" &&
        typeof s.source_bureau__code === "string" &&
        Number.isInteger(s.uploads) &&
        typeof s.latest_job === "string" &&
        Number.isInteger(s.unresolved_conflict_rows),
    )
  );
}
function validRows(value: unknown) {
  const p = value as Page<Row> | null;
  return (
    !!p &&
    Number.isInteger(p.count) &&
    Array.isArray(p.results) &&
    p.results.every(
      (r) =>
        !!r &&
        Number.isInteger(r.number) &&
        typeof r.state === "string" &&
        typeof r.error === "string" &&
        typeof r.resolution_reason === "string" &&
        (r.differences===undefined || (Array.isArray(r.differences) && r.differences.every(d=>d && typeof d.field==='string' && typeof d.eligible==='boolean' && typeof d.explanation==='string'))) &&
        (r.resolution==null || (typeof r.resolution==='object' && (r.resolution.decision===undefined || typeof r.resolution.decision==='string'))) &&
        !!r.data &&
        typeof r.data === "object" &&
        (r.current_case === null ||
          (!!r.current_case &&
            typeof r.current_case.id === "string" &&
            typeof r.current_case.institution?.name === "string" &&
            typeof r.current_case.summary === "string" &&
            Number.isInteger(r.current_case.version))) &&
        !!r.raw &&
        typeof r.raw === "object" &&
        Object.values(r.raw).every((v) => typeof v === "string") &&
        Number.isInteger(r.version),
    )
  );
}
function validJob(value: unknown) {
  const job = value as { registered_at: unknown } | null;
  return (
    !!job &&
    (job.registered_at === null || typeof job.registered_at === "string")
  );
}

export function SourceIntake() {
  const [params, setParams] = useSearchParams();
  const { data, error } = usePoll<Page<Source>>(
    `/api/source-intake?${params}`,
    5000,
    0,
    validSources,
  );
  return (
    <>
      <Heading
        eyebrow="MULTI-BUREAU CONSOLIDATION"
        title="Bureau-source uploads"
        subtitle="Independent Bureau files map to one institution registry. These are upload receipts, not live AICTE system connections."
      />
      <Link to="/imports" className="button">
        Upload Bureau records
      </Link>
      <Link to="/imports/source-jobs" className="button secondary">All upload history</Link>
      <label>
        Search source ID
        <input
          type="search"
          value={params.get("q") || ""}
          maxLength={80}
          onChange={(e) => {
            const p = new URLSearchParams(params);
            p.set("q", e.target.value);
            p.delete("page");
            setParams(p);
          }}
        />
      </label>
      <p className="muted">
        Last successful upload means every row was accepted or identified as an
        unchanged duplicate. Rejected, changed or disputed rows do not advance
        that timestamp. Registration and statistical reporting can finish while
        semantic matching is still pending. Times use your browser’s local
        timezone.
      </p>
      <ErrorBox message={error} />
      {!data && !error && <Loading />}
      {data && (
        <section className="panel card-body">
          {data.results.length ? (
            <div
              className="table-scroll"
              role="region"
              aria-label="Bureau source receipts"
              tabIndex={0}
            >
              <table>
                <thead>
                  <tr>
                    <th>Source / Bureau</th>
                    <th>Uploads</th>
                    <th>Last uploaded</th>
                    <th>Last intake completed</th>
                    <th>Last successful upload</th>
                    <th>Unresolved conflict rows</th>
                    <th>Latest upload</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((s) => (
                    <tr key={`${s.source_system}-${s.source_bureau__code}`}>
                      <th>
                        {s.source_system}
                        <span className="table-sub">
                          {s.source_bureau__name}
                        </span>
                      </th>
                      <td><Link to={`/imports/source-jobs?${new URLSearchParams({source:s.source_system,bureau:s.source_bureau__code})}`}>{s.uploads}</Link></td>
                      <td>{time(s.last_uploaded_at)}</td>
                      <td>{time(s.last_registered_at)}</td>
                      <td>{time(s.last_success_at)}</td>
                      <td><Link to={`/imports/source-jobs?${new URLSearchParams({source:s.source_system,bureau:s.source_bureau__code,conflicts:'true'})}`}>{s.unresolved_conflict_rows}</Link></td>
                      <td>
                        <Link to={`/imports/${s.latest_job}`}>
                          Inspect intake
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>
              No declared Bureau-source uploads in your current permission
              scope.
            </Empty>
          )}
          <Pagination data={data} params={params} setParams={setParams} />
        </section>
      )}
    </>
  );
}

function ReviewConflict({
  row,
  job,
  saved,
  user,
}: {
  row: Row;
  job: string;
  saved: () => void;
  user: User;
}) {
  const [decision,setDecision]=useState('keep_portal_record'),[fields,setFields]=useState<string[]>([]),[retain,setRetain]=useState(false),[reopen,setReopen]=useState(false);
  const [versions,setVersions]=useState<{row:number;case:number}|null>(null);
  function edit(){setVersions(old=>old??{row:row.version,case:row.current_case!.version});}
  const [reason, setReason] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [conflict, setConflict] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/api/imports/${job}/rows/${row.number}/resolve`, {
        method: "POST",
        body: JSON.stringify({
          expected_version: versions?.row??row.version,
          expected_case_version: versions?.case??row.current_case!.version,
          decision,
          fields: decision==='apply_selected_updates'?fields:[],
          retain_unselected:retain,
          confirm_reopen:reopen,
          reason,
        }),
      });
      saved();
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && e.status === 409) setConflict(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      className="action-form"
      onSubmit={submit}
      aria-label={`Review source conflict row ${row.number}`}
    >
      <p>
        Keeping the portal record records a review; it does not apply the
        incoming change. Use the authorized case workflow separately if a status
        or ownership correction is warranted. Original allegations remain
        immutable.
      </p>
      {row.differences && <div className="table-scroll" tabIndex={0} role="region" aria-label="Source changes compared with portal">
        <table><thead><tr><th>Field</th><th>Portal record</th><th>Incoming source</th><th>Permitted action</th></tr></thead><tbody>
          {row.differences.map(d=><tr key={d.field}><th>{d.field.replaceAll('_',' ')}</th><td><pre className="source-value">{JSON.stringify(d.before,null,2)}</pre></td><td><pre className="source-value">{JSON.stringify(d.after,null,2)}</pre></td>
            <td>{d.eligible && user.role==='coordinator' && decision==='apply_selected_updates' ? <label><input type="checkbox" checked={fields.includes(d.field)} onChange={e=>{edit();setFields(old=>e.target.checked?[...old,d.field]:old.filter(f=>f!==d.field));}}/>Apply {d.field.replaceAll('_',' ')}</label>:d.eligible?'Coordinator may select this update.':'Retain portal value.'}<p>{d.explanation}</p></td></tr>)}
        </tbody></table>
      </div>}
      {user.role==='coordinator' && row.differences && <label>Review decision<select value={decision} onChange={e=>{edit();setDecision(e.target.value);}}>
        <option value="keep_portal_record">Keep portal record</option><option value="apply_selected_updates">Apply selected metadata updates</option>
      </select></label>}
      {decision==='apply_selected_updates' && <>
        <p>Closing applies only to this complaint. Source disposal date and resolution note are recorded together; no other group member is closed. Bureau/officer changes use <Link to={`/cases/${row.current_case!.id}`}>the case workflow</Link>.</p>
        <label><input type="checkbox" required checked={retain} onChange={e=>{edit();setRetain(e.target.checked);}}/>Keep original allegations and all unselected/protected fields</label>
        {row.current_case?.status==='disposed' && row.data.status!=='disposed' && fields.includes('status') && <label><input type="checkbox" required checked={reopen} onChange={e=>{edit();setReopen(e.target.checked);}}/>Explicitly reopen this closed case</label>}
      </>}
      <ErrorBox message={error} />
      <label>
        {decision==='keep_portal_record'?'Reason for keeping portal record':'Reason for applying selected updates'}
        <textarea
          required
          rows={3}
          maxLength={2000}
          value={reason}
          onChange={(e) => {edit();setReason(e.target.value);}}
        />
      </label>
      {conflict && (
        <p role="alert">
          The case or source review changed. Your draft is retained until you
          explicitly reload.
        </p>
      )}
      <div className="form-actions">
        {conflict && (
          <button type="button" className="secondary" onClick={saved}>
            Reload row and discard draft
          </button>
        )}
        <button disabled={busy || conflict || (decision==='apply_selected_updates' && !fields.length)}>
          {busy ? "Recording…" : decision==='apply_selected_updates'?'Approve selected updates':'Keep portal record and record review'}
        </button>
      </div>
    </form>
  );
}

export function SourceRows({ user }: { user: User }) {
  const { id } = useParams();
  const [params, setParams] = useSearchParams(),
    [refresh, setRefresh] = useState(0);
  const { data: job, error: jobError } = usePoll<{
    registered_at: string | null;
  }>(`/api/imports/${id}`, 0, refresh, validJob);
  const { data, error } = usePoll<Page<Row>>(
    `/api/imports/${id}/rows?${params}`,
    0,
    refresh,
    validRows,
  );
  return (
    <>
      <Heading
        eyebrow="VALIDATION AND RECONCILIATION"
        title="Import rows and source conflicts"
        subtitle="All rows are available through server pagination. Incoming changes stay separate from accepted portal records."
      />
      <Link to={`/imports/${id}`}>Import overview and report</Link>
      <section className="panel card-body">
        <label>
          Row state
          <select
            aria-label="Row state"
            value={params.get("state") || "all"}
            onChange={(e) => {
              const p = new URLSearchParams(params);
              p.set("state", e.target.value);
              p.delete("page");
              setParams(p);
            }}
          >
            {[
              "all",
              "pending",
              "ready",
              "imported",
              "duplicate",
              "rejected",
              "conflict",
              "resolved",
            ].map((s) => (
              <option value={s} key={s}>
                {s === "resolved" ? "Conflict reviewed — portal retained" : s}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="secondary"
          onClick={() => setRefresh((n) => n + 1)}
        >
          Refresh rows
        </button>
        <a className="button secondary" href={`/api/imports/${id}/errors.csv`}>
          Download errors and conflicts CSV
        </a>
      </section>
      <ErrorBox message={error || jobError} />
      {!data && !error && <Loading />}
      {data && (
        <>
          {data.results.length ? (
            data.results.map((row) => (
              <article className="panel card-body" key={row.number}>
                <h2>
                  Row {row.number} —{" "}
                  {row.state === "resolved"
                    ? row.resolution?.decision==='apply_selected_updates'?'Reviewed - selected changes applied':'Conflict reviewed; portal record retained'
                    : row.state}
                </h2>
                {row.error && <p>{row.error}</p>}
                <details>
                  <summary>Incoming source values</summary>
                  <dl className="metadata">
                    {Object.entries(row.raw).map(([key, value]) => (
                      <div key={key}>
                        <dt>{key}</dt>
                        <dd>{value || "Not supplied"}</dd>
                      </div>
                    ))}
                  </dl>
                </details>
                {row.current_case && (
                  <section>
                    <h3>Current portal record</h3>
                    <Link to={`/cases/${row.current_case.id}`}>
                      {row.current_case.reference}
                    </Link>
                    <p>
                      <Link
                        to={`/institutions/${row.current_case.institution.id}`}
                      >
                        {row.current_case.institution.name}
                      </Link>
                    </p>
                    <p>{row.current_case.summary}</p>
                    <p>
                      Portal status: <Badge status={row.current_case.status} />{" "}
                      · Current Bureau: {row.current_case.bureau}
                    </p>
                    <p>
                      Accepted source status:{" "}
                      {row.current_case.source_status ||
                        "Not captured in legacy intake"}{" "}
                      · Incoming normalized status:{" "}
                      {typeof row.data.status === "string"
                        ? labels[row.data.status] || row.data.status
                        : "Not validated"}
                    </p>
                  </section>
                )}
                {row.state === "conflict" &&
                  row.current_case &&
                  ["coordinator", "officer"].includes(user.role) &&
                  (job?.registered_at ? (
                    <ReviewConflict
                      row={row}
                      user={user}
                      job={id!}
                      saved={() => setRefresh((n) => n + 1)}
                    />
                  ) : (
                    <p>
                      Confirm this intake and wait for registration to finish
                      before reviewing conflicts.
                    </p>
                  ))}
                {row.resolved_at && (
                  <p>
                    Reviewed by {row.resolved_by_name}: {row.resolution_reason}{" "}
                    · {time(row.resolved_at)}
                  </p>
                )}
              </article>
            ))
          ) : (
            <Empty>No rows match this state.</Empty>
          )}
          <Pagination data={data} params={params} setParams={setParams} />
        </>
      )}
    </>
  );
}
