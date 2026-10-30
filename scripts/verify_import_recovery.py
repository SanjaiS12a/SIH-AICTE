"""Verify a confirmed spreadsheet survives a real worker stop/start."""
import json,subprocess,time,uuid
from pathlib import Path
from benchmark import browser
from benchmark_import import request
ROOT=Path(__file__).resolve().parent.parent

def docker(*args):subprocess.run(['docker','compose',*args],cwd=ROOT,check=True)
def main():
 client,jar=browser();inst=request(client,jar,'/api/institutions')[0]['permanent_id'];run=uuid.uuid4().hex[:10];boundary=uuid.uuid4().hex
 csv='source_reference,institution_permanent_id,bureau,category,summary,description,received_at,status,source_system\n'
 for n in range(2):csv+=f'RECOVERY-{run}-{n},{inst},RB,refunds,Tuition refund was withheld after withdrawal.,Fictional worker recovery verification.,2026-08-01T10:00:00+05:30,registered,import-recovery\n'
 body=(f'--{boundary}\r\nContent-Disposition: form-data; name="kind"\r\n\r\ncomplaints\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="recovery.csv"\r\nContent-Type: text/csv\r\n\r\n'+csv+f'\r\n--{boundary}--\r\n').encode()
 docker('stop','worker')
 try:
  job=request(client,jar,'/api/imports',body=body,content_type=f'multipart/form-data; boundary={boundary}');assert job['counts']=={'ready':2},job
  request(client,jar,f"/api/imports/{job['id']}",{'action':'confirm'})
  stopped=request(client,jar,f"/api/imports/{job['id']}");assert stopped['state']=='importing' and stopped['counts']=={'ready':2},stopped
 finally:docker('up','-d','worker')
 started=time.perf_counter()
 while time.perf_counter()-started<120:
  after=request(client,jar,f"/api/imports/{job['id']}")
  if after['state']=='complete':break
  if after['state'] in ('failed','matching_failed'):raise AssertionError(after)
  time.sleep(1)
 assert after['counts']=={'imported':2} and after['matching']=={'complete':2},after
 result={'import_id':job['id'],'queued_while_worker_stopped':stopped['counts'],'after_restart':after['counts'],'matching':after['matching'],'recovery_seconds':time.perf_counter()-started,'real_worker_stop_start':True}
 (ROOT/'reports/import-queue-recovery.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
