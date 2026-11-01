"""HTTP upload-to-report benchmark. Retains explicitly synthetic benchmark imports."""
import argparse
import ctypes
import concurrent.futures
import csv
import io
import json
import os
import platform
import statistics
import subprocess
import threading
import sys
import time
import urllib.request
import uuid
from pathlib import Path
from benchmark import browser,BASE,RESULTS
ROOT=Path(__file__).resolve().parent.parent

class Memory(ctypes.Structure):
 _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(name,ctypes.c_ulonglong) for name in ['total','available','total_page','available_page','total_virtual','available_virtual','extended']]

def memory():
 if os.name!='nt':return None
 state=Memory();state.length=ctypes.sizeof(state)
 if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):raise OSError('Memory sampling failed')
 assert state.total>=state.available>0
 return {'total_bytes':state.total,'used_bytes':state.total-state.available}

def request(client,jar,path,payload=None,body=None,content_type=None):
 headers={}
 if payload is not None:body=json.dumps(payload).encode();content_type='application/json'
 if body is not None:
  headers={'X-CSRFToken':next(c.value for c in jar if c.name=='csrftoken'),'Content-Type':content_type}
 with client.open(urllib.request.Request(BASE+path,data=body,headers=headers),timeout=180) as response:return json.loads(response.read())

def simulate(index):
 client,jar=browser(f"readiness-user-{index+1}");values=[]
 for kind,path in [('dashboard','/api/dashboard'),('read','/api/cases')]*3:
  start=time.perf_counter();result=request(client,jar,path);values.append((kind,(time.perf_counter()-start)*1000))
 return values

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--rows',type=int,default=1000);parser.add_argument('--format',choices=['csv','xlsx'],default='csv');parser.add_argument('--concentrated',action='store_true');parser.add_argument('--kind',choices=['complaints','monthly','snapshot'],default='complaints');parser.add_argument('--timeout',type=int,default=1800);args=parser.parse_args()
 if not 1<=args.rows<=100000:raise ValueError('Use 1 to 100,000 rows; uploads are split into 10,000-row files.')
 project=os.environ['AUDIT_PROJECT']
 if not project.startswith('sih-readiness-'):raise ValueError('Use the audit project only.')
 client,jar=browser();institutions=request(client,jar,'/api/institutions');bureaus=request(client,jar,'/api/options')['bureaus'];run=uuid.uuid4().hex[:10];results=[];start_all=time.perf_counter()
 dest=ROOT/'data/benchmarks';dest.mkdir(parents=True,exist_ok=True)
 resources=[];stop=threading.Event()
 def sample():
  while not stop.is_set():
   try:
    stats=subprocess.check_output(['docker','stats','--no-stream','--format','{{json .}}',*[f'{project}-{service}-1' for service in ['api','worker','db']]],timeout=10,text=True)
    sample={'elapsed_seconds':time.perf_counter()-start_all,'containers':[json.loads(line) for line in stats.splitlines() if line.strip()],'host_memory':memory()}
    try:sample['gpu']=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=5,text=True).strip()
    except (OSError,subprocess.SubprocessError) as exc:sample['gpu_sampling_error']=str(exc)
    resources.append(sample)
   except Exception as exc:resources.append({'sampling_error':str(exc)})
   stop.wait(1)
 monitor=threading.Thread(target=sample,daemon=True);monitor.start()
 for offset in range(0,args.rows,10000):
  rows=[]
  for n in range(offset,min(offset+10000,args.rows)):
   institution=institutions[0 if args.concentrated else n%len(institutions)];bureau=bureaus[n%len(bureaus)]['code'];category=['refunds','admissions','documents','facilities','scholarships','administration'][n%6]
   common={'institution_permanent_id':institution['permanent_id'],'bureau':bureau,'category':category}
   if args.kind!='complaints':
    common['bureau']=bureaus[(n//(30*312))%len(bureaus)]['code']
    common['category']=['refunds','admissions','documents','facilities','scholarships','administration'][(n//(30*312*len(bureaus)))%6]
   if args.kind=='complaints':
    summary=[f'Tuition fees have not been refunded following cancellation of admission for programme cohort {n%200}. The student requests repayment and a written response from the institution.',f'Original certificates remain with the college following withdrawal from programme cohort {n%200}. The applicant requests return of the documents for admission elsewhere.',f'The merit scholarship sanctioned for programme cohort {n%200} has not reached the student. Please verify the payment record and provide the disbursement status.'][n%3]
    disposed=n%7==0
    rows.append({**common,'source_system':'synthetic-benchmark','source_reference':f'BENCH-{run}-{n}','summary':summary,'description':summary+' This is an explicitly fictional performance-test record. The institution should check its register, verify supporting receipts and record a written response. No real student, institution allegation or personal information is included.','received_at':'2026-08-01T10:00:00+05:30','status':'disposed' if disposed else ['registered','under_review','awaiting_response'][n%3],'disposed_at':'2026-08-20T10:00:00+05:30' if disposed else '', 'resolution_note':'Fictional benchmark resolution recorded.' if disposed else ''})
   elif args.kind=='monthly':rows.append({**common,'month':f'{2000+(n//30%312)//12:04d}-{n//30%12+1:02d}','received':10+n%30,'disposed':5+n%10})
   else:rows.append({**common,'snapshot_date':f'{2020+(n//30%2016)//336:04d}-{n//30//28%12+1:02d}-{n//30%28+1:02d}','registered':10,'under_review':4,'awaiting_response':3,'disposed':5,'overdue':2})
  stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows);raw=stream.getvalue().encode()
  filename=f'{args.kind}-{run}-{offset}.{args.format}'
  if args.format=='xlsx':
   from openpyxl import Workbook
   book=Workbook(write_only=True);sheet=book.create_sheet('Data');sheet.append(list(rows[0]));
   for row in rows:sheet.append(list(row.values()))
   binary=io.BytesIO();book.save(binary);raw=binary.getvalue()
  (dest/filename).write_bytes(raw)
  boundary=uuid.uuid4().hex;body=(f'--{boundary}\r\nContent-Disposition: form-data; name="kind"\r\n\r\n{args.kind}\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: text/csv\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
  started=time.perf_counter();job=request(client,jar,'/api/imports',body=body,content_type=f'multipart/form-data; boundary={boundary}');preview=time.perf_counter()-started
  assert job['counts'].get('ready',0)+job['counts'].get('duplicate',0)==len(rows),job
  confirmed=time.perf_counter();request(client,jar,f"/api/imports/{job['id']}",{'action':'confirm'})
  stats_at=None;statistics_report=None
  with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
   future=pool.submit(lambda:list(pool.map(simulate,range(9))))
   while time.perf_counter()-confirmed<args.timeout:
    job=request(client,jar,f"/api/imports/{job['id']}")
    if not job['counts'].get('ready') and stats_at is None:
     statistics_report=request(client,jar,f"/api/imports/{job['id']}/report")
     if args.kind=='complaints':assert statistics_report['total']==len(rows)
     stats_at=time.perf_counter()-confirmed
    if job['state'] in ('complete','matching_failed','failed'):break
    time.sleep(1)
   latencies=[item for batch in future.result() for item in batch]
  report=request(client,jar,f"/api/imports/{job['id']}/report")
  if args.kind=='complaints':assert report['total']==len(rows),(report['total'],len(rows))
  assert job['state']=='complete',job
  results.append({'import_id':job['id'],'rows':len(rows),'preview_seconds':preview,'statistics_ready_seconds':stats_at,'statistics_report_total':statistics_report.get('total') if statistics_report else None,'statistics_report_matching':statistics_report.get('matching') if statistics_report else None,'matching_and_report_seconds':time.perf_counter()-confirmed,'counts':job['counts'],'matching':job['matching'],'stage_timings':job.get('timings',{}),
   'latency':{kind:{'requests':len(v:=sorted(ms for k,ms in latencies if k==kind)),'p50_ms':statistics.median(v),'p95_ms':v[min(len(v)-1,int(.95*len(v)))]} for kind in ['dashboard','read']}})
 stop.set();monitor.join(timeout=12)
 output={'resources':resources,'format':args.format,'run':run,'kind':args.kind,'rows':args.rows,'distribution':'one institution' if args.concentrated else 'distributed institutions','platform':platform.platform(),'concurrent_sessions':10,'transport':'HTTP localhost; ten distinct users, nine readers alongside importer','total_seconds':time.perf_counter()-start_all,'results':results,'limits':'Synthetic performance data; no million-row claim. Shared laptop workload may affect results.'}
 path=RESULTS/f"completion-import-{args.kind}-{args.rows}-{'concentrated' if args.concentrated else 'distributed'}.json";
 if path.exists():raise FileExistsError(path)
 path.write_text(json.dumps(output,indent=2),encoding='utf-8');print(json.dumps(output,indent=2))
if __name__=='__main__':main()
