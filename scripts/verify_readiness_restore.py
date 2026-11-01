"""Restore the preserved baseline in the audit DB service; never start working writers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid
import zipfile
from verify_source_restore import TABLES

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def snapshot(container, user, database):
    result = {}
    for table in TABLES:
        sql = f"SELECT count(*),md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY id),'')) FROM {table} t"
        count, checksum = run('docker', 'exec', container, 'psql', '-U', user, '-d', database, '-At', '-c', sql).strip().split('|')
        result[table] = {'count': int(count), 'checksum': checksum}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('backup', type=Path)
    args = parser.parse_args()
    backup = args.backup.resolve()
    if not backup.is_relative_to(ROOT / 'backups'): raise ValueError('Use a preserved workspace backup.')
    audit = json.loads((ROOT / 'tests/results/logs/readiness-run.json').read_text())
    if not audit['project'].startswith('sih-readiness-'): raise ValueError('Audit project required.')
    container = audit['project'] + '-db-1'
    database = 'coordination_restore_' + uuid.uuid4().hex[:10]
    restored = backup / database
    restored.mkdir()
    manifest = json.loads((backup / 'manifest.json').read_text())
    with zipfile.ZipFile(backup / 'private-assets.zip') as archive:
        if any(not (restored / item.filename).resolve().is_relative_to(restored) for item in archive.infolist()):
            raise ValueError('Unsafe archive path.')
        archive.extractall(restored)
    assert all(digest(restored / name) == checksum for name, checksum in manifest.items()), 'Restored file checksum mismatch'
    expected = json.loads((ROOT / 'backend/model-manifest.json').read_text())
    assert digest(restored / 'models/minilm/model.safetensors') == expected['weights_sha256']
    assert json.loads((restored / 'models/minilm/revision.json').read_text())['revision'] == expected['revision']
    entries = json.loads(run('docker', 'inspect', 'sih-db-1'))[0]['Config']['Env']
    environment = dict(e.split('=', 1) for e in entries)
    # The working service is read only here. CREATE/RESTORE happen exclusively in the audit service.
    before = snapshot('sih-db-1', environment['POSTGRES_USER'], environment['POSTGRES_DB'])
    run('docker', 'exec', container, 'createdb', '-U', 'audit', database)
    target = '/tmp/' + database + '.dump'
    run('docker', 'cp', str(backup / 'database.dump'), container + ':' + target)
    run('docker', 'exec', container, 'pg_restore', '--no-owner', '--no-acl', '--exit-on-error', '-U', 'audit', '-d', database, target)
    after = snapshot(container, 'audit', database)
    assert before == after, 'Restored baseline differs from preserved working records'
    files = run('docker', 'exec', container, 'psql', '-U', 'audit', '-d', database, '-At', '-c', 'SELECT file FROM cases_attachment').splitlines()
    private = restored / 'backend/private'
    assert all((private / name).resolve().is_relative_to(private) and (private / name).is_file() for name in files), 'Restored attachment is missing'
    assert snapshot('sih-db-1', environment['POSTGRES_USER'], environment['POSTGRES_DB']) == before, 'Working records changed'
    os.environ['AUDIT_RESULTS'] = audit['directory']
    command = ['docker','compose','-p',audit['project'],'-f','compose.audit.yaml','run','--rm','--no-deps',
        '-e','POSTGRES_DB='+database,'-v',str(private)+':/app/private:ro','-v',str(restored/'models')+':/models:ro','api']
    run(*command, 'python', 'manage.py', 'migrate', '--noinput')
    probe = '''
import hashlib,json
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from cases.models import Complaint,CaseAction,Attachment
from cases.matching import encoder,runtime
client=APIClient();client.force_authenticate(User.objects.get(username='coordinator'))
assert client.get('/api/dashboard').status_code==200
assert client.get('/api/institution-registry').status_code==200
downloads=[]
for attachment in Attachment.objects.all():
    response=client.get('/api/attachments/'+str(attachment.pk))
    assert response.status_code==200
    content=b''.join(response.streaming_content);response.close()
    downloads.append({'file':attachment.file.name,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
assert len(encoder().encode('Restored local model verification.'))==384
print(json.dumps({'cases':Complaint.objects.count(),'actions':CaseAction.objects.count(),
    'unknown_historical_bureaus':CaseAction.objects.filter(bureau_at_action__isnull=True).count(),
    'model_revision':runtime()[1],'downloads':downloads,'api_reads_passed':True}))
'''
    application = json.loads(run(*command, 'python', 'manage.py', 'shell', '-c', probe).strip().splitlines()[-1])
    assert application['cases'] == before['cases_complaint']['count']
    assert application['actions'] == application['unknown_historical_bureaus'] == before['cases_caseaction']['count']
    assert application['model_revision'] == expected['revision']
    assert all(item['sha256'] == manifest['backend/private/'+item['file']] for item in application['downloads'])
    result = {'baseline_commit': None, 'baseline_note': 'Working data is compared directly with the preserved rowsets; its originating source commit is not inferred.',
        'verification_commit': run('git', 'rev-parse', 'HEAD').strip(),
        'database_restored': database, 'database_sha256': digest(backup / 'database.dump'),
        'tables': after, 'working_database_unchanged': True,
        'private_and_model_files_restored': len(manifest), 'all_file_checksums_match': True,
        'attachment_references_verified': len(files),
        'restored_application': application,
        'pinned_weights_verified': True, 'restore_directory': str(restored),
        'physical_offline': False, 'limit': 'Restored API reads, migration, files and model checked; physical offline startup is a separate operator gate.'}
    target = Path(audit['directory']) / ('restore-' + database + '.json')
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'tables'}, indent=2))


if __name__ == '__main__':
    main()
