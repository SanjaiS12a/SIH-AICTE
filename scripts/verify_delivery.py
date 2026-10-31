"""Restore private assets/database, rehearse on an internal Docker network, then resume the demo.

Temporarily occupies localhost:8000. Physical Wi-Fi is NOT disabled by this check.
"""
import hashlib
import json
import subprocess
import time
import urllib.request
import uuid
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BACKUPS=ROOT/'backups'
RESULTS=ROOT/'tests/results'
TABLES=['cases_institution','cases_bureau','cases_membership','cases_complaint','cases_caseaction','cases_overlapcandidate','cases_escalation','cases_notification']

def run(*args):
    return subprocess.check_output(list(args),cwd=ROOT,text=True,stderr=subprocess.STDOUT)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def shell(container,code):
    output=run('docker','exec',container,'python','manage.py','shell','-c',code)
    return json.loads(output.strip().splitlines()[-1])

def snapshot(container,compose=False):
    result={}
    for table in TABLES:
        sql=f"SELECT count(*),md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY id),'')) FROM {table} t"
        command=['docker','compose','exec','-T','db'] if compose else ['docker','exec',container]
        value=run(*command,'sh','-c','psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "$1"','sh',sql).strip().split('|')
        result[table]={'count':int(value[0]),'checksum':value[1]}
    return result

def main():
    nonce=uuid.uuid4().hex[:10];prefix='aicte-offline-'+nonce;network=prefix+'-net'
    names={kind:prefix+'-'+kind for kind in ['db','api','worker']}
    stage=(BACKUPS/(prefix+'-restored')).resolve()
    assert stage.is_relative_to(BACKUPS.resolve()) and not stage.exists()
    stage.mkdir(parents=True)
    dump=BACKUPS/(prefix+'.dump');archive=BACKUPS/(prefix+'-assets.zip')
    report={'physical_offline':False,'physical_limit':'Windows token is not elevated; physical Wi-Fi disconnection was not performed. This is a separate internal-network/no-egress rehearsal.', 'source_commit':run('git','rev-parse','HEAD').strip(),'migration':'0010_manual_relationship_origin','private_assets_archive':archive.name,'database_archive':dump.name}
    image=json.loads(run('docker','inspect','sih-api-1'))[0]['Config']['Image']
    envs={}
    for kind,container in [('api','sih-api-1'),('db','sih-db-1')]:
        entries=json.loads(run('docker','inspect',container))[0]['Config']['Env']
        envs[kind]='\n'.join(e for e in entries if e.startswith(('POSTGRES_','DB_','DJANGO_','DEMO_PASSWORD=','MODEL_PATH=','HF_HUB_OFFLINE=')))+'\n'
    stopped=False;created=[];network_created=False
    try:
        # Stop writers before taking the matching database/filesystem snapshot.
        run('docker','compose','stop','api','worker');stopped=True
        before=snapshot('db',compose=True)
        run('docker','compose','exec','-T','db','sh','-c','pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/delivery.dump')
        run('docker','cp','sih-db-1:/tmp/delivery.dump',str(dump))
        manifest={}
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for folder in ['backend/private','models/minilm','frontend/dist']:
                for path in sorted((ROOT/folder).rglob('*')):
                    if path.is_file() and not path.name.endswith('.partial'):
                        key=path.relative_to(ROOT).as_posix();z.write(path,key);manifest[key]=digest(path)
            for key,path in [('configuration/source.env',ROOT/'.env'),('configuration/compose.yaml',ROOT/'compose.yaml'),('models/minilm/LICENSE',ROOT/'data/research/public_pairs/MODEL-APACHE2-LICENSE.txt')]:
                z.write(path,key);manifest[key]=digest(path)
            for kind,value in envs.items():
                key=f'configuration/{kind}.env';z.writestr(key,value);manifest[key]=hashlib.sha256(value.encode()).hexdigest()
        with zipfile.ZipFile(archive) as z:
            for entry in z.infolist():
                assert (stage/entry.filename).resolve().is_relative_to(stage)
            z.extractall(stage)
        assert all(digest(stage/key)==value for key,value in manifest.items())
        assert digest(stage/'configuration/source.env')==digest(ROOT/'.env')
        report.update(assets_restored_and_verified=True,configuration_verified=True,asset_files=len(manifest),database_sha256=digest(dump),assets_sha256=digest(archive))
        run('docker','network','create','--internal',network);network_created=True
        report['internal_network']=json.loads(run('docker','network','inspect',network))[0]['Internal']
        run('docker','run','-d','--name',names['db'],'--network',network,'--network-alias','db','--env-file',str(stage/'configuration/db.env'),'-e','POSTGRES_DB=delivery_check','--shm-size','256mb','pgvector/pgvector:pg17');created.append(names['db'])
        for _ in range(40):
            try:run('docker','exec',names['db'],'sh','-c','pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"');break
            except subprocess.CalledProcessError:time.sleep(1)
        else:raise RuntimeError('Restored PostgreSQL did not start')
        run('docker','cp',str(dump),names['db']+':/tmp/delivery.dump')
        run('docker','exec',names['db'],'sh','-c','pg_restore --exit-on-error -U "$POSTGRES_USER" -d "$POSTGRES_DB" /tmp/delivery.dump')
        assert snapshot(names['db'])==before
        report['database_restored_and_verified']=before
        common=['--network',network,'--env-file',str(stage/'configuration/api.env'),'-e','POSTGRES_DB=delivery_check','-e','DB_HOST=db','-e','DB_PORT=5432','-e','HF_HUB_OFFLINE=1','-e','TRANSFORMERS_OFFLINE=1',
            '-v',str(ROOT/'backend')+':/app:ro','-v',str(ROOT/'tests')+':/app/tests','-v',str(RESULTS)+':/reports','-v',str(stage/'models')+':/models:ro','-v',str(stage/'backend/private')+':/app/private']
        run('docker','run','-d','--name',names['api'],*common,'-p','127.0.0.1:8000:8000',image,'python','manage.py','runserver','0.0.0.0:8000','--noreload','--insecure');created.append(names['api'])
        run('docker','run','-d','--name',names['worker'],*common,image,'python','manage.py','qcluster');created.append(names['worker'])
        for _ in range(45):
            try:
                with urllib.request.urlopen('http://127.0.0.1:8000/api/session',timeout=2) as response:assert response.status==200
                break
            except Exception:time.sleep(1)
        else:raise RuntimeError('Isolated API did not start')
        probe="import socket,json; blocked=False\ntry: socket.create_connection(('1.1.1.1',443),timeout=2)\nexcept OSError: blocked=True\nassert blocked;print(json.dumps({'external_egress_blocked':blocked}))"
        report['egress_probe']=json.loads(run('docker','exec',names['api'],'python','-c',probe).strip())
        model_started=time.perf_counter()
        report['model']=shell(names['api'],"import json,time,numpy as np;from cases.matching import encoder,tokenizer,runtime;s=time.perf_counter();assert len(tokenizer().encode('Fictional local grievance.',add_special_tokens=True).ids)<=256;v=encoder().encode(['Fictional local grievance.'],normalize_embeddings=True);assert v.shape==(1,384) and np.isfinite(v).all() and abs(float(np.linalg.norm(v[0]))-1)<1e-5;print(json.dumps({'dimension':384,'local_only':True,'load_and_inference_seconds_after_imports':time.perf_counter()-s,'revision':runtime()[1],'threshold':runtime()[2]}))")
        report['model']['container_exec_seconds_including_imports']=time.perf_counter()-model_started
        # Existing browser configuration uses this localhost API and the bundled Vite preview.
        with (RESULTS/'logs/completion-isolated-browser.log').open('w',encoding='utf-8') as log:
            subprocess.run(['npx.cmd','playwright','test'],cwd=ROOT/'frontend',stdout=log,stderr=subprocess.STDOUT,check=True)
        report['isolated_full_browser_passed']=True
        run('docker','stop',names['worker'])
        queued=shell(names['api'],"import json,uuid;from django.contrib.auth.models import User;from rest_framework.test import APIClient;from cases.models import Complaint;from django_q.models import OrmQ;c=APIClient();c.force_authenticate(User.objects.get(username='coordinator'));i=Complaint.objects.filter(source_system='sih-demo').first().institution_id;r=c.post('/api/cases',{'submission_id':str(uuid.uuid4()),'institution':str(i),'bureau':'RB','source_system':'isolated-recovery','source_reference':str(uuid.uuid4()),'category':'refunds','summary':'Fictional tuition refund remains unpaid.','description':'Isolated restart check.'},format='json');assert r.status_code==201;r=r.data;e=c.post(f\"/api/cases/{r['id']}/escalations\",{'submission_id':str(uuid.uuid4()),'expected_version':r['version'],'reason':'Verify durable notification recovery'},format='json');assert e.status_code==201;assert OrmQ.objects.exists();print(json.dumps({'case':r['id'],'escalation':str(e.data['id']),'queued_while_stopped':True}))")
        run('docker','start',names['worker']);started=time.monotonic()
        for _ in range(90):
            state=shell(names['api'],f"import json;from cases.models import Complaint,Notification;c=Complaint.objects.get(pk='{queued['case']}');print(json.dumps({{'state':c.matching_state,'notifications':Notification.objects.filter(escalation_id='{queued['escalation']}').count(),'matching_ms':c.matching_duration_ms,'queue_ms':c.matching_queue_ms}}))")
            if state['state']=='complete' and state['notifications']>0:break
            if state['state']=='failed':raise AssertionError(state)
            time.sleep(1)
        else:raise RuntimeError('Worker restart recovery timed out')
        repeat=shell(names['api'],f"import json;from cases.tasks import notify_escalation;print(json.dumps({{'new_notifications':notify_escalation('{queued['escalation']}')}}))")
        assert repeat['new_notifications']==0
        report['worker_recovery']={**queued,**state,'recovery_seconds':time.monotonic()-started,'notification_retry_added':0}
        # Fault injection is isolated; accelerate timeouts, retaining the production three-attempt bound.
        for _ in range(30):
            pending=shell(names['api'],"import json;from django_q.models import OrmQ,Schedule;Schedule.objects.update(repeats=0);print(json.dumps({'pending':OrmQ.objects.count()}))")
            if pending['pending']==0:break
            time.sleep(1)
        else:raise RuntimeError('Isolated queue was not idle before fault injection')
        run('docker','stop',names['worker'])
        fault=shell(names['api'],"import json;from django_q.tasks import async_task;print(json.dumps({'id':async_task('operator.truediv',1,0,task_name='isolated-delivery-failure')}))")
        fault_name=prefix+'-fault-worker'
        fault_code="import os;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings');from django.conf import settings;settings.Q_CLUSTER={**settings.Q_CLUSTER,'timeout':1,'retry':2,'max_attempts':3};import django;django.setup();from django.core.management import call_command;call_command('qcluster')"
        run('docker','run','-d','--name',fault_name,*common,image,'python','-c',fault_code);created.append(fault_name)
        for _ in range(35):
            failure=shell(names['api'],f"import json;from django_q.models import Failure;f=Failure.objects.filter(pk='{fault['id']}').first();print(json.dumps({{'attempts':f.attempt_count if f else 0}}))")
            if failure['attempts']==3:break
            time.sleep(1)
        else:raise RuntimeError('The three-attempt fault did not reach its failure limit')
        time.sleep(3)
        exhausted=shell(names['api'],f"import json;from django_q.models import Failure,OrmQ;f=Failure.objects.get(pk='{fault['id']}');assert f.attempt_count==3 and OrmQ.objects.count()==0;print(json.dumps({{'no_further_attempts':True}}))")
        admin_check=shell(names['api'],"import json;from django.contrib.auth.models import User;from django.test import Client;c=Client();c.force_login(User.objects.get(username='admin'));r=c.get('/admin/django_q/failure/');assert r.status_code==200 and b'isolated-delivery-failure' in r.content;print(json.dumps({'failed_task_admin_visible':True}))")
        report['exhausted_retry_visibility']={**failure,**admin_check,**exhausted,'isolated_retry_seconds':2,'isolated_timeout_seconds':1,'production_policy_unchanged':True}
        report['working_database_unchanged']=snapshot('db',compose=True)==before
        assert report['working_database_unchanged']
    finally:
        for name in reversed(created):
            try:run('docker','rm','-f','-v',name)
            except subprocess.CalledProcessError:pass
        if network_created:
            try:run('docker','network','rm',network)
            except subprocess.CalledProcessError:pass
        if stopped:run('docker','compose','start','api','worker')
        (RESULTS/'completion-delivery.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['database_restored_and_verified']},indent=2))

if __name__=='__main__':main()
