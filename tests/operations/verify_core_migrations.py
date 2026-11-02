"""Restore the pre-change audit archive and prove old case data survives 0016/0017."""
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[2]


def main():
    audit=json.loads((ROOT/'tests/results/logs/readiness-run.json').read_text(encoding='utf-8-sig'))
    core=json.loads((ROOT/'tests/results/logs/core-intelligence-run.json').read_text(encoding='utf-8-sig'))
    project=audit['project']
    if not project.startswith('sih-readiness-'):raise ValueError('An isolated audit project is required.')
    os.environ['AUDIT_RESULTS']=audit['directory']
    db=project+'-db-1';name='coordination_core_preservation_'+uuid.uuid4().hex[:10]
    def run(*args):return subprocess.check_output(args,cwd=ROOT,text=True,stderr=subprocess.STDOUT)
    archive=Path(core['directory'])/'preflight/audit.dump'
    if not archive.is_file():raise FileNotFoundError(archive)
    run('docker','exec',db,'createdb','-U','audit',name)
    target='/tmp/'+name+'.dump';run('docker','cp',str(archive),db+':'+target)
    run('docker','exec',db,'pg_restore','-U','audit','-d',name,'--no-owner','--no-acl','--exit-on-error',target)
    def sql(query):return run('docker','exec',db,'psql','-U','audit','-d',name,'-At','-c',query).strip()
    def snapshot():
        result={}
        for table in sql("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'cases_%' ORDER BY tablename").splitlines():
            if not table.replace('_','').isalnum():raise ValueError('Unexpected table identifier.')
            removed={'cases_incidentgroup':"ARRAY['state','retired_at']",'cases_coordinationrecord':"ARRAY['incident_group_id','incident_group_version']"}.get(table,'ARRAY[]::text[]')
            value=sql(f"SELECT count(*),md5(coalesce(string_agg(md5((to_jsonb(t)-{removed})::text),'' ORDER BY id),'')) FROM {table} t").split('|')
            result[table]={'rows':int(value[0]),'original_columns_digest':value[1]}
        return result
    before=snapshot()
    log=run('docker','compose','-p',project,'-f','compose.audit.yaml','exec','-T','-e','POSTGRES_DB='+name,'api','python','manage.py','migrate','--noinput')
    after=snapshot();assert before==after,'Original case data changed during additive migration.'
    result={'database':name,'archive':str(archive),'all_original_case_tables_preserved':True,'before':before,'after':after,'migrations':log,
        'scope':'Independent restoration of the pre-change audit database; original columns compared, new fields excluded from digest.'}
    with (Path(core['directory'])/'migration-preservation.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({'database':name,'tables_verified':len(before),'preserved':True}))


if __name__=='__main__':main()
