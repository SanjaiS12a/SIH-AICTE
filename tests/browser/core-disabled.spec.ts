import { test, expect } from '@playwright/test';

test('Disabled feature gates hide incident intelligence and reject direct API access',async({page})=>{
  test.skip(process.env.TEST_FEATURE_GATES!=='disabled','Run separately against the audit stack with both flags disabled.');
  await page.goto('/accounts/login/');
  await page.getByLabel('Username:').fill('coordinator');
  await page.getByLabel('Password:').fill(process.env.DEMO_PASSWORD||'Demo-only-26264!');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Complaint Monitoring Dashboard',exact:true})).toBeVisible();
  const response=await page.request.get('/api/institutions');expect(response.ok()).toBeTruthy();
  const institutions=await response.json();expect(institutions.length).toBeGreaterThan(0);
  await page.goto(`/institutions/${institutions[0].id}`);
  await expect(page.getByRole('region',{name:'Complaint and incident counts'})).toHaveCount(0);
  for(const url of ['/api/incident-summary','/api/incident-summary/records','/api/incident-summary.csv','/api/incident-groups']){
    expect((await page.request.get(url)).status()).toBe(404);
  }
});
