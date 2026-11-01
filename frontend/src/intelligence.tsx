import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api, ApiError, date, labels } from './api';
import type { Case, User, Page } from './api';
import { usePoll } from './imports';
import { ErrorBox, Loading, Empty } from './ui';

type Brief = { generated_at: string; allegation_label: string; case: Case; pending_escalation: boolean;
  latest_action: { kind: string; reason: string; created_at: string } | null;
  responsibilities: { instruction: string; bureau: string; officer: string; action_date: string | null; acknowledged_at: string | null }[];
  relationship_status?: { awaiting_review: number; same_incident: number; related_issue: number } };

export function CaseIntelligence({ id, user }: { id: string; user: User }) {
  const [open, setOpen] = useState(false);
  return <section className="panel"><details onToggle={e => setOpen(e.currentTarget.open)}>
    <summary className="panel-heading">Case brief: current responsibilities</summary>
    {open && <BriefContent id={id} user={user} />}
  </details></section>;
}

function BriefContent({ id, user }: { id: string; user: User }) {
  const { data, error } = usePoll<Brief>(`/api/cases/${id}/brief`, 5000, 0, validBrief);
  return <div className="card-body"><ErrorBox message={error} />{!data && !error && <Loading />}{data && <>
    <p className="muted">Current records, refreshed {new Date(data.generated_at).toLocaleTimeString('en-IN')}. This brief does not establish legal findings.</p>
    <p><strong>{data.case.reference}</strong> · <Link to={`/institutions/${data.case.institution.id}`}>{data.case.institution.name}</Link> · {data.case.institution.permanent_id}</p>
    <h3>{data.allegation_label}</h3><p>{data.case.summary}</p>
    <p>Responsible Bureau: {data.case.bureau}. Assigned officer: {data.case.assigned_name || 'Unassigned'}.</p>
    <p>Current status: {labels[data.case.status] || data.case.status}. Category: {data.case.category}. Classification: {data.case.classification.replaceAll('_',' ')}.</p>
    <p>Received: {date(data.case.received_at)}. Recorded incident date: {date(data.case.incident_date)}. Case deadline: {date(data.case.due_at)}.</p>
    <p>Next official action: {data.case.next_action || 'Not recorded'} · {date(data.case.next_action_date)}.</p>
    <p>Supervisory escalation: {data.pending_escalation ? 'Pending' : 'None pending'}.</p>
    <p>Latest authorized action: {data.latest_action ? `${data.latest_action.kind.replaceAll('_',' ')} — ${data.latest_action.reason} (${date(data.latest_action.created_at)})` : 'No recorded action'}.</p>
    <h3>Current coordination responsibilities</h3>{data.responsibilities.length ? <ul>{data.responsibilities.map((r,i) => <li key={i}>{r.bureau} · {r.officer}: {r.instruction} · action expected {date(r.action_date)} · {r.acknowledged_at ? 'Acknowledged' : 'Awaiting acknowledgment'}</li>)}</ul> : <p>No responsibilities visible to this account.</p>}
    {data.relationship_status && <p>Human-reviewed same-incident relationships: {data.relationship_status.same_incident}. Related issues: {data.relationship_status.related_issue}. Suggestions awaiting review: {data.relationship_status.awaiting_review}. Suggestions are not confirmed incidents.</p>}
    <Link to={`/institutions/${data.case.institution.id}?section=history`}>Complete institution history</Link>
    {user.features?.reviewed_facts && <ReviewedFacts complaint={data.case} user={user} />}
  </>}</div>;
}

function validBrief(value: unknown): boolean {
  const b = value as Brief | null;
  const c=b?.case, i=c?.institution, relation=b?.relationship_status;
  const validDate=(v:unknown)=>typeof v==='string' && Number.isFinite(Date.parse(v));
  const optionalDate=(v:unknown)=>v===null || validDate(v);
  return !!b && !!c && !!i && ['id','name','permanent_id'].every(k=>typeof i[k as keyof typeof i]==='string')
    && ['id','summary','description','source_reference','classification','category','status','reference','bureau','assigned_name','next_action'].every(k=>typeof c[k as keyof Case]==='string')
    && validDate(c.received_at) && validDate(c.due_at) && optionalDate(c.incident_date) && optionalDate(c.next_action_date)
    && validDate(b.generated_at) && typeof b.allegation_label==='string' && typeof b.pending_escalation==='boolean'
    && Array.isArray(b.responsibilities) && b.responsibilities.every(r=>r && ['instruction','bureau','officer'].every(k=>typeof r[k as keyof typeof r]==='string') && optionalDate(r.action_date) && optionalDate(r.acknowledged_at))
    && (relation===undefined || !!relation && ['awaiting_review','same_incident','related_issue'].every(k=>Number.isInteger(relation[k as keyof typeof relation]) && relation[k as keyof typeof relation]>=0))
    && (b.latest_action===null || !!b.latest_action && typeof b.latest_action.kind==='string' && typeof b.latest_action.reason==='string' && validDate(b.latest_action.created_at));
}

type Fact = { id: string; kind: string; source_field: string; quote: string; value: string; state: string; version: number; reason: string; method: string; source_digest:string; reviewer_id:number|null; reviewed_at:string|null };
function ReviewedFacts({ complaint, user }: { complaint: Case; user: User }) {
  const [refresh, setRefresh] = useState(0), [page,setPage] = useState(1);
  const { data, error } = usePoll<Page<Fact>>(`/api/cases/${complaint.id}/facts?page=${page}`, 0, refresh, validFacts);
  const [field,setField] = useState<'summary'|'description'|'source_reference'>('summary');
  const [kind,setKind] = useState('remedy'), [start,setStart] = useState(0), [end,setEnd] = useState(0);
  const [message,setMessage] = useState(''), [busy,setBusy] = useState(false), [submission,setSubmission] = useState(crypto.randomUUID());
  const text = complaint[field], quote = text.slice(start,end);
  async function propose(e: FormEvent) {
    e.preventDefault(); setBusy(true); setMessage('');
    try {
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))), b=>b.toString(16).padStart(2,'0')).join('');
      await api(`/api/cases/${complaint.id}/facts`,{method:'POST',body:JSON.stringify({submission_id:submission,kind,source_field:field,span_start:Array.from(text.slice(0,start)).length,span_end:Array.from(text.slice(0,end)).length,quote,source_digest:digest,value:quote.trim()})});
      setSubmission(crypto.randomUUID()); setRefresh(r=>r+1);
    } catch(e) { setMessage((e as Error).message); } finally { setBusy(false); }
  }
  return <section aria-label="Reviewed source facts"><h3>Source-grounded facts — experimental</h3><p>Proposals remain unverified until a coordinator reviews them. Original allegations are preserved.</p>
    <ErrorBox message={error || message} />{!data && !error && <Loading />}
    {data && (data.results.length ? data.results.map(f => <FactReview key={f.id} fact={f} caseId={complaint.id} user={user} refresh={()=>setRefresh(r=>r+1)} />) : <Empty>No proposed facts.</Empty>)}
    {data && <LocalPages page={page} count={data.count} next={data.next} change={setPage} />}
    {user.role !== 'auditor' && <form onSubmit={propose} className="form-panel form-grid">
      <label>Fact type<select value={kind} onChange={e=>setKind(e.target.value)}><option value="remedy">Requested remedy</option><option value="reference">Explicit reference</option><option value="incident_date">Incident date (ISO only)</option></select></label>
      <label>Evidence source<select value={field} onChange={e=>{setField(e.target.value as typeof field);setStart(0);setEnd(0);}}><option value="summary">Original summary</option><option value="description">Original description</option><option value="source_reference">Source reference</option></select></label>
      <label className="wide">Select supporting text<textarea readOnly value={text} onSelect={e=>{setStart(e.currentTarget.selectionStart);setEnd(e.currentTarget.selectionEnd);}} /></label>
      <p className="wide">Selected evidence: {quote || 'Select an exact span in the field above.'}</p>
      <button disabled={busy || !quote.trim()} type="submit">Propose selected fact</button>
    </form>}
  </section>;
}
function FactReview({fact,caseId,user,refresh}:{fact:Fact;caseId:string;user:User;refresh:()=>void}) {
  const [reason,setReason]=useState(''), [error,setError]=useState(''), [busy,setBusy]=useState(false);
  async function review(state:string) {
    setBusy(true);setError('');
    try { await api(`/api/cases/${caseId}/facts/${fact.id}/review`,{method:'POST',body:JSON.stringify({state,reason,expected_version:fact.version})});refresh(); }
    catch(e) {setError(e instanceof ApiError && e.status===409 ? 'Another reviewer changed this fact. Your reason is retained below. Copy it before reloading the latest facts and reconciling the review.' : (e as Error).message);} finally {setBusy(false);}
  }
  return <article className="panel card-body form-panel"><p><strong>{fact.kind.replaceAll('_',' ')}</strong> · {fact.state} · version {fact.version}</p><blockquote>{fact.quote}</blockquote><p>Source: {fact.source_field}. Method: {fact.method}. {fact.reason}</p><p>Reviewer: {fact.reviewer_id || 'Awaiting review'} · {date(fact.reviewed_at)}</p><details><summary>Source integrity digest</summary><code style={{overflowWrap:'anywhere'}}>{fact.source_digest}</code></details><ErrorBox message={error} />
    {user.role==='coordinator' && <><label>Fact review rationale<textarea value={reason} onChange={e=>setReason(e.target.value)} maxLength={4000} /></label><button disabled={busy || !reason.trim()} onClick={()=>review('accepted')}>Accept fact</button> <button className="secondary" disabled={busy || !reason.trim()} onClick={()=>review('rejected')}>Reject / correct fact</button> <button className="text-button" onClick={refresh}>Reload latest facts (discard review draft)</button></>}
  </article>;
}

type Group = { id:string; title:string; reason:string; version:number; needs_review:boolean; supporting_relationship_id:number|null; cases:{id:string;reference:string}[] };
export function IncidentGroups({institution,user}:{institution:string;user:User}) {
  const [refresh,setRefresh]=useState(0), [page,setPage]=useState(1), [casePage,setCasePage]=useState(1), [search,setSearch]=useState('');
  const {data,error}=usePoll<Page<Group>>(user.features?.incident_groups ? `/api/incident-groups?institution=${institution}&page=${page}` : null,0,refresh,validGroups);
  const {data:cases,error:caseError}=usePoll<Page<Case>>(user.features?.incident_groups && user.role==='coordinator' ? `/api/institutions/${institution}/cases?page=${casePage}&q=${encodeURIComponent(search)}` : null);
  const [editing,setEditing]=useState<Group|null>(null), [selected,setSelected]=useState<string[]>([]),[title,setTitle]=useState(''),[reason,setReason]=useState(''),[support,setSupport]=useState('');
  const [message,setMessage]=useState(''),[busy,setBusy]=useState(false),[submission,setSubmission]=useState(crypto.randomUUID());
  if (!user.features?.incident_groups) return null;
  async function save(e:FormEvent) {
    e.preventDefault();setBusy(true);setMessage('');
    try {await api(`/api/incident-groups${editing ? '/'+editing.id : ''}`,{method:editing?'PATCH':'POST',body:JSON.stringify({submission_id:submission,expected_version:editing?.version,institution,title,reason,cases:selected,supporting_relationship:support?Number(support):null})});
      setEditing(null);setSelected([]);setTitle('');setReason('');setSupport('');setSubmission(crypto.randomUUID());setRefresh(r=>r+1);
    } catch(e) {setMessage(e instanceof ApiError && e.status===409 ? 'This group changed. Your selection is retained; reload the group and reconcile before saving.' : (e as Error).message);} finally {setBusy(false);}
  }
  return <section className="card-body" aria-label="Manual incident groups"><h3>Manual incident groups — experimental</h3><p>Explicit organization only. Cases retain their own ownership, deadlines and status. Related issues do not establish one incident.</p><ErrorBox message={error || message || caseError} />
    <button type="button" className="text-button" onClick={()=>setRefresh(r=>r+1)}>Reload group list (keep unsaved draft)</button>
    {!data && !error && <Loading />}{data && (data.results.length ? data.results.map(g=><article className="panel card-body" key={g.id}><h4>{g.title}</h4><p>{g.reason} · version {g.version} · {g.needs_review?'Supporting relationship changed: review required':'Explicitly reviewed'}</p><ul>{g.cases.map(c=><li key={c.id}><Link to={`/cases/${c.id}`}>{c.reference}</Link></li>)}</ul>{user.role==='coordinator' && <button onClick={()=>{setEditing(g);setSelected(g.cases.map(c=>c.id));setTitle(g.title);setReason(g.reason);setSupport(g.supporting_relationship_id?.toString()||'');setMessage('');}}>Review group {g.title} (replace unsaved draft)</button>}</article>) : <Empty>No incident groups.</Empty>)}
    {data && <LocalPages page={page} count={data.count} next={data.next} change={setPage} />}
    {user.role==='coordinator' && <form onSubmit={save} className="form-panel form-grid"><h4>{editing?'Review existing group':'Create an explicit group'}</h4>
      <label>Incident group title<input required maxLength={180} value={title} onChange={e=>setTitle(e.target.value)} /></label><label>Group decision reason<textarea required maxLength={4000} value={reason} onChange={e=>setReason(e.target.value)} /></label>
      <label>Supporting same-incident relationship ID (optional)<input type="number" min="1" value={support} onChange={e=>setSupport(e.target.value)} /></label>
      <label>Find member cases<input value={search} onChange={e=>{setSearch(e.target.value);setCasePage(1);}} /></label>
      <fieldset className="wide"><legend>Select 2–20 cases from this institution ({selected.length} selected across pages)</legend>{cases?.results.map(c=><label key={c.id}><input type="checkbox" checked={selected.includes(c.id)} onChange={e=>setSelected(s=>e.target.checked?[...s,c.id]:s.filter(id=>id!==c.id))} />{c.reference} · {c.summary}</label>)}</fieldset>
      {cases && <LocalPages page={casePage} count={cases.count} next={cases.next} change={setCasePage} />}
      <button type="submit" disabled={busy || selected.length<2 || selected.length>20}>Save explicit incident group</button>
    </form>}
  </section>;
}
function LocalPages({page,count,next,change}:{page:number;count:number;next:string|null;change:(page:number)=>void}) {
  return <nav className="pagination" aria-label="Section pages"><button type="button" className="button secondary" disabled={page===1} onClick={()=>change(page-1)}>Previous page</button> <span>Page {page} · {count} records</span> <button type="button" className="button secondary" disabled={!next} onClick={()=>change(page+1)}>Next page</button></nav>;
}

function validFacts(value: unknown): boolean {
  const p=value as Page<Fact>|null;
  return !!p && Number.isInteger(p.count) && p.count>=0 && Array.isArray(p.results) && p.results.every(f=>f && typeof f.id==='string' && typeof f.kind==='string' && typeof f.quote==='string' && typeof f.state==='string' && Number.isInteger(f.version));
}
function validGroups(value: unknown): boolean {
  const p=value as Page<Group>|null;
  return !!p && Number.isInteger(p.count) && p.count>=0 && Array.isArray(p.results) && p.results.every(g=>g && typeof g.id==='string' && typeof g.title==='string' && typeof g.reason==='string' && Number.isInteger(g.version) && Array.isArray(g.cases) && g.cases.every(c=>c && typeof c.id==='string' && typeof c.reference==='string'));
}
