import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.db import IntegrityError, transaction, connections, close_old_connections
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django_q.models import OrmQ
from rest_framework.test import APIClient

from cases.models import Escalation, Notification, Membership, CaseAction
from cases.tasks import notify_escalation
from .test_workflow import WorkflowTests


class EscalationTests(TestCase):
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)

    @classmethod
    def setUpTestData(cls):
        WorkflowTests.setUpTestData.__func__(cls)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.coordinator)

    def create(self, case=None, **data):
        case = case or self.case
        case.refresh_from_db()
        return self.client.post(f'/api/cases/{case.pk}/escalations',
            {'submission_id': str(uuid.uuid4()), 'expected_version': case.version, 'reason': 'Supervisory review required', **data}, format='json')

    def resolve(self, escalation, **data):
        return self.client.post(f'/api/escalations/{escalation.pk}/resolve',
            {'expected_version': 1, 'reason': 'Supervisory guidance recorded', **data}, format='json')

    def test_creation_replay_conflicts_and_atomic_history(self):
        request_id = str(uuid.uuid4())
        due, status = self.case.due_at, self.case.status
        response = self.create(submission_id=request_id)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data['case']['has_unresolved_escalation'])
        self.assertEqual(self.create(submission_id=request_id, expected_version=1).status_code, 200)
        self.assertEqual(self.create(submission_id=request_id, reason='Different reason').status_code, 409)
        self.assertEqual(self.create().status_code, 409)
        self.case.refresh_from_db()
        self.assertEqual((self.case.version, self.case.due_at, self.case.status, self.case.next_action), (2, due, status, ''))
        self.assertEqual(Escalation.objects.count(), 1)
        self.assertEqual(self.case.actions.get().kind, 'escalation_created')
        self.assertEqual(OrmQ.objects.count(), 1)

    def test_current_bureau_permissions_and_read_only_auditor(self):
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.create().status_code, 201)
        escalation = Escalation.objects.get()
        self.assertEqual(self.create(self.hidden).status_code, 404)
        self.assertEqual(self.resolve(escalation).status_code, 403)
        self.assertEqual(self.client.get('/api/escalations').status_code, 403)
        Membership.objects.filter(user=self.officer).update(bureau=self.pg)
        self.assertEqual(self.client.get(f'/api/cases/{self.case.pk}/escalations').status_code, 404)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.create().status_code, 403)
        self.assertEqual(self.resolve(escalation).status_code, 403)
        self.assertEqual(self.client.get('/api/escalations').data['count'], 1)
        self.assertEqual(self.client.get(f'/api/cases/{self.case.pk}/escalations').data['count'], 1)

    def test_closed_case_reason_and_stale_creation_validation(self):
        for fields in [{'reason': ''}, {'reason': '  '}, {'reason': 'x' * 4001}, {'submission_id': 'invalid'}, {'expected_version': 999}]:
            response = self.create(**fields)
            self.assertIn(response.status_code, [400, 409])
        self.case.status = 'disposed'
        self.case.save()
        self.assertEqual(self.create().status_code, 400)
        self.assertFalse(Escalation.objects.exists())
        self.assertFalse(self.case.actions.exists())

    def test_resolution_is_reasoned_versioned_and_retry_safe(self):
        request_id = str(uuid.uuid4())
        self.create(submission_id=request_id)
        escalation = Escalation.objects.get()
        self.assertEqual(self.resolve(escalation, reason=' ').status_code, 400)
        self.assertEqual(self.resolve(escalation, expected_version=999).status_code, 409)
        self.assertEqual(self.resolve(escalation).status_code, 200)
        escalation.refresh_from_db()
        self.assertEqual((escalation.status, escalation.version, escalation.resolved_by_id), ('resolved', 2, self.coordinator.pk))
        self.assertIsNotNone(escalation.resolved_at)
        self.assertEqual(self.resolve(escalation).status_code, 200)
        self.assertEqual(self.resolve(escalation, reason='Change an existing decision').status_code, 409)
        self.assertEqual(self.case.actions.filter(kind='escalation_resolved').count(), 1)
        self.assertEqual(self.create(submission_id=request_id, expected_version=1).status_code, 200)
        self.assertEqual(Escalation.objects.count(), 1)
        self.assertEqual(self.create().status_code, 201)
        self.assertEqual(Escalation.objects.filter(status='pending').count(), 1)

    def test_transfer_closure_and_resolution_do_not_change_other_workflows(self):
        self.case.classification = 'grievance'
        self.case.next_action = 'Await written reply'
        self.case.save()
        self.create()
        escalation = Escalation.objects.get()
        due = self.case.due_at
        for action in [{'kind': 'transfer', 'bureau': 'PGRC'}, {'kind': 'status', 'status': 'disposed'}]:
            self.case.refresh_from_db()
            response = self.client.post(f'/api/cases/{self.case.pk}/actions', {'expected_version': self.case.version, 'reason': 'Independent official decision', **action}, format='json')
            self.assertEqual(response.status_code, 200)
            escalation.refresh_from_db()
            self.assertEqual(escalation.status, 'pending')
        self.case.refresh_from_db()
        self.assertEqual(self.case.due_at, due)
        self.assertEqual(self.case.classification, 'grievance')
        self.assertEqual(self.case.next_action, '')
        self.assertTrue(self.client.get(f'/api/cases/{self.case.pk}').data['has_unresolved_escalation'])
        self.assertEqual(self.resolve(escalation).status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual((self.case.status, self.case.bureau_id, self.case.due_at, self.case.next_action), ('disposed', self.pg.pk, due, ''))
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get(f'/api/cases/{self.case.pk}/escalations').status_code, 404)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'/api/cases/{self.case.pk}/escalations').data['count'], 1)

    def test_notifications_are_event_specific_and_permission_checked(self):
        active = self.make_user('extra-coordinator', 'coordinator')
        inactive = self.make_user('inactive-coordinator', 'coordinator')
        inactive.is_active = False
        inactive.save()
        self.create()
        escalation = Escalation.objects.get()
        self.assertEqual(notify_escalation(escalation.pk), 2)
        self.assertEqual(notify_escalation(escalation.pk), 0)
        self.assertEqual(Notification.objects.filter(escalation=escalation).count(), 2)
        self.assertFalse(Notification.objects.filter(user=inactive).exists())
        response = self.client.get('/api/notifications').data
        self.assertEqual(response['unread'], 1)
        self.assertEqual(str(response['results'][0]['escalation_id']), str(escalation.pk))
        self.assertIsNone(response['results'][0]['deadline'])
        Membership.objects.filter(user=self.coordinator).update(role='officer', bureau=self.rb)
        self.assertEqual(self.client.get('/api/notifications').data['unread'], 0)
        self.assertEqual(self.client.get('/api/notifications').data['results'], [])
        self.client.post('/api/notifications', {}, format='json')
        self.assertFalse(Notification.objects.get(user=self.coordinator).read)
        active.is_active = False
        active.save()
        self.client.force_authenticate(active)
        self.assertEqual(self.client.get('/api/notifications').data['unread'], 0)

    def test_failed_delivery_rolls_back_and_can_be_retried(self):
        self.make_user('second-coordinator', 'coordinator')
        self.create()
        escalation = Escalation.objects.get()
        original = Notification.objects.get_or_create
        calls = 0
        def interrupted(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError('Delivery interrupted')
            return original(*args, **kwargs)
        with patch('cases.tasks.Notification.objects.get_or_create', side_effect=interrupted), self.assertRaises(RuntimeError):
            notify_escalation(escalation.pk)
        self.assertFalse(Notification.objects.exists())
        self.assertEqual(notify_escalation(escalation.pk), 2)
        self.assertEqual(notify_escalation(escalation.pk), 0)

    def test_audit_or_queue_failure_rolls_back_creation(self):
        for target in ['cases.escalations.CaseAction.objects.create', 'cases.escalations.async_task']:
            with patch(target, side_effect=RuntimeError('Transaction failure')), self.assertRaises(RuntimeError):
                self.create()
            self.assertFalse(Escalation.objects.exists())
            self.assertFalse(self.case.actions.exists())
            self.assertFalse(OrmQ.objects.exists())
            self.case.refresh_from_db()
            self.assertEqual(self.case.version, 1)

    def test_resolution_audit_failure_rolls_back(self):
        self.create()
        escalation = Escalation.objects.get()
        with patch('cases.escalations.CaseAction.objects.create', side_effect=RuntimeError('Audit failure')), self.assertRaises(RuntimeError):
            self.resolve(escalation)
        escalation.refresh_from_db()
        self.case.refresh_from_db()
        self.assertEqual((escalation.status, escalation.version, self.case.version), ('pending', 1, 2))
        self.assertEqual(self.case.actions.count(), 1)

    def test_constraints_protection_and_submission_scope(self):
        request_id = str(uuid.uuid4())
        self.create(submission_id=request_id)
        escalation = Escalation.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Escalation.objects.create(case=self.case, submission_id=uuid.uuid4(), created_by=self.coordinator, reason='Duplicate pending request')
        with self.assertRaises(ProtectedError):
            self.case.delete()
        with self.assertRaises(ProtectedError):
            self.coordinator.delete()
        self.assertEqual(self.create(self.hidden, submission_id=request_id).status_code, 403)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.create(submission_id=request_id).status_code, 403)
        self.client.force_authenticate(self.coordinator)
        self.assertEqual(self.client.get('/api/escalations?state=bad').status_code, 400)
        self.assertEqual(self.client.get('/api/escalations?institution=bad').status_code, 400)
        notify_escalation(escalation.pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Notification.objects.create(user=self.coordinator, case=self.case, escalation=escalation, kind='escalation')

    def test_scoped_counts_filters_and_history_pagination(self):
        for i in range(21):
            self.create(reason=f'Review cycle {i}')
            self.resolve(Escalation.objects.get(case=self.case, status='pending'))
        self.create(self.hidden)
        result = self.client.get(f'/api/cases/{self.case.pk}/escalations?page=2').data
        self.assertEqual((result['count'], len(result['results'])), (21, 1))
        self.assertEqual(self.client.get('/api/escalations?state=resolved&page=2').data['count'], 21)
        self.assertEqual(self.client.get('/api/cases?escalated=true').data['count'], 1)
        self.assertEqual(self.client.get(f'/api/institutions/{self.institution.pk}').data['overview']['unresolved_escalations'], 1)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get('/api/cases?escalated=true').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/institutions/{self.institution.pk}').data['overview']['unresolved_escalations'], 0)

    @patch('cases.matching.encoder', side_effect=RuntimeError('AI unavailable'))
    def test_manual_escalation_does_not_use_ai(self, encoder):
        self.assertEqual(self.create().status_code, 201)
        self.assertEqual(self.resolve(Escalation.objects.get()).status_code, 200)
        encoder.assert_not_called()


class EscalationConcurrencyTests(TransactionTestCase):
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)

    def setUp(self):
        WorkflowTests.setUpTestData.__func__(type(self))

    def race(self, url, payloads):
        barrier = Barrier(2)
        def run(payload):
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(User.objects.get(pk=self.coordinator.pk))
                barrier.wait(timeout=10)
                return client.post(url, payload, format='json').status_code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, payloads))

    def test_parallel_distinct_requests_create_one_pending_request(self):
        payloads = [{'submission_id': str(uuid.uuid4()), 'expected_version': 1, 'reason': 'Concurrent review'} for _ in range(2)]
        self.assertEqual(sorted(self.race(f'/api/cases/{self.case.pk}/escalations', payloads)), [201, 409])
        self.assertEqual((Escalation.objects.count(), CaseAction.objects.count(), OrmQ.objects.count()), (1, 1, 1))

    def test_parallel_replay_and_resolution_are_idempotent(self):
        payload = {'submission_id': str(uuid.uuid4()), 'expected_version': 1, 'reason': 'Same retried request'}
        self.assertEqual(sorted(self.race(f'/api/cases/{self.case.pk}/escalations', [payload, payload])), [200, 201])
        escalation = Escalation.objects.get()
        resolution = {'expected_version': 1, 'reason': 'Same retried resolution'}
        self.assertEqual(self.race(f'/api/escalations/{escalation.pk}/resolve', [resolution, resolution]), [200, 200])
        self.assertEqual(CaseAction.objects.filter(kind='escalation_resolved').count(), 1)
