import { useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { usePoll } from './imports';
import type { Page } from './api';
import { labels } from './api';
import { ErrorBox, Loading, Empty, Pagination } from './ui';

const metrics = {
  complaints:'Complaint records', pending_pairs:'Pending relationship pairs', suggested_cases:'Distinct cases with suggestions',
  same_incident_pairs:'Reviewed same-incident pairs', related_issue_pairs:'Reviewed related-issue pairs',
  confirmed_groups:'Confirmed incident groups', grouped_cases:'Distinct cases in confirmed groups', ungrouped_cases:'Not in a confirmed group',
  matching_complete:'Matching complete', matching_pending:'Matching pending', matching_failed:'Matching failed', matching_not_processed:'Not processed with current model',
};
type Metric = keyof typeof metrics;
type Summary = {counts:Record<Metric,number>;generated_at:string;model_revision:string};
type Row = {id:string|number;reference?:string;status?:string;title?:string;institution_id?:string;scope_case_count?:number;all_time_case_count?:number;left_reference?:string;right_reference?:string;decision?:string;score?:number|null;cases?:{id:string;reference:string}[]};
function validSummary(value:unknown): boolean {
  const s=value as Summary|null;
  return !!s && typeof s.model_revision==='string' && typeof s.generated_at==='string' && Number.isFinite(Date.parse(s.generated_at)) && !!s.counts && Object.keys(metrics).every(k=>Number.isInteger(s.counts[k as Metric]) && s.counts[k as Metric]>=0);
}

export function IncidentSummary({filters,allTime=false}:{filters:string;allTime?:boolean}) {
  const [params,setParams]=useSearchParams();
  const selected=params.get('incident_metric');
  const metric=selected && Object.prototype.hasOwnProperty.call(metrics,selected) ? selected as Metric : null;
  const [pages,setPages]=useState<URLSearchParams>(new URLSearchParams());
  const {data,error}=usePoll<Summary>(`/api/incident-summary?${filters}`,5000,0,validSummary);
  const query=new URLSearchParams(filters);query.set('metric',metric || 'complaints');query.set('page',pages.get('page')||'1');
  const validateRows=useCallback((value:unknown)=>{
    const p=value as Page<Row>|null;
    return !!p && Number.isInteger(p.count) && p.count>=0 && Array.isArray(p.results) && p.results.every(r=>r && ['string','number'].includes(typeof r.id) &&
      (metric==='confirmed_groups' ? typeof r.title==='string' && Number.isInteger(r.scope_case_count) && Number.isInteger(r.all_time_case_count)
        : metric?.endsWith('_pairs') ? typeof r.left_reference==='string' && typeof r.right_reference==='string' && typeof r.decision==='string'
          : typeof r.reference==='string' && typeof r.status==='string'));
  },[metric]);
  const {data:rows,error:rowError}=usePoll<Page<Row>>(metric ? `/api/incident-summary/records?${query}` : null,5000,0,validateRows);
  function choose(value:Metric) {const next=new URLSearchParams(params);next.set('incident_metric',value);setPages(new URLSearchParams());setParams(next,{replace:true});}
  return <section className="panel detail-card card-body incident-summary" aria-label="Complaint and incident counts">
    <h2>Complaint and incident counts</h2>
    <p className="policy-note">{allTime?'All-time authorized institution cases; Home date filters do not apply.':'Selected authorized complaint scope, including the report receipt filters.'} Both pair endpoints must be in scope. Groups count when they touch the scope; member counts use distinct complaint IDs within it.</p>
    <ErrorBox message={error} />{!data && !error && <Loading />}
    {data && <><div className="incident-metrics">{Object.entries(metrics).map(([key,label])=><button type="button" className={metric===key?'incident-metric active':'incident-metric'} key={key} onClick={()=>choose(key as Metric)} aria-pressed={metric===key}>
      <span>{label}</span><strong>{data.counts[key as Metric].toLocaleString('en-IN')}</strong><small>View records →</small>
    </button>)}</div>
    <p>Potentially related — AI suggestion. Same incident and related issue — coordinator-reviewed. Stored pairs and top-five suggestions are not an exhaustive count of similar complaints. Group membership never reduces complaint totals; groups can overlap.</p>
    {!!(data.counts.matching_pending+data.counts.matching_failed+data.counts.matching_not_processed) && <p role="status" className="policy-note">Matching incomplete: {data.counts.matching_pending} pending, {data.counts.matching_failed} failed, {data.counts.matching_not_processed} not processed with the current model. Missing matches are not confirmed zero relationships.</p>}
    <p className="muted">Refreshed {new Date(data.generated_at).toLocaleTimeString('en-IN')} · current model {data.model_revision}</p></>}
    {metric && <div className="incident-drilldown"><h3>{metrics[metric]}</h3><a className="button secondary no-print" href={`/api/incident-summary.csv?${query}`}>Download {metrics[metric]} CSV</a>
      <ErrorBox message={rowError} />{!rows && !rowError && <Loading />}
      {rows && <>{rows.results.length ? <div className="table-scroll" role="region" aria-label="Incident metric records" tabIndex={0}><table><thead><tr><th>Record</th><th>Details</th></tr></thead><tbody>
        {rows.results.map(r=><tr key={r.id}>{metric==='confirmed_groups'?<><td><Link to={`/institutions/${r.institution_id}?section=coordination#incident-${r.id}`}>{r.title}</Link></td><td>{r.scope_case_count} cases in selected scope · {r.all_time_case_count} all-time members</td></>
          : metric.endsWith('_pairs')?<><td><Link to={`/coordination?pair=${r.id}&decision=all`}>{r.left_reference} / {r.right_reference}</Link></td><td>{r.decision==='pending'?'Potentially related — AI suggestion':`${r.decision?.replaceAll('_',' ')} — coordinator-reviewed`}</td></>
            : <><td><Link to={`/cases/${r.id}`}>{r.reference}</Link></td><td>{labels[r.status!]||r.status}</td></>}</tr>)}
      </tbody></table></div>:<Empty>No records for this metric in this scope.</Empty>}
      <Pagination data={rows} params={pages} setParams={setPages} /></>}
    </div>}
  </section>;
}
