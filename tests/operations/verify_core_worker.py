"""Actual stop/register/restart recovery on the isolated audit stack only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]


def main():
    audit=json.loads((ROOT/'tests/results/logs/readiness-run.json').read_text(encoding='utf-8-sig'))
    core=json.loads(Path(os.environ.get('CORE_RUN_FILE',ROOT/'tests/results/logs/core-intelligence-run.json')).read_text(encoding='utf-8-sig'))
    project=audit['project']
    if not project.startswith('sih-readiness-'):raise ValueError('Isolated audit project required.')
    os.environ.update(AUDIT_RESULTS=audit['directory'],BENCHMARK_URL='http://127.0.0.1:8001',AUDIT_ARTIFACT_DIR=str(Path(core['directory'])/'worker-probe'))
    def run(*args):return subprocess.check_output(args,cwd=ROOT,text=True,stderr=subprocess.STDOUT)
    env=json.loads(run('docker','inspect',project+'-api-1'))[0]['Config']['Env']
    if 'POSTGRES_DB=coordination_audit' not in env:raise ValueError('Restore the audit API configuration first.')
    sys.path.insert(0,str(ROOT/'scripts'))
    from benchmark import browser
    from benchmark_import import request
    client,jar=browser('coordinator');institution=request(client,jar,'/api/institutions')[0]['id']
    command=['docker','compose','-p',project,'-f','compose.audit.yaml']
    was_running=json.loads(run('docker','inspect',project+'-worker-1'))[0]['State']['Running']
    if not was_running:raise ValueError('Start with a running audit worker to verify recovery.')
    run(*command,'stop','worker')
    try:
        started=time.perf_counter()
        case=request(client,jar,'/api/cases',{'submission_id':str(uuid.uuid4()),'institution':institution,'bureau':'RB',
            'source_system':'core-worker-recovery','source_reference':str(uuid.uuid4()),'category':'refunds',
            'summary':'Fictional admission cancellation tuition repayment remains pending.','description':'Isolated durable queue recovery fixture only.'})
        create_ms=(time.perf_counter()-started)*1000
        assert case['matching_state']=='pending'
        queued=int(run(*command,'exec','-T','api','python','manage.py','shell','-c','from django_q.models import OrmQ;print(OrmQ.objects.count())').strip().splitlines()[-1])
        assert queued>=1
        run(*command,'start','worker');started=time.perf_counter()
        while time.perf_counter()-started<120:
            case=request(client,jar,'/api/cases/'+case['id'])
            if case['matching_state']=='complete':break
            if case['matching_state']=='failed':raise RuntimeError('Recovered task failed; inspect worker logs.')
            time.sleep(.5)
        else:raise TimeoutError('Durable task was not recovered.')
        result={'case_id':case['id'],'pending_while_worker_stopped':True,'durable_queue_rows':queued,
            'registration_ms':create_ms,'restart_to_complete_seconds':time.perf_counter()-started,'matching_state':case['matching_state'],
            'physical_offline':False,'scope':'Actual audit worker restart; no working-demo database access.'}
        with (Path(core['directory'])/'worker-recovery.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
        print(json.dumps(result))
    finally:run(*command,'start','worker')


if __name__=='__main__':main()
