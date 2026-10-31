"""Restore a fresh database backup separately, retaining both recovery artifacts."""
import json
import uuid
from pathlib import Path
from verify_delivery import run, digest, ROOT

TABLES = ['auth_user', 'cases_institution', 'cases_bureau', 'cases_membership', 'cases_complaint',
          'cases_caseaction', 'cases_overlapcandidate', 'cases_escalation', 'cases_notification',
          'cases_coordinationrecord', 'cases_coordinationparticipant', 'cases_coordinationrecord_cases',
          'cases_importjob', 'cases_importrow', 'cases_summaryrecord', 'cases_attachment', 'cases_auditevent', 'cases_modelrelease']


def snapshot(database):
    result = {}
    for table in TABLES:
        sql = f"SELECT count(*),md5(coalesce(string_agg(md5(to_jsonb(t)::text),'' ORDER BY id),'')) FROM {table} t"
        values = run('docker', 'compose', 'exec', '-T', 'db', 'sh', '-c',
                     'psql -U "$POSTGRES_USER" -d "$1" -At -c "$2"', 'sh', database, sql).strip().split('|')
        result[table] = {'count': int(values[0]), 'checksum': values[1]}
    return result


def main():
    nonce = uuid.uuid4().hex[:10]
    restored = 'coordination_source_restore_' + nonce
    dump = ROOT / 'backups' / ('source-intake-latest-' + nonce + '.dump')
    assert restored.startswith('coordination_source_restore_') and dump.resolve().is_relative_to((ROOT / 'backups').resolve())
    assert not dump.exists()
    entries = json.loads(run('docker', 'inspect', 'sih-db-1'))[0]['Config']['Env']
    original = next(e.split('=', 1)[1] for e in entries if e.startswith('POSTGRES_DB='))
    assert original != restored
    report = {'source_commit': run('git', 'rev-parse', 'HEAD').strip(), 'migration': '0012',
              'restore_database': restored, 'dump': dump.name, 'scope': 'Database only; files/models and physical offline startup are not tested here.'}
    run('docker', 'compose', 'stop', 'api', 'worker')
    try:
        before = snapshot(original)
        run('docker', 'compose', 'exec', '-T', 'db', 'sh', '-c', 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/source-latest.dump')
        run('docker', 'cp', 'sih-db-1:/tmp/source-latest.dump', str(dump))
        run('docker', 'compose', 'exec', '-T', 'db', 'sh', '-c', 'createdb -U "$POSTGRES_USER" "$1"', 'sh', restored)
        run('docker', 'compose', 'exec', '-T', 'db', 'sh', '-c', 'pg_restore -U "$POSTGRES_USER" -d "$1" --exit-on-error /tmp/source-latest.dump', 'sh', restored)
        assert snapshot(restored) == before, 'Restored rows differ'
        assert snapshot(original) == before, 'Working database changed'
        report.update(full_restore_verified=True, working_database_unchanged=True, snapshot=before, dump_sha256=digest(dump))
    finally:
        (ROOT / 'tests/results/source-intake-latest-restore.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        run('docker', 'compose', 'start', 'api', 'worker')
    print(json.dumps({k: v for k, v in report.items() if k != 'snapshot'}))


if __name__ == '__main__':
    main()
