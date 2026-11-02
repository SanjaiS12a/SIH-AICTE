import { test, expect } from '@playwright/test';
import type { APIRequestContext, Page } from '@playwright/test';
import { artifact } from './support';

test.describe.configure({mode:'serial'});
let backend:APIRequestContext, institution:any, cases:any[]=[], group:any, options:any;
const stamp=Date.now(), title=`Reviewed six-case incident ${stamp}`;
async function post(path:string,data:unknown) {
  const token=(await backend.storageState()).cookies.find(c=>c.name==='csrftoken')!.value;
  return backend.post(path,{data,headers:{'X-CSRFToken':token}});
}
async function login(page:Page,username='coordinator') {
  await page.goto('/accounts/login/');await page.getByLabel('Username:').fill(username);
  await page.getByLabel('Password:').fill(process.env.DEMO_PASSWORD||'Demo-only-26264!');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Complaint Monitoring Dashboard',exact:true})).toBeVisible();
}
async function overview(page:Page) {
  await page.goto(`/institutions/${institution.id}`);
  await expect(page.getByRole('region',{name:'Complaint and incident counts'})).toBeVisible();
}
function metric(page:Page,name:string) {return page.getByRole('region',{name:'Complaint and incident counts'}).getByRole('button',{name:new RegExp('^'+name)});}

test.beforeAll(async({playwright})=>{
  backend=await playwright.request.newContext({baseURL:process.env.PLAYWRIGHT_BASE_URL||'http://127.0.0.1:5174'});
  await backend.get('/accounts/login/');
  const csrf=(await backend.storageState()).cookies.find(c=>c.name==='csrftoken')!.value;
  expect((await backend.post('/accounts/login/',{form:{username:'coordinator',password:process.env.DEMO_PASSWORD||'Demo-only-26264!',csrfmiddlewaretoken:csrf}})).ok()).toBeTruthy();
  const r=await post('/api/institution-registry',{permanent_id:`CORE-${stamp}`,name:`Core Fictional Institute ${stamp}`,region:'Southern',district:'Synthetic only',reason:'Explicit synthetic core-intelligence fixture'});
  expect(r.status()).toBe(201);institution=await r.json();options=await (await backend.get('/api/options')).json();
  for(let n=0;n<6;n++) {
    const r=await post('/api/cases',{submission_id:crypto.randomUUID(),institution:institution.id,bureau:n%2?'PGRC':'RB',source_system:'core-browser',source_reference:`${stamp}-${n}`,category:'refunds',
      summary:n%2?'The admission cancellation refund for transaction DEMO-REF-2026 is still unpaid.':'Tuition fees have not been returned for the cancelled admission transaction DEMO-REF-2026.',
      description:'Fictional fixture only. Six independent complaints concern the same declared demonstration transaction, academic year 2026.'});
    expect(r.status()).toBe(201);cases.push(await r.json());
  }
});
test.afterAll(async()=>backend?.dispose());
test.beforeEach(async({context})=>{await context.route(/^https?:\/\//,route=>['127.0.0.1','localhost'].includes(new URL(route.request().url()).hostname)?route.continue():route.abort());});

test('six complaints become one explicitly reviewed group and accountable coordination without merging',async({page,browser})=>{
  test.setTimeout(90000);await login(page);await overview(page);
  await expect(metric(page,'Complaint records').locator('strong')).toHaveText('6');
  await expect(metric(page,'Confirmed incident groups').locator('strong')).toHaveText('0');
  await expect.poll(async()=>{const d=await (await backend.get('/api/incident-summary?institution='+institution.id)).json();return d.counts.matching_complete;}).toBe(6);
  const suggestions=(await (await backend.get('/api/overlaps?decision=all&institution='+institution.id)).json()).results;
  expect(suggestions.some((p:any)=>typeof p.score==='number' && p.model_revision)).toBeTruthy();
  const existing=suggestions.find((p:any)=>[p.left.id,p.right.id].includes(cases[0].id)&&[p.left.id,p.right.id].includes(cases[1].id));
  const relation=await post('/api/relationships',{left:cases[0].id,right:cases[1].id,decision:'same_incident',reason:'Source transaction checked deliberately for this fictional scenario',...(existing?{expected_version:existing.version}:{})});
  expect(relation.ok()).toBeTruthy();const pair=await relation.json();
  await page.goto(`/institutions/${institution.id}?section=coordination`);
  const groups=page.getByRole('region',{name:'Manual incident groups'});
  await groups.getByLabel('Incident group title').fill(title);
  await groups.getByLabel('Group decision reason').fill('Six independently received reports refer to the same fictional transaction. Supporting original descriptions checked explicitly.');
  await groups.getByLabel('Supporting same-incident relationship ID (optional)').fill(String(pair.id));
  for(const c of cases)await groups.getByRole('checkbox',{name:new RegExp(c.reference)}).check();
  await groups.getByRole('button',{name:'Save explicit incident group',exact:true}).click();
  await expect(groups.getByRole('heading',{name:title,exact:true})).toBeVisible();
  group=(await (await backend.get('/api/incident-groups?institution='+institution.id)).json()).results[0];
  await overview(page);
  await expect(metric(page,'Confirmed incident groups').locator('strong')).toHaveText('1');
  await expect(metric(page,'Distinct cases in confirmed groups').locator('strong')).toHaveText('6');
  await metric(page,'Confirmed incident groups').click();
  await expect(page.getByRole('region',{name:'Incident metric records'})).toContainText('6 cases in selected scope');
  const csv=await page.request.get((await page.getByRole('link',{name:'Download Confirmed incident groups CSV'}).getAttribute('href'))!);
  expect((await csv.text()).trim().split('\n')).toHaveLength(2);
  await page.screenshot({path:artifact('core-six-cases-one-incident.png'),fullPage:true});
  await page.goto(`/coordination/workspace?institution=${institution.id}&incident_group=${group.id}`);
  await page.getByRole('button',{name:'Use reviewed group cases'}).click();
  await page.getByLabel('Private coordination reason').fill('Coordinate evidence requests for the explicitly reviewed incident.');
  for(const code of ['RB','PGRC']) {
    const bureau=options.bureaus.find((b:any)=>b.code===code);
    await page.getByRole('checkbox',{name:bureau.name,exact:true}).check();
    await page.getByLabel(`Responsible officer — ${bureau.name}`,{exact:true}).selectOption(String(options.officers.find((o:any)=>o.bureau===code).id));
    await page.getByLabel(`Shared instruction — ${bureau.name}`,{exact:true}).fill(`Core ${stamp} ${code}: verify the agreed source record.`);
  }
  await page.getByLabel('Lead Bureau',{exact:true}).selectOption('RB');
  await page.getByRole('button',{name:'Record agreed coordination',exact:true}).click();
  await expect(page).toHaveURL(/coordination\/workspace\/[0-9a-f-]+$/);const url=page.url();
  await expect(page.getByText('Source incident group snapshot: version 1.',{exact:false})).toBeVisible();
  for(const [username,code] of [['officer_rb','RB'],['officer_pgrc','PGRC']]) {
    const officer=await browser.newPage({baseURL:process.env.PLAYWRIGHT_BASE_URL||'http://127.0.0.1:5174'});await login(officer,username);
    await officer.goto('/coordination/requests');const card=officer.locator('section.panel').filter({hasText:`Core ${stamp} ${code}:`});
    await card.getByRole('button',{name:'Acknowledge agreed action'}).click();
    await card.getByLabel('Completion note').fill(`${code} checked its assigned evidence.`);
    await card.getByRole('button',{name:'Complete agreed action'}).click();await officer.close();
  }
  await page.goto(url);await page.getByLabel('Coordination outcome').fill('Both Bureaus completed their agreed checks without disposing the complaint records.');
  await page.getByRole('button',{name:'Close coordination',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Coordination closed',exact:true})).toBeVisible();
  for(const c of cases)expect((await (await backend.get('/api/cases/'+c.id)).json()).status).toBe('registered');
});

test('membership correction, stale draft and retirement preserve paginated authoritative history',async({page})=>{
  await login(page);await page.goto(`/institutions/${institution.id}?section=coordination`);
  const groups=page.getByRole('region',{name:'Manual incident groups'});
  await groups.getByRole('button',{name:`Review group ${title} (replace unsaved draft)`,exact:true}).click();
  await groups.getByRole('checkbox',{name:new RegExp(cases[5].reference)}).uncheck();
  await groups.getByLabel('Group decision reason').fill('One record removed through an auditable correction.');
  await groups.getByRole('button',{name:'Save explicit incident group',exact:true}).click();
  await expect(groups.getByText('5 independent complaint records.',{exact:false})).toBeVisible();
  group=(await (await backend.get('/api/incident-groups?institution='+institution.id)).json()).results[0];
  await groups.getByRole('button',{name:`Review group ${title} (replace unsaved draft)`,exact:true}).click();
  const token=(await backend.storageState()).cookies.find(c=>c.name==='csrftoken')!.value;
  const update={institution:institution.id,title,reason:'Concurrent source correction',cases:group.cases.map((c:any)=>c.id),supporting_relationship:group.supporting_relationship_id,expected_version:group.version};
  expect((await backend.patch('/api/incident-groups/'+group.id,{data:update,headers:{'X-CSRFToken':token}})).ok()).toBeTruthy();
  await groups.getByLabel('Group decision reason').fill('Retain my deliberate correction draft');
  await groups.getByRole('button',{name:'Save explicit incident group',exact:true}).click();
  await expect(groups.getByRole('alert')).toContainText('This group changed');
  await expect(groups.getByLabel('Group decision reason')).toHaveValue('Retain my deliberate correction draft');
  await page.reload();await groups.getByRole('button',{name:`Review group ${title} (replace unsaved draft)`,exact:true}).click();
  await groups.getByLabel('Group lifecycle').selectOption('retired');await groups.getByLabel('Group decision reason').fill('Retired after an explicit corrected review; history is retained.');
  await groups.getByRole('button',{name:'Save explicit incident group',exact:true}).click();
  await expect(groups.getByText('Retired — historical membership',{exact:false})).toBeVisible();
  await groups.getByText('Complete incident membership history',{exact:true}).click();
  await expect(groups.getByRole('button',{name:'Next page',exact:true}).first()).toBeEnabled();
  await groups.getByRole('button',{name:'Next page',exact:true}).first().click();
  await expect(groups.getByText(/Page 2 ·/)).toBeVisible();
  await overview(page);await expect(metric(page,'Complaint records').locator('strong')).toHaveText('6');await expect(metric(page,'Confirmed incident groups').locator('strong')).toHaveText('0');
});

test('overlapping groups use distinct cases and restricted roles cannot recover metadata',async({page})=>{
  for(const members of [cases.slice(0,4),cases.slice(3)]) {
    const r=await post('/api/incident-groups',{submission_id:crypto.randomUUID(),institution:institution.id,title:'Overlapping explicit review '+members.length,reason:'Independent issue components justified in this authored fixture',cases:members.map(c=>c.id)});
    expect(r.status()).toBe(201);
  }
  await login(page,'auditor');await overview(page);
  await expect(metric(page,'Confirmed incident groups').locator('strong')).toHaveText('2');await expect(metric(page,'Distinct cases in confirmed groups').locator('strong')).toHaveText('6');
  await page.goto(`/institutions/${institution.id}?section=coordination`);await expect(page.getByRole('button',{name:'Save explicit incident group'})).toHaveCount(0);
  await page.context().clearCookies();await login(page,'officer_rb');await overviewOfficer(page);
  for(const path of ['/api/incident-summary','/api/incident-summary/records','/api/incident-summary.csv'])expect((await page.request.get(path+'?institution='+institution.id)).status()).toBe(403);
});
async function overviewOfficer(page:Page) {await page.goto(`/institutions/${institution.id}`);await expect(page.getByRole('region',{name:'Complaint and incident counts'})).toHaveCount(0);}

test('malformed counts fail visibly and unknown metric parameters do not crash',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await login(page);
  await page.route('**/api/incident-summary?*',route=>route.fulfill({json:{counts:{complaints:null},model_revision:'invalid'}}));
  await overview(page);await expect(page.getByRole('region',{name:'Complaint and incident counts'}).getByRole('alert')).toContainText('incomplete or invalid');
  await page.unroute('**/api/incident-summary?*');await page.goto(`/institutions/${institution.id}?incident_metric=constructor`);
  await expect(metric(page,'Complaint records').locator('strong')).toHaveText('6');expect(errors).toEqual([]);
  await page.setViewportSize({width:390,height:844});await metric(page,'Distinct cases in confirmed groups').click();
  await expect(page.getByRole('region',{name:'Incident metric records'})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await page.screenshot({path:artifact('core-incident-counts-mobile.png'),fullPage:true});
});
