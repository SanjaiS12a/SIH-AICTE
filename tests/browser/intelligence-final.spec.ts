import { test, expect } from '@playwright/test';
import type { APIRequestContext, Page } from '@playwright/test';
import { artifact } from './support';
let backend: APIRequestContext;
let institution: string, first: string, second: string;
const stamp=Date.now();
async function post(url:string,data:unknown) {
  const token=(await backend.storageState()).cookies.find(c=>c.name==='csrftoken')!.value;
  return backend.post(url,{data,headers:{'X-CSRFToken':token}});
}
async function login(page:Page,user='coordinator') {
  await page.goto('/accounts/login/');await page.getByLabel('Username:').fill(user);
  await page.getByLabel('Password:').fill(process.env.DEMO_PASSWORD || 'Demo-only-26264!');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Complaint Monitoring Dashboard',exact:true})).toBeVisible();
}
test.beforeAll(async({playwright})=>{
  backend=await playwright.request.newContext({baseURL:process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5174'});
  await backend.get('/accounts/login/');
  const token=(await backend.storageState()).cookies.find(c=>c.name==='csrftoken')!.value;
  expect((await backend.post('/accounts/login/',{form:{username:'coordinator',password:process.env.DEMO_PASSWORD || 'Demo-only-26264!',csrfmiddlewaretoken:token}})).ok()).toBeTruthy();
  const inst=await post('/api/institution-registry',{name:`Final Intelligence Institute ${stamp}`,permanent_id:`FINAL-${stamp}`,region:'Southern',district:'Fictional',reason:'Synthetic browser fixture'});
  expect(inst.status()).toBe(201);institution=(await inst.json()).id;
  const ids:string[]=[];
  for (const bureau of ['RB','PGRC']) {
    const response=await post('/api/cases',{submission_id:crypto.randomUUID(),institution,bureau,source_system:'final-browser',source_reference:crypto.randomUUID(),category:'refunds',summary:'Please refund tuition fees after admission cancellation.',description:'Fictional case. The incident date recorded in this allegation is 2026-08-01.'});
    expect(response.status()).toBe(201);ids.push((await response.json()).id);
  }
  [first,second]=ids;
});
test.afterAll(async()=>{await backend?.dispose();});

test('current brief, exact fact proposal, review and stale conflict retain reason',async({page})=>{
  await login(page);await page.goto(`/cases/${first}`);
  await page.getByText('Case brief: current responsibilities',{exact:true}).click();
  const panel=page.getByRole('region',{name:'Reviewed source facts'});
  await expect(page.getByRole('heading',{name:'Original allegation — not a verified finding'})).toBeVisible();
  await panel.getByLabel('Select supporting text').click();
  await panel.getByLabel('Select supporting text').press('Control+A');
  await panel.getByRole('button',{name:'Propose selected fact'}).click();
  const article=panel.locator('article').first();
  await expect(article).toContainText('pending');
  await article.getByLabel('Fact review rationale').fill('Exact source span checked independently by the demo coordinator.');
  await article.getByRole('button',{name:'Accept fact',exact:true}).click();
  await expect(panel.locator('article').first()).toContainText('accepted');
  const current=await (await backend.get(`/api/cases/${first}/facts`)).json();
  await post(`/api/cases/${first}/facts/${current.results[0].id}/review`,{expected_version:current.results[0].version,state:'rejected',reason:'Concurrent correction fixture'});
  await panel.locator('article').first().getByLabel('Fact review rationale').fill('My retained rationale');
  await panel.getByRole('button',{name:'Accept fact',exact:true}).first().click();
  await expect(panel).toContainText('Another reviewer changed this fact');
  await expect(panel.getByLabel('Fact review rationale').first()).toHaveValue('My retained rationale');
  await page.screenshot({path:artifact('case-intelligence-brief.png'),fullPage:true});
});

test('explicit incident group through institution screen and mobile placement',async({page})=>{
  await login(page);await page.goto(`/institutions/${institution}?section=coordination`);
  const groups=page.getByRole('region',{name:'Manual incident groups'});
  await groups.getByLabel('Incident group title').fill('Fictional tuition incident');
  await groups.getByLabel('Group decision reason').fill('Explicit cases selected; no automatic merging.');
  await expect(groups.getByRole('checkbox')).toHaveCount(2);
  for(const checkbox of await groups.getByRole('checkbox').all()) await checkbox.check();
  await groups.getByRole('button',{name:'Save explicit incident group'}).click();
  await expect(groups.getByRole('heading',{name:'Fictional tuition incident',exact:true})).toBeVisible();
  const stored=await (await backend.get(`/api/incident-groups?institution=${institution}`)).json();
  expect(stored.results[0].cases.map((c:{id:string})=>c.id).sort()).toEqual([first,second].sort());
  await page.setViewportSize({width:390,height:844});
  await expect(groups.getByRole('heading',{name:'Fictional tuition incident',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2)).toBeTruthy();
  await page.screenshot({path:artifact('incident-groups-mobile.png'),fullPage:true});
});

test('officer brief omits restricted relationships and auditor cannot propose',async({page})=>{
  await login(page,'officer_rb');await page.goto(`/cases/${first}`);
  await page.getByText('Case brief: current responsibilities',{exact:true}).click();
  await expect(page.getByRole('heading',{name:'Original allegation — not a verified finding'})).toBeVisible();
  await expect(page.getByText('Human-reviewed same-incident relationships:',{exact:false})).toHaveCount(0);
  // Separate authenticated context avoids relying on logout's CSRF-protected POST flow.
  await page.context().clearCookies();await login(page,'auditor');await page.goto(`/cases/${first}`);
  await page.getByText('Case brief: current responsibilities',{exact:true}).click();
  await expect(page.getByRole('heading',{name:'Source-grounded facts — experimental'})).toBeVisible();
  await expect(page.getByRole('button',{name:'Propose selected fact'})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Accept fact',exact:true})).toHaveCount(0);
});

test('malformed brief reports an error and recovers without a blank page',async({page})=>{
  await login(page);
  await page.route('**/api/cases/*/brief',route=>route.fulfill({json:{case:{},responsibilities:null}}));
  await page.goto(`/cases/${first}`);
  await page.getByText('Case brief: current responsibilities',{exact:true}).click();
  await expect(page.getByText('The server returned incomplete or invalid data.',{exact:false})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Original complaint',exact:true})).toBeVisible();
  await page.unroute('**/api/cases/*/brief');
  await expect(page.getByRole('heading',{name:'Original allegation — not a verified finding'})).toBeVisible();
});
