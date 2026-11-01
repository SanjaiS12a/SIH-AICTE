import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";
import { artifact } from "./support";

async function login(page: Page) {
  await page.goto("/accounts/login/");
  await page.getByLabel("Username:").fill("coordinator");
  await page.getByLabel("Password:").fill(process.env.DEMO_PASSWORD || "Demo-only-26264!");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Complaint Monitoring Dashboard", exact: true })).toBeVisible();
}

test("dashboard rejects nested omissions and null counts while genuine zero remains valid", async ({ page }) => {
  await login(page);
  const good = await (await page.request.get("/api/dashboard")).json();
  const errors: string[] = []; page.on("pageerror", e => errors.push(e.message));
  for (const bad of [{ ...good, management: {} }, { ...good, ageing: undefined }, { ...good, pending: null },
    {...good, management:{...good.management,institutions:[{...good.management.institutions[0],bureau_details:{invalid:true}}]}}]) {
    await page.route("**/api/dashboard?*", route => route.fulfill({ json: bad }));
    await page.goto("/?category=refunds");
    await expect(page.getByRole("alert")).toContainText("incomplete or invalid data");
    await expect(page.locator("main")).toBeVisible();
    await page.unroute("**/api/dashboard?*");
  }
  await page.goto("/?from=2000-01-01&to=2000-01-31");
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Open complaints/ })).toContainText("0");
  expect(errors).toEqual([]);
});

test("a page render failure preserves navigation and resets on route change", async ({ page }) => {
  await login(page);
  await page.route("**/api/institutions", route => route.fulfill({ json: { unexpected: true } }));
  await page.goto("/cases/new");
  await expect(page.getByRole("heading", { name: "This page could not be displayed" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry page" })).toBeVisible();
  await page.unroute("**/api/institutions");
  await page.getByRole("button", { name: "Retry page" }).click();
  await expect(page.getByRole("heading", { name: "Register a complaint", exact:true })).toBeVisible();
  await page.getByRole("link", { name: "Institutions", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Institutions", exact: true })).toBeVisible();
});

test("operational homepage totals and all-time acknowledgment drilldown reconcile", async ({ page }) => {
  await login(page);
  const filters = "from=2000-01-01&to=2000-01-31&region=Southern";
  await page.goto(`/?${filters}`);
  const facts = await (await page.request.get(`/api/dashboard?${filters}`)).json();
  for (const [label, key] of [["Received complaints", "total"], ["Open complaints", "pending"], ["Under-process complaints", "under_process"], ["Closed complaints", "disposed"]]) {
    await expect(page.getByRole("button", { name: label, exact: false }).locator("strong")).toHaveText(String(facts[key]));
    await page.getByRole("button", { name: label, exact: false }).click();
    const q = new URL(page.url()).search;
    expect((await (await page.request.get(`/api/cases${q}`)).json()).count).toBe(facts[key]);
    await page.goto(`/?${filters}`);
  }
  const link = page.getByRole('link', { name: /records awaiting acknowledgment/ });
  await expect(link).toContainText(String(facts.management.pending_acknowledgment_records));
  await link.click();
  expect(new URL(page.url()).searchParams.get('from')).toBeNull();
  expect(new URL(page.url()).searchParams.get('region')).toBe('Southern');
  expect((await (await page.request.get(`/api/coordination-records${new URL(page.url()).search}`)).json()).count).toBe(facts.management.pending_acknowledgment_records);
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Priority institutions',exact:true})).toBeVisible();
  await page.screenshot({path: artifact('readiness-operational-home.png'), fullPage:true});
});

test("source upload history uses server pagination and retains conflict filters", async ({ page }) => {
  await login(page);
  const requested: string[] = [];
  await page.route('**/api/source-intake/jobs?*', route => {
    const q = new URL(route.request().url()).searchParams;
    requested.push(q.toString());
    const second = q.get('page') === '2';
    return route.fulfill({json:{count:21,next:second?null:'?page=2',previous:second?'?page=1':null,
      results: Array.from({length:second?1:20},(_,i)=>({id:`10000000-0000-4000-8000-${String((second?20:0)+i).padStart(12,'0')}`,filename:`source-${(second?20:0)+i}.csv`,source_system:'legacy',source_bureau:'RB',state:'complete',created_at:'2026-10-31T12:00:00Z',registered_at:null,total_rows:2,unresolved_conflicts:1}))}});
  });
  await page.goto('/imports/source-jobs?source=legacy&bureau=RB&conflicts=true');
  const table=page.getByRole('region',{name:'Source upload history',exact:true});
  await expect(table.locator('tbody tr')).toHaveCount(20);
  await page.getByRole('button',{name:'Next',exact:true}).click();
  await expect(table.locator('tbody tr')).toHaveCount(1);
  expect(requested.some(q=>q.includes('page=2') && q.includes('conflicts=true') && q.includes('source=legacy'))).toBeTruthy();
  await table.getByRole('link',{name:'1',exact:true}).click();
  await expect(page).toHaveURL(/rows\?state=conflict/);
});

test("invalid coordination assignments have a visible reassignment warning", async ({page})=>{
  await login(page);
  const id='10000000-0000-4000-8000-000000000099';
  await page.route(`**/api/coordination-records/${id}`,route=>route.fulfill({json:{id,institution_id:id,institution_name:'Synthetic assignment fixture',lead_bureau_name:'Regulation Bureau',lead_officer_name:'Former officer',reason:'Review responsibilities',state:'in_coordination',outcome:'',version:1,cases:[],participants:[{id:1,bureau:'Regulation Bureau',bureau_code:'RB',officer_id:1,officer_name:'Former officer',assignment_current:false,instruction:'Check evidence',action_date:null,acknowledged_at:null,completed_at:null,completion_note:''}]}}));
  await page.route(`**/api/coordination-records/${id}/history?*`,route=>route.fulfill({json:{count:0,next:null,previous:null,results:[]}}));
  await page.goto(`/coordination/workspace/${id}`);
  await expect(page.getByRole('status').filter({hasText:'Reassignment needed'})).toBeVisible();
  await expect(page.getByText('Revise this Bureau’s agreed action',{exact:true})).toBeVisible();
});

test("report institution escalation drilldown excludes closed cases while the cohort total retains them", async ({page})=>{
  await login(page);
  async function post(url:string,data:unknown) {
    const token=(await page.context().cookies()).find(c=>c.name==='csrftoken')!.value;
    const response=await page.request.post(url,{data,headers:{'X-CSRFToken':token}});
    expect(response.ok()).toBeTruthy();return response.json();
  }
  const stamp=crypto.randomUUID();
  const institution=await post('/api/institution-registry',{name:`Scope fixture ${stamp}`,permanent_id:`SC-${stamp}`,region:'Southern',district:'Synthetic',reason:'Synthetic scope regression'});
  for (const close of [false,true]) {
    const c=await post('/api/cases',{submission_id:crypto.randomUUID(),institution:institution.id,bureau:'RB',source_reference:crypto.randomUUID(),category:'refunds',summary:'Synthetic fee refund requires supervisory review.',description:'Fictional scope acceptance fixture.'});
    await post(`/api/cases/${c.id}/escalations`,{submission_id:crypto.randomUUID(),expected_version:1,reason:'Independent supervisory review'});
    if(close) await post(`/api/cases/${c.id}/actions`,{kind:'status',status:'disposed',expected_version:2,reason:'Fictional case resolution; supervisory review remains independent.'});
  }
  await page.goto(`/reports?institution=${institution.id}`);
  const row=page.getByRole('region',{name:'Institution workload',exact:true}).locator('tbody tr');
  const link=row.locator('a[href*="/escalations"]');
  await expect(link).toHaveText('1');
  const href=await link.getAttribute('href');
  expect((await (await page.request.get(`/api/escalations${new URL(href!,page.url()).search}`)).json()).count).toBe(1);
  const total=page.getByRole('link',{name:/Unresolved escalations/});
  await expect(total.locator('strong')).toHaveText('2');
  const totalHref=await total.getAttribute('href');
  expect((await (await page.request.get(`/api/escalations${new URL(totalHref!,page.url()).search}`)).json()).count).toBe(2);
});
