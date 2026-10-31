import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.test import TestCase, TransactionTestCase
from django.db import close_old_connections, connections
from rest_framework.test import APIClient
from cases.models import CoordinationRecord, CoordinationParticipant, CaseAction, Membership
from .test_workflow import WorkflowTests


class CoordinationWorkflowTests(TestCase):
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)
    @classmethod
    def setUpTestData(cls): WorkflowTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client = APIClient(); self.client.force_authenticate(self.coordinator)
    def payload(self):
        return {'submission_id': str(uuid.uuid4()), 'institution': str(self.institution.pk),
            'cases': [str(self.case.pk), str(self.hidden.pk)], 'reason': 'Private cross-Bureau coordination evidence',
            'lead_bureau': 'RB', 'lead_officer': self.officer.pk,
            'participants': [{'bureau': 'RB', 'officer': self.officer.pk, 'instruction': 'Obtain the approval records.'},
                             {'bureau': 'PGRC', 'officer': self.other.pk, 'instruction': 'Confirm the refund payment.'}]}
    def open(self):
        r = self.client.post('/api/coordination-records', self.payload(), format='json')
        self.assertEqual(r.status_code, 201, r.data)
        return r.data
    def action(self, record, user, action, version, **extra):
        self.client.force_authenticate(user)
        return self.client.post(f'/api/coordination-records/{record["id"]}/actions', {'action': action, 'expected_version': version, **extra}, format='json')
    def test_complete_journey_without_ai_and_audited_on_both_cases(self):
        with patch('cases.matching.encoder', side_effect=RuntimeError('Model unavailable')):
            record = self.open()
            self.assertEqual(self.action(record, self.coordinator, 'close', 1, note='Too early').status_code, 400)
            self.assertEqual(self.action(record, self.officer, 'complete', 1, note='Not acknowledged').status_code, 400)
            for user, version in [(self.officer, 1), (self.other, 3)]:
                self.assertEqual(self.action(record, user, 'acknowledge', version).status_code, 200)
                self.assertEqual(self.action(record, user, 'complete', version + 1, note='Evidence checked and agreed action completed.').status_code, 200)
            self.assertEqual(self.action(record, self.coordinator, 'close', 5, note='Both Bureaus completed their agreed responsibilities.').status_code, 200)
        obj = CoordinationRecord.objects.get(); self.assertEqual(obj.state, 'closed')
        self.assertEqual(CaseAction.objects.filter(case=self.case).count(), 6)
        self.assertEqual(CaseAction.objects.filter(case=self.hidden).count(), 6)
        self.case.refresh_from_db(); self.assertEqual(self.case.status, 'registered')
        self.assertEqual(self.case.bureau, self.rb)
        self.assertEqual(self.client.get(f'/api/coordination-records/{obj.pk}/history').data['count'], 12)
    def test_idempotence_conflicts_and_rollback(self):
        payload = self.payload()
        first = self.client.post('/api/coordination-records', payload, format='json')
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(self.client.post('/api/coordination-records', payload, format='json').status_code, 200)
        self.assertEqual(CaseAction.objects.count(), 2)
        payload['reason'] = 'Different'; self.assertEqual(self.client.post('/api/coordination-records', payload, format='json').status_code, 409)
        record = first.data
        self.assertEqual(self.action(record, self.officer, 'acknowledge', 1).status_code, 200)
        self.assertEqual(self.action(record, self.other, 'acknowledge', 1).status_code, 409)
        self.assertEqual(CaseAction.objects.count(), 4)
        self.client.force_authenticate(self.coordinator)
        with patch('cases.coordination_workflow.audit', side_effect=RuntimeError('History unavailable')), self.assertRaises(RuntimeError): self.open()
        self.assertEqual(CoordinationRecord.objects.count(), 1)
    def test_scope_and_current_membership_without_other_bureau_evidence(self):
        record = self.open()
        for user in [self.officer, self.other]:
            self.client.force_authenticate(user)
            for url in ['/api/coordination-records', f'/api/coordination-records/{record["id"]}', f'/api/coordination-records/{record["id"]}/history']:
                self.assertEqual(self.client.get(url).status_code, 403)
            inbox = self.client.get('/api/coordination-requests').data
            self.assertEqual(inbox['count'], 1)
            self.assertNotIn('Private cross-Bureau', str(inbox)); self.assertNotIn('institution', str(inbox)); self.assertNotIn('cases', str(inbox))
        Membership.objects.filter(user=self.officer).update(bureau=self.pg)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get('/api/coordination-requests').data['count'], 0)
        self.assertEqual(self.action(record, self.officer, 'acknowledge', 1).status_code, 404)
        self.client.force_authenticate(self.other)
        history = self.client.get(f'/api/cases/{self.hidden.pk}').data['actions']
        self.assertNotIn('Private cross-Bureau', str(history)); self.assertNotIn('coordination_id', str(history))
    def test_auditor_is_read_only_and_validation_is_atomic(self):
        record = self.open()
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.client.get('/api/coordination-records').data['count'], 1)
        self.assertEqual(self.client.get(f'/api/coordination-records/{record["id"]}').status_code, 200)
        self.assertEqual(self.client.post('/api/coordination-records', self.payload(), format='json').status_code, 403)
        self.assertEqual(self.action(record, self.auditor, 'acknowledge', 1).status_code, 403)
        self.assertEqual(self.action(record, self.auditor, 'close', 1, note='Attempt').status_code, 403)
        self.client.force_authenticate(self.coordinator)
        for field, value in [('cases', [str(uuid.uuid4())]), ('lead_officer', self.other.pk), ('reason', ' ')]:
            payload = self.payload(); payload[field] = value
            self.assertEqual(self.client.post('/api/coordination-records', payload, format='json').status_code, 400)
        payload = self.payload(); payload['participants'][1]['bureau'] = 'RB'
        self.assertEqual(self.client.post('/api/coordination-records', payload, format='json').status_code, 400)
        self.assertEqual(CoordinationRecord.objects.count(), 1)
    def test_server_pagination_and_one_case_shared_work(self):
        for _ in range(21):
            payload = self.payload(); payload['cases'] = [str(self.case.pk)]
            self.assertEqual(self.client.post('/api/coordination-records', payload, format='json').status_code, 201)
        data = self.client.get('/api/coordination-records?page=2').data
        self.assertEqual(data['count'], 21); self.assertTrue(data['results'])
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get('/api/coordination-requests?page=2').data['count'], 21)

    def test_revision_reassigns_current_officer_and_requires_new_acknowledgment(self):
        record = self.open()
        self.assertEqual(self.action(record, self.officer, 'acknowledge', 1).status_code, 200)
        replacement = self.make_user('replacement', 'officer', self.rb)
        participant = CoordinationParticipant.objects.get(record_id=record['id'], bureau=self.rb)
        self.assertEqual(self.action(record, self.coordinator, 'revise', 2, participant=participant.pk,
            officer=replacement.pk, instruction='Obtain revised regulatory evidence.', note='Officer reassigned by coordinator.').status_code, 200)
        participant.refresh_from_db(); self.assertIsNone(participant.acknowledged_at)
        self.assertEqual(CoordinationRecord.objects.get().lead_officer, replacement)
        self.assertEqual(self.action(record, self.officer, 'acknowledge', 3).status_code, 404)
        self.assertEqual(self.action(record, replacement, 'complete', 3, note='Too early').status_code, 400)
        self.assertEqual(self.action(record, replacement, 'acknowledge', 3).status_code, 200)


class CoordinationConcurrencyTests(TransactionTestCase):
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)
    def setUp(self): WorkflowTests.setUpTestData.__func__(type(self))
    def test_parallel_acknowledgments_cannot_silently_overwrite_version(self):
        client = APIClient(); client.force_authenticate(self.coordinator)
        response = client.post('/api/coordination-records', CoordinationWorkflowTests.payload(self), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        record = response.data
        barrier = Barrier(2)
        def run(user):
            close_old_connections()
            try:
                actor = APIClient(); actor.force_authenticate(user)
                barrier.wait(timeout=10)
                return actor.post(f'/api/coordination-records/{record["id"]}/actions', {'expected_version': 1, 'action': 'acknowledge'}, format='json').status_code
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(run, [self.officer, self.other])), [200, 409])
        self.assertEqual(CoordinationParticipant.objects.filter(acknowledged_at__isnull=False).count(), 1)
        self.assertEqual(CaseAction.objects.filter(kind='coordination_acknowledge').count(), 2)
