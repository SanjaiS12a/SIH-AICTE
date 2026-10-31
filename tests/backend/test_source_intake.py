import json
import uuid
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from cases.models import Complaint, ImportJob, ImportRow, CaseAction, Membership
from cases.imports import process_import
from .test_imports import ImportTests


class SourceIntakeTests(TestCase):
    setUpTestData = classmethod(ImportTests.setUpTestData.__func__)
    make_user = classmethod(ImportTests.make_user.__func__)
    make_case = classmethod(ImportTests.make_case.__func__)
    setUp = ImportTests.setUp
    csv = ImportTests.csv
    row = ImportTests.row
    finish = ImportTests.finish

    def upload(self, rows=None, bureau='RB', source='demo-rb', mapping=None):
        data = {'file': self.csv(rows or [self.row(status='Received')]), 'kind': 'complaints', 'source_system': source, 'source_bureau': bureau,
                'status_mapping': json.dumps(mapping if mapping is not None else {'Received': 'registered', 'In progress': 'under_review'})}
        with patch('cases.serializers.CreateCaseSerializer.validate_summary', lambda self, value: value):
            response = self.client.post('/api/imports', data, format='multipart')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_separate_sources_share_canonical_institution_and_retain_provenance(self):
        for bureau, source, status in [('RB','demo-rb','Received'), ('PGRC','demo-pgrc','In progress')]:
            job = self.upload([self.row(bureau=bureau, status=status)], bureau=bureau, source=source)
            self.finish(job)
        rows = Complaint.objects.filter(source_reference='IMPORT-1')
        self.assertEqual(rows.count(), 2)
        self.assertEqual(set(rows.values_list('institution_id', flat=True)), {self.institution.pk})
        rb = rows.get(source_system='demo-rb')
        self.assertEqual((rb.source_status, rb.source_bureau, rb.status), ('Received', self.rb, 'registered'))
        self.assertIsNotNone(rb.source_last_seen_at); self.assertIsNotNone(rb.source_import_id)
        self.assertEqual(self.client.get('/api/source-intake').data['count'], 2)
        self.assertEqual(len(self.client.get('/api/source-intake').data['results']), 2)

    def test_replay_updates_seen_time_only_after_confirmation_and_preserves_portal_actions(self):
        job = self.upload(); self.finish(job)
        case = Complaint.objects.get(source_system='demo-rb')
        seen = case.source_last_seen_at; case.status = 'under_review'; case.bureau = self.pg; case.save()
        repeat = self.upload()
        self.assertEqual(repeat['counts'], {'duplicate': 1})
        case.refresh_from_db(); self.assertEqual(case.source_last_seen_at, seen)
        self.finish(repeat); case.refresh_from_db()
        self.assertEqual((case.status, case.bureau, case.source_bureau), ('under_review', self.pg, self.rb))
        self.assertGreaterEqual(case.source_last_seen_at, seen)
        self.assertEqual(case.source_import_id, uuid.UUID(repeat['id']))
        self.assertEqual(case.actions.count(), 1)

    def test_changed_source_conflict_review_is_audited_not_an_overwrite(self):
        original = self.upload(); self.finish(original)
        success = self.client.get('/api/source-intake').data['results'][0]['last_success_at']
        changed = self.upload([self.row(status='In progress', summary='Changed incoming allegation.')])
        self.assertEqual(changed['counts'], {'conflict': 1})
        self.assertEqual(self.client.get(f'/api/imports/{changed["id"]}/report').data['total'], 0)
        self.finish(changed)
        source = self.client.get('/api/source-intake').data['results'][0]
        self.assertEqual(source['last_success_at'], success); self.assertEqual(source['unresolved_conflict_rows'], 1)
        row = self.client.get(f'/api/imports/{changed["id"]}/rows?state=conflict').data['results'][0]
        self.assertEqual(row['data']['source_status'], 'In progress'); self.assertEqual(row['current_case']['source_status'], 'Received')
        url = f'/api/imports/{changed["id"]}/rows/2/resolve'
        payload = {'expected_version': 1, 'expected_case_version': row['current_case']['version'], 'reason': 'Incoming source update disputed; portal evidence retained.', 'decision': 'keep_portal_record'}
        for _ in range(2): self.assertEqual(self.client.post(url, payload, format='json').status_code, 200)
        case = Complaint.objects.get(source_system='demo-rb')
        self.assertEqual((case.summary, case.status, case.source_status), ('Fee refund withheld.', 'registered', 'Received'))
        self.assertEqual(CaseAction.objects.filter(case=case, kind='source_conflict').count(), 1)
        self.assertEqual(self.client.post(url, {**payload, 'reason': 'Different decision'}, format='json').status_code, 409)
        self.assertEqual(self.client.get(f'/api/imports/{changed["id"]}/report').data['total'], 0)

    def test_scope_after_transfer_and_auditor_read_only(self):
        self.client.force_authenticate(self.officer); job = self.upload(); self.finish(job)
        self.assertEqual(self.client.get('/api/source-intake').data['count'], 1)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/source-intake').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/imports/{job["id"]}/rows').status_code, 404)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.client.get('/api/source-intake').data['count'], 1)
        self.assertEqual(self.client.post(f'/api/imports/{job["id"]}/rows/2/resolve', {}, format='json').status_code, 403)
        Complaint.objects.filter(source_system='demo-rb').update(bureau=self.pg)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get('/api/source-intake').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/imports/{job["id"]}/rows').status_code, 404)

    def test_source_row_identity_and_status_validation(self):
        job = self.upload([self.row(status='Unmapped', source_system=''), self.row(source_reference='X2', status='Received', institution_permanent_id='UNKNOWN'), self.row(source_reference='X3', status='Received', bureau='PGRC'), self.row(source_reference='X4', status='Received', source_system='other-source')])
        self.assertEqual(job['counts'], {'rejected': 4})
        self.assertFalse(Complaint.objects.filter(source_system='demo-rb').exists())
        for extra in [{'source_system': 'bad source'}, {'status_mapping': '{invalid'}, {'status_mapping': json.dumps({'X': 'automatic_duplicate'})}]:
            data = {'kind':'complaints', 'file':self.csv([self.row()]), 'source_system':'demo-rb', 'source_bureau':'RB', **extra}
            self.assertEqual(self.client.post('/api/imports', data, format='multipart').status_code, 400)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.post('/api/imports', {'kind':'complaints','file':self.csv([self.row()]), 'source_system':'demo-pgrc','source_bureau':'PGRC'}, format='multipart').status_code, 403)

    def test_stale_portal_version_rejected_and_rows_paginate_past_twenty(self):
        first = self.upload(); self.finish(first)
        changed = self.upload([self.row(status='In progress')]); self.finish(changed)
        case = Complaint.objects.get(source_system='demo-rb'); case.version += 1; case.save()
        self.assertEqual(self.client.post(f'/api/imports/{changed["id"]}/rows/2/resolve', {'expected_version':1,'expected_case_version':1,'reason':'Stale review','decision':'keep_portal_record'}, format='json').status_code, 409)
        job = self.upload([self.row(source_reference=f'PAGE-{n}', status='Received') for n in range(21)])
        data = self.client.get(f'/api/imports/{job["id"]}/rows?page=2').data
        self.assertEqual(data['count'], 21); self.assertEqual(len(data['results']), 1)

    def test_new_source_provenance_survives_both_csv_paths(self):
        import csv, io
        from cases.exports import build_export
        job = self.upload(); self.finish(job)
        response = self.client.get(f'/api/reports.csv?import_id={job["id"]}')
        rows = list(csv.DictReader(io.StringIO(b''.join(response.streaming_content).decode())))
        self.assertEqual((rows[0]['Source system'], rows[0]['Original source status']), ('demo-rb', 'Received'))
        exported = self.client.post('/api/exports', {'import_id':job['id']}, format='json').data
        build_export(exported['id'])
        response = self.client.get(f'/api/exports/{exported["id"]}/download')
        data = list(csv.DictReader(io.StringIO(b''.join(response.streaming_content).decode('utf-8-sig'))))
        self.assertEqual(rows, data)

    def test_source_provenance_does_not_add_per_pair_queries(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from cases.models import OverlapCandidate
        self.case.source_bureau = self.rb; self.case.save()
        for n in range(21):
            other = self.make_case(self.pg, f'SOURCE-QUERY-{n}')
            other.source_bureau = self.pg; other.save()
            left, right = sorted([self.case.pk, other.pk])
            OverlapCandidate.objects.create(left_id=left, right_id=right, score=.9, model_revision='query-fixture')
        with CaptureQueriesContext(connection) as queries:
            result = self.client.get('/api/overlaps')
        self.assertEqual(len(result.data['results']), 20)
        self.assertLessEqual(len(queries), 7)

    def test_queued_duplicate_cannot_update_provenance_after_transfer(self):
        self.client.force_authenticate(self.officer)
        first = self.upload(); self.finish(first)
        case = Complaint.objects.get(source_system='demo-rb'); seen = case.source_last_seen_at
        repeat = self.upload()
        self.assertEqual(self.client.post(f'/api/imports/{repeat["id"]}', {'action':'confirm'}, format='json').status_code, 200)
        Complaint.objects.filter(pk=case.pk).update(bureau=self.pg)
        with self.assertRaises(ValueError): process_import(repeat['id'])
        case.refresh_from_db()
        self.assertEqual(case.source_last_seen_at, seen)
        self.assertEqual(case.source_import_id, uuid.UUID(first['id']))
        self.assertEqual(ImportJob.objects.get(pk=repeat['id']).state, 'failed')

    def test_deactivated_import_owner_cannot_continue_queued_registration(self):
        self.client.force_authenticate(self.officer)
        job = self.upload()
        self.assertEqual(self.client.post(f'/api/imports/{job["id"]}', {'action':'confirm'}, format='json').status_code, 200)
        type(self.officer).objects.filter(pk=self.officer.pk).update(is_active=False)
        with self.assertRaises(ValueError): process_import(job['id'])
        self.assertFalse(Complaint.objects.filter(source_system='demo-rb').exists())
