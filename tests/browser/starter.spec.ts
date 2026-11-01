import { test, expect } from '@playwright/test';
import { resolve } from 'node:path';
import { artifact } from './support';

test('provided beginner Excel file imports, reports six cases and reconciles with CSV', async ({page})=>{
  test.setTimeout(180000);
  await page.context().route(/^https?:\/\//, route =>
    ['127.0.0.1','localhost'].includes(new URL(route.request().url()).hostname) ? route.continue() : route.abort());
  await page.goto('/accounts/login/');
  await page.getByLabel('Username:').fill('coordinator');
  await page.getByLabel('Password:').fill(process.env.DEMO_PASSWORD || 'Demo-only-26264!');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Complaint Monitoring Dashboard',exact:true})).toBeVisible();
  const institutions=await (await page.request.get('/api/institutions')).json();
  const institution=institutions.find((i:any)=>i.permanent_id==='SIH-26264-DEMO');
  expect(institution,'Prepare the fixed SIH demonstration institution before using the starter workbook').toBeTruthy();
  await page.getByRole('link',{name:'Import data',exact:true}).click();
  await page.getByLabel('Spreadsheet',{exact:true}).setInputFiles(resolve('../tests/fixtures/sih-walkthrough/start-here-6-cases.xlsx'));
  await page.getByRole('button',{name:'Upload and preview',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Map and validate columns',exact:true})).toBeVisible();
  await expect(page.getByText(/Unknown institution permanent ID/)).toHaveCount(0);
  await page.screenshot({path:artifact('starter-1-preview.png'),fullPage:true});
  await page.getByRole('button',{name:'Confirm import',exact:true}).click();
  await page.getByRole('link',{name:'Open report',exact:true}).click();
  await expect(page.getByText(/Import complete/)).toBeVisible({timeout:120000});
  const stats=page.locator('.report-workspace .import-stats');
  for(const [label,count] of [['Total','6'],['Pending','5'],['Closed','1']]) {
    await expect(stats.getByText(label,{exact:true}).locator('..').locator('strong')).toHaveText(count);
  }
  await page.screenshot({path:artifact('starter-2-report.png'),fullPage:true});
  await page.getByRole('button',{name:'Export report',exact:true}).click();
  const downloadLink=page.getByRole('link',{name:'Download CSV',exact:true});
  await expect(downloadLink).toBeVisible({timeout:120000});
  const exported=page.waitForEvent('download');await downloadLink.click();
  const download=await exported;const stream=await download.createReadStream();
  const chunks:Buffer[]=[];for await(const chunk of stream!) chunks.push(Buffer.from(chunk));
  expect(Buffer.concat(chunks).toString('utf-8').trim().split(/\r?\n/)).toHaveLength(7);
  await page.goto(`/institutions/${institution.id}`);
  await expect(page.getByRole('heading',{name:institution.name,exact:true})).toBeVisible();
  await page.screenshot({path:artifact('starter-3-institution.png'),fullPage:true});
});

test('provided 1000-row Excel file completes through the real upload workspace', async ({page})=>{
  test.setTimeout(240000);
  await page.goto('/accounts/login/');
  await page.getByLabel('Username:').fill('coordinator');
  await page.getByLabel('Password:').fill(process.env.DEMO_PASSWORD || 'Demo-only-26264!');
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await page.getByRole('link',{name:'Import data',exact:true}).click();
  await page.getByLabel('Spreadsheet',{exact:true}).setInputFiles(resolve('../tests/fixtures/sih-walkthrough/load-test-1000-cases.xlsx'));
  await page.getByRole('button',{name:'Upload and preview',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Map and validate columns',exact:true})).toBeVisible();
  await expect(page.getByText(/Unknown institution permanent ID/)).toHaveCount(0);
  await page.getByRole('button',{name:'Confirm import',exact:true}).click();
  await page.getByRole('link',{name:'Open report',exact:true}).click();
  await expect(page.getByText(/Import complete/)).toBeVisible({timeout:180000});
  const stats=page.locator('.report-workspace .import-stats');
  for(const [label,count] of [['Total','1000'],['Pending','1000'],['Closed','0']]) {
    await expect(stats.getByText(label,{exact:true}).locator('..').locator('strong')).toHaveText(count);
  }
  await page.screenshot({path:artifact('starter-4-thousand-row-report.png'),fullPage:true});
});
