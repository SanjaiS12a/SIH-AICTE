"""Four fresh isolated HTTP workloads; restore the audit application configuration."""
import io
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[1]


def main():
    audit=json.loads((ROOT/'tests/results/logs/readiness-run.json').read_text())
    final=json.loads(Path(os.environ.get('BENCHMARK_RUN_FILE',ROOT/'tests/results/logs/final-run.json')).read_text(encoding='utf-8-sig'))
    core = os.environ.get('BENCHMARK_CORE_INTELLIGENCE')=='1'
    project=audit['project']
    if not project.startswith('sih-readiness-'):raise ValueError('Audit project required.')
    env=os.environ.copy();env['AUDIT_RESULTS']=audit['directory']
    base=['docker','compose','-p',project,'-f','compose.audit.yaml']
    def run(*args):return subprocess.check_output(args,cwd=ROOT,env=env,text=True,stderr=subprocess.STDOUT)
    current=json.loads(run('docker','inspect',project+'-api-1'))[0]['Config']['Env']
    current=dict(v.split('=',1) for v in current)
    if current.get('POSTGRES_DB')!='coordination_audit':raise ValueError('Start from the preserved audit application configuration.')
    for key in ['ENABLE_REVIEWED_FACTS','ENABLE_INCIDENT_GROUPS']:env[key]=current.get(key,'0')
    destination=Path(final['directory'])/'performance-http';destination.mkdir(exist_ok=False)
    results=[]
    try:
        for rows,concentrated in ([(1000,False),(10000,True)] if core else [(1000,False),(1000,True),(10000,False),(10000,True)]):
            name=f'{rows}-'+('concentrated' if concentrated else 'distributed')
            folder=destination/name;folder.mkdir()
            database='coordination_scale_http_'+uuid.uuid4().hex[:10]
            private='benchmark_'+uuid.uuid4().hex[:10]
            override=folder/'compose-benchmark.json'
            override.write_text(json.dumps({'services':{s:{'environment':{'POSTGRES_DB':database,'ENABLE_REVIEWED_FACTS':'1' if core else '0','ENABLE_INCIDENT_GROUPS':'1' if core else '0'},
                'volumes':[private+':/app/private']} for s in ['api','worker']},'volumes':{private:{}}}),encoding='utf-8')
            command=[*base,'-f',str(override)]
            result={'rows':rows,'distribution':name.split('-',1)[1],'database':database,'folder':str(folder),'passed':False}
            results.append(result)
            print('START '+name,flush=True)
            try:
                run(*base,'stop','api','worker')
                run('docker','exec',project+'-db-1','createdb','-U','audit',database)
                for operation in [('migrate','--noinput'),('createcachetable',)]:run(*command,'run','--rm','--no-deps','api','python','manage.py',*operation)
                setup="""
import json,uuid,os
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import connection
from cases.models import Institution,Bureau,Membership,Complaint,CaseAction
from django_q.tasks import async_task
assert connection.settings_dict['NAME'].startswith('coordination_scale_http_') and not Complaint.objects.exists()
for code in ['RB','PGRC','DEMO']:Bureau.objects.create(code=code,name=code+' synthetic benchmark Bureau')
for i in range(30):Institution.objects.create(name='Fictional benchmark institution '+str(i),permanent_id=f'BENCH-{i:04d}',region='Synthetic',district='Synthetic')
for i in range(10):
 u=User.objects.create_user('readiness-user-'+str(i),password=os.environ['DEMO_PASSWORD']);Membership.objects.create(user=u,role='coordinator')
u=User.objects.get(username='readiness-user-0')
c=Complaint.objects.create(submission_id=uuid.uuid4(),reference='WARMUP',source_system='benchmark-warmup',source_reference='WARMUP',institution=Institution.objects.first(),bureau=Bureau.objects.get(code='RB'),created_by=u,summary='Fictional warmup allegation about admission fee repayment.',description='Synthetic warmup only.',category='refunds',received_at=timezone.now(),due_at=timezone.now())
CaseAction.objects.create(case=c,actor=u,kind='registered',reason='Synthetic warmup outside timed workload')
async_task('cases.matching.match_case',str(c.pk))
"""
                run(*command,'run','--rm','--no-deps','api','python','manage.py','shell','-c',setup)
                run(*command,'up','-d','--no-deps','api','worker')
                warm=time.perf_counter()
                while time.perf_counter()-warm<120:
                    probe=run(*command,'exec','-T','api','python','manage.py','shell','-c',"from cases.models import Complaint;from django_q.models import OrmQ;print(Complaint.objects.filter(matching_state='complete').count(),OrmQ.objects.count())")
                    if probe.strip().splitlines()[-1]=='1 0':break
                    time.sleep(1)
                else:raise TimeoutError('Worker did not warm with an empty queue.')
                result['warmup_seconds']=time.perf_counter()-warm
                env.update(BENCHMARK_URL='http://127.0.0.1:8001',AUDIT_ARTIFACT_DIR=str(folder),AUDIT_PROJECT=project)
                args=[sys.executable,str(ROOT/'scripts/benchmark_import.py'),'--rows',str(rows),'--format','xlsx' if rows==1000 else 'csv','--timeout','1800']
                if concentrated:args.append('--concentrated')
                for script,args_run in [('import',args),('ordinary-http',[sys.executable,str(ROOT/'scripts/benchmark.py')])]:
                    with (folder/(script+'.log')).open('x',encoding='utf-8') as stream:
                        completed=subprocess.run(args_run,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=2100)
                    if completed.returncode:raise RuntimeError(script+' failed; inspect its saved log.')
                if core:
                    with (folder/'incident-http.log').open('x',encoding='utf-8') as stream:
                        completed=subprocess.run([sys.executable,str(ROOT/'scripts/benchmark_incidents.py')],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=300)
                    if completed.returncode:raise RuntimeError('Incident report benchmark failed; inspect its saved log.')
                os.environ.update({key:env[key] for key in ['BENCHMARK_URL','AUDIT_ARTIFACT_DIR']})
                from benchmark import browser, BASE
                from benchmark_import import request
                # Imported modules hold their first RESULTS constant; only request/browser are reused here.
                client,jar=browser();expected=request(client,jar,'/api/cases')['count']
                started=time.perf_counter();export=request(client,jar,'/api/exports',{})
                while time.perf_counter()-started<120:
                    state=request(client,jar,'/api/exports/'+export['id'])
                    if state['state']=='complete':break
                    if state['state']=='failed':raise RuntimeError(state)
                    time.sleep(.5)
                else:raise TimeoutError('Asynchronous export did not complete.')
                export_seconds=time.perf_counter()-started
                started=time.perf_counter()
                with client.open(BASE+'/api/exports/'+export['id']+'/download',timeout=120) as response:
                    count=sum(1 for _ in csv.reader(io.TextIOWrapper(response,encoding='utf-8-sig')))-1
                assert count==expected,(count,expected)
                result.update(passed=True,case_count=expected,async_export_seconds=export_seconds,download_seconds=time.perf_counter()-started,export_rows=count)
                measurements="""
import json
from django.db import connection
with connection.cursor() as c:
 c.execute("SELECT count(*),percentile_cont(.95) WITHIN GROUP(ORDER BY matching_duration_ms),percentile_cont(.95) WITHIN GROUP(ORDER BY matching_queue_ms) FROM cases_complaint WHERE source_system='synthetic-benchmark'")
 print(json.dumps(dict(zip(['cases','matching_execution_p95_ms','queue_delay_p95_ms'],c.fetchone()))))
"""
                result['matching']=json.loads(run(*command,'exec','-T','api','python','manage.py','shell','-c',measurements).strip().splitlines()[-1])
            except Exception as exc:
                result['error']=str(exc)
                (folder/'worker-tail.log').write_text(run(*command,'logs','--tail','80','worker'),encoding='utf-8')
            finally:
                (destination/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
                print(json.dumps(result),flush=True)
    finally:
        run(*base,'up','-d','--no-deps','api','worker')
        print('Audit database and private-volume configuration restored.',flush=True)


if __name__=='__main__':main()
