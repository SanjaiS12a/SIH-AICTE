"""Recover the current audit schema, private files and pinned model independently."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.check_output(args,cwd=ROOT,text=True,stderr=subprocess.STDOUT)


def digest(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def snapshot(container,database):
    names=run('docker','exec',container,'psql','-U','audit','-d',database,'-At','-c',
        "SELECT tablename FROM pg_tables WHERE schemaname='public' AND (tablename LIKE 'cases_%' OR tablename IN ('auth_user','django_migrations')) ORDER BY tablename").splitlines()
    result={}
    for name in names:
        if not name.replace('_','').isalnum(): raise ValueError('Unexpected table identifier.')
        value=run('docker','exec',container,'psql','-U','audit','-d',database,'-At','-c',
            f"SELECT count(*),md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY id),'')) FROM {name} t").strip().split('|')
        result[name]={'count':int(value[0]),'rowset_checksum':value[1]}
    return result


def main():
    metadata=json.loads((ROOT/'tests/results/logs/readiness-run.json').read_text())
    current=json.loads(Path(os.environ.get('RESTORE_RUN_FILE',ROOT/'tests/results/logs/final-run.json')).read_text(encoding='utf-8-sig'))
    project=metadata['project']
    if not project.startswith('sih-readiness-'): raise ValueError('Isolated audit project required.')
    os.environ['AUDIT_RESULTS']=metadata['directory']
    base=['docker','compose','-p',project,'-f','compose.audit.yaml']
    database='coordination_restore_final_'+uuid.uuid4().hex[:10]
    backup=ROOT/'backups'/database; backup.mkdir()
    db=project+'-db-1'; api=project+'-api-1'
    env=json.loads(run('docker','inspect',api))[0]['Config']['Env']
    source=next(x.split('=',1)[1] for x in env if x.startswith('POSTGRES_DB='))
    if source!='coordination_audit': raise ValueError('Restore verification must start from audit data, never the working demo or benchmark database.')
    worker_running=json.loads(run('docker','inspect',project+'-worker-1'))[0]['State']['Running']
    run(*base,'stop','worker')
    try:
        before=snapshot(db,source)
        target='/tmp/'+database+'.dump'
        run('docker','exec',db,'pg_dump','-U','audit','-d',source,'-Fc','-f',target)
        run('docker','cp',db+':'+target,str(backup/'database.dump'))
        pack="import zipfile,pathlib; r=pathlib.Path('/app/private'); z=zipfile.ZipFile('/tmp/final-private.zip','w',zipfile.ZIP_DEFLATED); [z.write(p,p.relative_to(r).as_posix()) for p in r.rglob('*') if p.is_file()]; z.close()"
        run('docker','exec',api,'python','-c',pack)
        run('docker','cp',api+':/tmp/final-private.zip',str(backup/'private.zip'))
        private=backup/'private'; private.mkdir()
        with zipfile.ZipFile(backup/'private.zip') as archive:
            if any(not (private/item.filename).resolve().is_relative_to(private) for item in archive.infolist()): raise ValueError('Unsafe recovery archive.')
            archive.extractall(private)
        shutil.copytree(ROOT/'models/minilm',backup/'models/minilm')
        model=json.loads((ROOT/'backend/model-manifest.json').read_text())
        assert digest(backup/'models/minilm/model.safetensors')==model['weights_sha256']
        manifest={str(p.relative_to(backup)).replace('\\','/'):digest(p) for p in backup.rglob('*') if p.is_file()}
        (backup/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        run('docker','exec',db,'createdb','-U','audit',database)
        run('docker','exec',db,'pg_restore','-U','audit','-d',database,'--no-owner','--no-acl','--exit-on-error',target)
        assert snapshot(db,database)==before,'Restored database differs'
        command=[*base,'run','--rm','--no-deps','-e','POSTGRES_DB='+database,'-e','ENABLE_REVIEWED_FACTS=1','-e','ENABLE_INCIDENT_GROUPS=1',
            '-v',str(private)+':/app/private:ro','-v',str(backup/'models')+':/models:ro','api']
        run(*command,'python','manage.py','migrate','--check')
        probe="""
import json,hashlib
from pathlib import Path
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from cases.models import Complaint,Attachment,ReviewedFact,IncidentGroup
from cases.matching import encoder,runtime
c=APIClient();c.force_authenticate(User.objects.get(username='coordinator'))
for path in ['/api/dashboard','/api/institution-registry','/api/overlaps?decision=all','/api/coordination-records','/api/incident-summary','/api/incident-summary/records?metric=confirmed_groups']:
 assert c.get(path).status_code==200,path
case=Complaint.objects.first()
assert c.get('/api/cases/'+str(case.pk)+'/brief').status_code==200
assert c.get('/api/cases/'+str(case.pk)+'/history').status_code==200
files=[]
for attachment in Attachment.objects.all():
 response=c.get('/api/attachments/'+str(attachment.pk));assert response.status_code==200
 content=b''.join(response.streaming_content);response.close()
 files.append({'file':attachment.file.name,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)})
assert len(encoder().encode('Independent restored local model.'))==384
print(json.dumps({'api_reads_passed':True,'model_revision':runtime()[1],'attachment_downloads':files,'facts':ReviewedFact.objects.count(),'incident_groups':IncidentGroup.objects.count()}))
"""
        application=json.loads(run(*command,'python','manage.py','shell','-c',probe).strip().splitlines()[-1])
        assert application['model_revision']==model['revision']
        assert all(item['sha256']==manifest['private/'+item['file']] for item in application['attachment_downloads'])
        assert snapshot(db,source)==before,'Audit source changed during recovery'
        result={'source':'isolated audit fixtures including current case intelligence','source_commit':run('git','rev-parse','HEAD').strip(),
            'restore_database':database,'backup_directory':str(backup),'database_sha256':digest(backup/'database.dump'),
            'all_tables_match':True,'tables':before,'private_and_model_checksums_verified':True,'working_database_accessed':False,
            'restored_application':application,'physical_offline':False,'limit':'Independent database, file and model restore; physical disconnection remains an operator gate.'}
        destination=Path(current['directory'])/'final-restore.json'
        with destination.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
        print(json.dumps({k:v for k,v in result.items() if k!='tables'},indent=2))
    finally:
        if worker_running:run(*base,'start','worker')


if __name__=='__main__':main()
