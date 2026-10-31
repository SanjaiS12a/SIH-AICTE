import hashlib
import json
import csv
import io
from datetime import timedelta
from unittest.mock import patch

from django.db import connection, transaction, IntegrityError
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from cases.models import Complaint, CaseAction, Membership
from .test_workflow import WorkflowTests


class Phase2Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        WorkflowTests.setUpTestData.__func__(cls)

    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)
    payload = WorkflowTests.payload

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.coordinator)

    def act(self, **data):
        self.case.refresh_from_db()
        return self.client.post(f'/api/cases/{self.case.pk}/actions',
                                {'expected_version': self.case.version, 'reason': 'Official workflow correction', **data}, format='json')

    @patch('cases.serializers.CreateCaseSerializer.validate_summary', lambda self, value: value)
    def test_legacy_default_replay_and_explicit_classification(self):
        payload = self.payload()
        response = self.client.post('/api/cases', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['classification'], 'unclassified')
        legacy = Complaint.objects.get(pk=response.data['id'])
        original = {k: str(v) for k, v in payload.items()}
        original.update(bureau=str(self.rb.pk), source_system='manual')
        self.assertEqual(legacy.submission_fingerprint, hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest())
        payload['classification'] = 'unclassified'
        self.assertEqual(self.client.post('/api/cases', payload, format='json').status_code, 200)
        payload['classification'] = 'grievance'
        self.assertEqual(self.client.post('/api/cases', payload, format='json').status_code, 409)
        payload = self.payload()
        payload.update(source_reference='CLASS-NEW', classification='regulatory_compliance')
        response = self.client.post('/api/cases', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['classification'], 'regulatory_compliance')
        self.assertEqual(Complaint.objects.get(pk=response.data['id']).actions.get().changes['classification'], 'regulatory_compliance')

    @patch('cases.serializers.CreateCaseSerializer.validate_summary', lambda self, value: value)
    def test_invalid_registration_classification_is_atomic(self):
        payload = self.payload()
        payload['classification'] = 'regulatory'
        self.assertEqual(self.client.post('/api/cases', payload, format='json').status_code, 400)
        self.assertEqual(Complaint.objects.count(), 2)

    def test_coordinator_correction_reason_history_and_stale_version(self):
        self.assertEqual(self.act(kind='classification', classification='grievance', reason=' ').status_code, 400)
        response = self.act(kind='classification', classification='grievance')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['version'], 2)
        self.assertEqual(self.case.actions.get().changes, {'classification': {'before': 'unclassified', 'after': 'grievance'}})
        self.assertEqual(self.act(kind='classification', classification='regulatory_compliance', expected_version=1).status_code, 409)
        self.assertEqual(self.act(kind='classification', classification='grievance').status_code, 400)
        self.assertEqual(self.act(kind='classification', classification='invalid').status_code, 400)
        self.assertEqual(self.case.actions.count(), 1)

    def test_read_only_and_officer_classification_permissions(self):
        for user in [self.officer, self.other, self.auditor]:
            self.client.force_authenticate(user)
            response = self.act(kind='classification', classification='grievance')
            self.assertIn(response.status_code, [403, 404])
        self.assertFalse(self.case.actions.exists())

    def test_next_action_is_independent_and_versioned(self):
        due = self.case.due_at
        self.client.force_authenticate(self.officer)
        response = self.act(kind='next_action', next_action='Request inspection photographs', next_action_date='2026-11-09')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['next_action_date'], '2026-11-09')
        self.assertEqual(response.data['status'], 'registered')
        self.case.refresh_from_db()
        self.assertEqual(self.case.due_at, due)
        self.assertEqual(self.case.actions.get().changes['next_action_date'], {'before': None, 'after': '2026-11-09'})
        self.assertEqual(self.act(kind='next_action', next_action='Stale change', expected_version=1).status_code, 409)
        self.assertEqual(self.act(kind='next_action', next_action='Await documents').status_code, 200)
        self.case.refresh_from_db()
        self.assertIsNone(self.case.next_action_date)
        self.assertEqual(self.act(kind='next_action', next_action='').status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.next_action, '')

    def test_next_action_validation_and_current_membership(self):
        for payload in [{'next_action': '', 'next_action_date': '2026-11-09'}, {'next_action': 'x', 'next_action_date': 'bad'}, {'next_action': 'x' * 1001}, {}]:
            self.assertEqual(self.act(kind='next_action', **payload).status_code, 400)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.act(kind='next_action', next_action='Not allowed').status_code, 403)
        self.client.force_authenticate(self.officer)
        Membership.objects.filter(user=self.officer).update(bureau=self.pg)
        self.assertEqual(self.act(kind='next_action', next_action='Old bureau access').status_code, 404)
        self.assertFalse(self.case.actions.exists())

    def test_closure_clears_operational_fields_and_preserves_history(self):
        self.act(kind='next_action', next_action='Await principal reply', next_action_date='2026-11-10')
        due = self.case.due_at
        self.assertEqual(self.act(kind='status', status='disposed', reason='Reply accepted; case resolved').status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.next_action, '')
        self.assertIsNone(self.case.next_action_date)
        self.assertEqual(self.case.due_at, due)
        closed = self.case.actions.get(kind='status')
        self.assertEqual(closed.changes['next_action'], {'before': 'Await principal reply', 'after': ''})
        self.assertEqual(closed.changes['next_action_date'], {'before': '2026-11-10', 'after': None})
        self.assertEqual(self.act(kind='next_action', next_action='Closed case').status_code, 400)
        self.assertEqual(self.act(kind='status', status='under_review').status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.next_action, '')
        self.assertEqual(self.case.actions.get(kind='next_action').changes['next_action']['after'], 'Await principal reply')

    def test_classification_filters_statistics_and_exports_are_scoped(self):
        self.act(kind='classification', classification='grievance')
        Complaint.objects.filter(pk=self.hidden.pk).update(classification='regulatory_compliance')
        for user, total in [(self.coordinator, 2), (self.auditor, 2), (self.officer, 1)]:
            self.client.force_authenticate(user)
            data = self.client.get(f'/api/institutions/{self.institution.pk}?from=2099-01-01').data
            self.assertEqual(sum(row['count'] for row in data['classifications']), total)
            self.assertEqual(data['overview']['total'], total)
            for classification, count in [('grievance', 1), ('regulatory_compliance', total - 1), ('unclassified', 0)]:
                query = f'?classification={classification}'
                self.assertEqual(self.client.get('/api/cases' + query).data['count'], count)
                self.assertEqual(self.client.get('/api/dashboard' + query).data['total'], count)
                self.assertEqual(self.client.get(f'/api/institutions/{self.institution.pk}/cases' + query).data['count'], count)
        exported = b''.join(self.client.get('/api/reports.csv?classification=grievance').streaming_content).decode()
        self.assertIn('Classification', exported)
        self.assertNotIn(self.hidden.reference, [row[0] for row in list(csv.reader(io.StringIO(exported)))[1:]])
        self.assertEqual(self.client.get('/api/cases?classification=invalid').status_code, 400)

    def test_database_rejects_invalid_workflow_fields(self):
        for update in [{'classification': 'invalid'}, {'next_action_date': timezone.localdate()}, {'status': 'disposed', 'next_action': 'Pending work'}]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Complaint.objects.filter(pk=self.case.pk).update(**update)

    @patch('cases.matching.encoder', side_effect=RuntimeError('AI unavailable'))
    @patch('cases.api.async_task', side_effect=RuntimeError('AI queue unavailable'))
    def test_workflow_updates_do_not_depend_on_ai(self, queue, encoder):
        self.assertEqual(self.act(kind='classification', classification='grievance').status_code, 200)
        self.assertEqual(self.act(kind='next_action', next_action='Request a written response').status_code, 200)
        encoder.assert_not_called()
        queue.assert_not_called()

    def test_transfer_does_not_infer_classification_or_clear_next_action(self):
        self.act(kind='classification', classification='grievance')
        self.act(kind='next_action', next_action='Await response', next_action_date='2026-11-12')
        self.assertEqual(self.act(kind='transfer', bureau='PGRC').status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.classification, 'grievance')
        self.assertEqual(self.case.next_action, 'Await response')
        self.assertEqual(self.case.next_action_date.isoformat(), '2026-11-12')


class Phase2MigrationTests(TransactionTestCase):
    def test_legacy_cases_and_actions_survive_unclassified_backfill(self):
        old = [('cases', '0007_case_action_insert_timestamp')]
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes('cases')
        try:
            executor.migrate(old)
            apps = executor.loader.project_state(old).apps
            user = apps.get_model('auth', 'User').objects.create(username='legacy-phase2')
            institution = apps.get_model('cases', 'Institution').objects.create(name='Legacy', permanent_id='PHASE2-LEGACY', region='South', district='Test')
            bureau = apps.get_model('cases', 'Bureau').objects.create(code='RB', name='Legacy bureau')
            import uuid
            case = apps.get_model('cases', 'Complaint').objects.create(submission_id=uuid.uuid4(), reference='OLD-PHASE2', source_reference='OLD-PHASE2', institution=institution, bureau=bureau, created_by=user, category='refunds', summary='Original allegation', description='Preserved', status='disposed', received_at=timezone.now(), due_at=timezone.now() + timedelta(days=30))
            action = apps.get_model('cases', 'CaseAction').objects.create(case=case, actor=user, kind='note', reason='Original history', changes={'preserved': True})
            MigrationExecutor(connection).migrate(latest)
            saved = Complaint.objects.get(pk=case.pk)
            self.assertEqual((saved.classification, saved.next_action, saved.next_action_date), ('unclassified', '', None))
            self.assertEqual((saved.summary, saved.category, saved.status), ('Original allegation', 'refunds', 'disposed'))
            self.assertEqual(CaseAction.objects.get(pk=action.pk).changes, {'preserved': True})
        finally:
            MigrationExecutor(connection).migrate(latest)
