import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
import { artifact } from './support';
import { readFile, writeFile } from 'node:fs/promises';
test.describe.configure({mode:'serial'});
test.setTimeout(180000);
let institution:any, cases:any[], originals:Record<string,string>[], source:string, rowCase:any, reviewedGroup:any;
const stamp=Date.now();
async function login(page:Page,user='coordinator'){
  await page.goto('/accounts/login/');await page.getByLabel('Username:').fill(user);
  await page.getByLabel('Password:').fill(process.env.DEMO_PASSWORD||'Demo-only-26264!');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Complaint Monitoring Dashboard',exact:true})).toBeVisible();
}
async function post(page:Page,path:string,data:unknown){
  const token=(await page.context().storageState()).cookies.find(c=>c.name==='csrftoken')!.value;
  return page.request.post(path,{data,headers:{'X-CSRFToken':token}});
}
async function upload(page:Page,rows:Record<string,string>[],bureau:string,system:string){
  const keys=Object.keys(rows[0]);const quote=(v:string)=>'"'+v.replaceAll('"','""')+'"';
  const csv=[keys.map(quote).join(','),...rows.map(row=>keys.map(k=>quote(row[k]||'')).join(','))].join('\n');
  const token=(await page.context().storageState()).cookies.find(c=>c.name==='csrftoken')!.value;
  const response=await page.request.post('/api/imports',{headers:{'X-CSRFToken':token},multipart:{kind:'complaints',source_system:system,source_bureau:bureau,file:{name:`${system}.csv`,mimeType:'text/csv',buffer:Buffer.from(csv)}}});
  expect(response.status()).toBe(201);const job=await response.json();
  expect((await post(page,`/api/imports/${job.id}`,{action:'confirm'})).ok()).toBeTruthy();
  await expect.poll(async()=>{const j=await(await page.request.get(`/api/imports/${job.id}`)).json();return ['complete','matching_failed','failed'].includes(j.state)?j.state:'pending';},{timeout:120000}).toBe('complete');
  return job;
}

test('guide explains decisions, provides offline fictional files and preserves five primary sections',async({page})=>{
  await login(page);await page.getByRole('link',{name:'Help · How it works'}).click();
  await expect(page.getByRole('heading',{name:'How this portal works',exact:true})).toBeVisible();
  await expect(page.getByRole('region',{name:'Decision responsibilities'})).toContainText('not truth or duplicate probability');
  const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('link',{name:'Download fictional RB CSV'}).click()]);
  expect(download.suggestedFilename()).toBe('six-case-rb.csv');
  await download.saveAs(artifact('download-rb.csv'));expect(await readFile(artifact('download-rb.csv'),'utf-8')).toContain('CORE-DEMO-001');
  await page.setViewportSize({width:390,height:844});
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
  await page.screenshot({path:artifact('operational-guide-mobile.png'),fullPage:true});
  await login(page,'officer_rb');await page.goto('/guide');
  await expect(page.getByRole('heading',{name:'How this portal works',exact:true})).toBeVisible();
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
});

test('six independent Bureau complaints, missing category correction and reviewed grouping',async({page})=>{
  await login(page);const created=await post(page,'/api/institution-registry',{name:`Operational Fictional Institute ${stamp}`,permanent_id:`OP-${stamp}`,region:'Synthetic',district:'Synthetic',reason:'Fictional operational workflow acceptance fixture.'});
  expect(created.status(),await created.text()).toBe(201);institution=await created.json();source=`op-rb-${stamp}`;
  const received=new Date(Date.now()-40*86400000).toISOString();
  originals=Array.from({length:3},(_,i)=>({source_reference:`OP-${stamp}-${i}`,institution_permanent_id:institution.permanent_id,bureau:'RB',category:i?'refunds':'',summary:`Tuition refund for fictional transaction OP-TX-${stamp} is withheld after admission cancellation.`,description:'Authored synthetic complaints about the same fictional transaction, supplied for workflow testing only.',received_at:received,status:'registered'}));
  await upload(page,originals,'RB',source);
  await upload(page,originals.map((r,i)=>({...r,bureau:'PGRC',category:'refunds',source_reference:`PG-${stamp}-${i}`})),'PGRC',`op-pgrc-${stamp}`);
  cases=(await(await page.request.get(`/api/cases?institution=${institution.id}`)).json()).results;
  expect(cases).toHaveLength(6);rowCase=cases.find(c=>c.category==='needs_categorization');expect(rowCase).toBeTruthy();
  await page.goto(`/cases/${rowCase.id}`);await page.getByRole('combobox',{name:'Action',exact:true}).selectOption('category');
  await page.getByRole('combobox',{name:'New category',exact:true}).selectOption('refunds');
  await page.getByLabel('Reason / note',{exact:true}).fill('Reviewed original text: this is a refund complaint.');
  await page.getByRole('button',{name:'Record action',exact:true}).click();
  await expect.poll(async()=>(await(await page.request.get(`/api/cases/${rowCase.id}`)).json()).category).toBe('refunds');
  const pair=(await(await page.request.get(`/api/overlaps?institution=${institution.id}`)).json()).results[0];expect(pair).toBeTruthy();
  expect((await post(page,`/api/overlaps/${pair.id}/review`,{decision:'same_incident',reason:'Synthetic source explicitly identifies the same fictional transaction.',expected_version:pair.version})).ok()).toBeTruthy();
  const group=await post(page,'/api/incident-groups',{submission_id:crypto.randomUUID(),institution:institution.id,title:`Operational reviewed incident ${stamp}`,cases:cases.map(c=>c.id),reason:'Explicit human test decision based on authored shared incident evidence.',supporting_relationship:pair.id});
  expect(group.ok()).toBeTruthy();
  reviewedGroup=await group.json();
  const counts=(await(await page.request.get(`/api/incident-summary?institution=${institution.id}`)).json()).counts;
  expect([counts.complaints,counts.confirmed_groups,counts.grouped_cases]).toEqual([6,1,6]);
});

test('controlled scenario records one shared simulated request and two accountable Bureau actions',async({page,browser})=>{
  await login(page);
  const current=(await(await page.request.get(`/api/cases?institution=${institution.id}`)).json()).results;
  const lifecycles=Object.fromEntries(current.map((c:any)=>[c.id,c.status]));
  const requestCase=current.find((c:any)=>c.bureau==='RB' && c.status!=='disposed');const marker=`SIMULATED-LEDGER-${stamp}`;
  expect((await post(page,`/api/cases/${requestCase.id}/actions`,{kind:'note',expected_version:requestCase.version,reason:`SIMULATED shared document request ${marker}: RB collects one refund ledger for joint review. No external request is sent.`})).ok()).toBeTruthy();
  const officers=[];
  for(const code of ['RB','PGRC']){
    const officer=await browser.newPage({baseURL:process.env.PLAYWRIGHT_BASE_URL||'http://127.0.0.1:5174'});
    await login(officer,code==='RB'?'officer_rb':'officer_pgrc');
    const session=await(await officer.request.get('/api/session')).json();officers.push({page:officer,code,id:session.user.id});
  }
  try {
    const opened=await post(page,'/api/coordination-records',{submission_id:crypto.randomUUID(),institution:institution.id,cases:current.map((c:any)=>c.id),
      incident_group:reviewedGroup.id,expected_group_version:reviewedGroup.version,lead_bureau:'RB',lead_officer:officers[0].id,
      reason:'Controlled fictional comparison: reuse one explicitly recorded simulated document request.',
      participants:officers.map(o=>({bureau:o.code,officer:o.id,instruction:o.code==='RB'?`Collect ledger once under ${marker}.`:`Reuse ${marker}; review the same ledger without a second request.`}))});
    expect(opened.status(),await opened.text()).toBe(201);const record=await opened.json();let version=record.version;
    for(const officer of officers){
      for(const action of ['acknowledge','complete']){
        const response=await post(officer.page,`/api/coordination-records/${record.id}/actions`,{action,expected_version:version,note:`${officer.code} ${action}: used the single simulated ledger.`});
        expect(response.ok()).toBeTruthy();version=(await response.json()).version;
      }
    }
    expect((await post(page,`/api/coordination-records/${record.id}/actions`,{action:'close',expected_version:version,note:'Both Bureaus completed their scripted duties using one shared simulated request. No staff productivity claim is made.'})).ok()).toBeTruthy();
    const history=await(await page.request.get(`/api/cases/${requestCase.id}/history`)).json();
    const shared=history.results.filter((a:any)=>a.kind==='note' && a.reason.includes(marker));expect(shared).toHaveLength(1);
    const after=(await(await page.request.get(`/api/cases?institution=${institution.id}`)).json()).results;
    expect(Object.fromEntries(after.map((c:any)=>[c.id,c.status]))).toEqual(lifecycles);
    await writeFile(artifact('controlled-coordination.json'),JSON.stringify({provenance:'Authored controlled scenario, not actual AICTE staff workload.',scripted_independent_requests:[{bureau:'RB',artifact:'refund ledger'},{bureau:'PGRC',artifact:'refund ledger'}],scripted_baseline_requests:2,recorded_coordinated_simulated_requests:shared.length,designated_bureaus:2,acknowledged_and_completed:2,case_statuses_unchanged:true,real_productivity_savings_measured:false},null,2));
    await page.goto(`/coordination/workspace/${record.id}`);await expect(page.getByRole('heading',{name:'Coordination closed',exact:true})).toBeVisible();
    await page.screenshot({path:artifact('operational-coordination-closed.png'),fullPage:true});
  } finally {for(const officer of officers)await officer.page.close();}
});

test('coordinator approves one source closure without replacing allegations or closing siblings',async({page})=>{
  await login(page);const disposition=new Date(Date.now()-86400000).toISOString();
  const changed={...originals[0],summary:'Different incoming text retained only as source evidence.',status:'disposed',disposed_at:disposition,resolution_note:'Synthetic source receipt reports repayment; coordinator reviewed this evidence.'};
  const job=await upload(page,[changed],'RB',source);
  await page.goto(`/imports/${job.id}/rows?state=all`);
  const reason='Source disposal evidence reviewed; retain original allegations and independent cases.';
  async function prepare(){
    await page.getByRole('combobox',{name:'Review decision',exact:true}).selectOption('apply_selected_updates');
    await page.getByRole('checkbox',{name:'Apply status',exact:true}).check();
    await page.getByRole('checkbox',{name:'Keep original allegations and all unselected/protected fields'}).check();
    await page.getByLabel('Reason for applying selected updates').fill(reason);
  }
  await prepare();
  const before=await(await page.request.get(`/api/cases/${rowCase.id}`)).json();
  expect((await post(page,`/api/cases/${rowCase.id}/actions`,{kind:'note',expected_version:before.version,reason:'Concurrent official note before source approval.'})).ok()).toBeTruthy();
  await page.getByRole('button',{name:'Approve selected updates',exact:true}).click();
  await expect(page.getByLabel('Reason for applying selected updates')).toHaveValue(reason);
  await expect(page.getByRole('button',{name:'Approve selected updates',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Reload row and discard draft'}).click();
  await expect(page.getByLabel('Reason for keeping portal record')).toHaveValue('');
  await prepare();
  await page.getByRole('button',{name:'Approve selected updates',exact:true}).click();
  await expect(page.getByRole('heading',{name:/selected changes applied/})).toBeVisible();
  const current=(await(await page.request.get(`/api/cases?institution=${institution.id}`)).json()).results;
  expect(current.filter((c:any)=>c.status==='disposed')).toHaveLength(1);expect(current.filter((c:any)=>c.status==='registered')).toHaveLength(5);
  expect(current.find((c:any)=>c.id===rowCase.id).summary).toBe(originals[0].summary);
  const counts=(await(await page.request.get(`/api/incident-summary?institution=${institution.id}`)).json()).counts;
  expect([counts.complaints,counts.confirmed_groups,counts.grouped_cases]).toEqual([6,1,6]);
  await upload(page,[changed],'RB',source);
  const history=await(await page.request.get(`/api/cases/${rowCase.id}/history`)).json();expect(history.results.filter((a:any)=>a.kind==='source_conflict')).toHaveLength(1);
  await page.screenshot({path:artifact('operational-source-approval.png'),fullPage:true});
});
