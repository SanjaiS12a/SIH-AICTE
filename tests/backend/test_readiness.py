"""Corrective readiness checks against isolated test records."""
from .test_milestone3_analytics import _Base
import uuid
import csv
import io
from datetime import timedelta
from django.db import connection, transaction, DatabaseError
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from cases.models import CaseAction, CoordinationRecord, CoordinationParticipant, ImportJob, ImportRow, Notification, Membership
from cases.tasks import send_reminders


class HomepageTests(_Base):
    def test_priority_and_totals_reconcile_with_filtered_cases(self):
        self._case(self.rb, overdue=True)
        self._case(self.pg, status='under_review')
        self._case(self.rb, institution=self.inst2, status='awaiting_response')
        self.client.force_authenticate(self.coord)
        dashboard = self.client.get('/api/dashboard?region=South').data
        for metric, query in [('total', ''), ('pending', '&pending=true'),
                              ('under_process', '&under_process=true'), ('disposed', '&closed=true')]:
            self.assertEqual(dashboard[metric], self.client.get('/api/cases?region=South' + query).data['count'])
        priority = dashboard['management']['priority_institutions']
        self.assertEqual(len(priority), 1)
        self.assertEqual(priority[0]['count'], 2)
        self.assertEqual(priority[0]['overdue'], 1)
        self.assertEqual(str(priority[0]['institution_id']), str(self.inst.pk))
        exported = b''.join(self.client.get('/api/reports.csv?region=South').streaming_content).decode()
        self.assertEqual(len(list(csv.reader(io.StringIO(exported))))-1, dashboard['total'])

    def test_officers_receive_no_management_payload(self):
        self._case(self.pg)
        self.client.force_authenticate(self.rb_officer)
        data = self.client.get('/api/dashboard').data
        self.assertEqual(data['total'], 0)
        self.assertNotIn('management', data)
        self.assertNotIn('coordination_institutions', data)


class AccountabilityTests(_Base):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.coord)
        self.case = self._case(self.rb)

    def record(self, institution=None):
        record = CoordinationRecord.objects.create(submission_id=uuid.uuid4(), submission_fingerprint='test',
            institution=institution or self.inst, lead_bureau=self.rb, lead_officer=self.rb_officer,
            reason='Verify shared responsibility', created_by=self.coord)
        record.cases.add(self.case)
        for bureau, officer in [(self.rb, self.rb_officer), (self.pg, self.pg_officer)]:
            CoordinationParticipant.objects.create(record=record, bureau=bureau, officer=officer, instruction='Check records')
        return record

    def test_pending_ack_counts_records_and_uses_all_time_geographic_scope(self):
        record = self.record()
        self.record(self.inst2)
        data = self.client.get('/api/dashboard?from=2000-01-01&to=2000-01-02&region=South').data
        self.assertEqual(data['total'], 0)
        self.assertEqual(data['management']['pending_acknowledgment_records'], 1)
        result = self.client.get('/api/coordination-records?awaiting_ack=true&region=South').data
        self.assertEqual(result['count'], 1)
        self.assertEqual(str(result['results'][0]['id']), str(record.pk))
        record.participants.update(acknowledged_at=timezone.now())
        self.assertEqual(self.client.get('/api/coordination-records?awaiting_ack=true&region=South').data['count'], 0)
        self.assertEqual(self.client.get('/api/coordination-records?awaiting_ack=nonsense').status_code, 400)

    def test_invalid_participant_assignments_are_flagged_without_officer_leakage(self):
        record = self.record()
        self.rb_officer.is_active = False
        self.rb_officer.save()
        Membership.objects.filter(user=self.pg_officer).update(bureau=self.rb)
        data = self.client.get(f'/api/coordination-records/{record.pk}').data
        self.assertEqual([p['assignment_current'] for p in data['participants']], [False, False])
        self.client.force_authenticate(self.pg_officer)
        self.assertEqual(self.client.get('/api/coordination-records?awaiting_ack=true').status_code, 403)

    def test_reminders_follow_current_deadline_status_and_membership(self):
        self.case.due_at = timezone.now() + timedelta(hours=12)
        self.case.save()
        send_reminders()
        self.assertEqual(self.client.get('/api/notifications').data['unread'], 1)
        self.case.due_at += timedelta(days=10)
        self.case.save()
        self.assertEqual(self.client.get('/api/notifications').data['unread'], 0)

    def test_reminder_generation_is_one_statement_and_returns_only_new_rows(self):
        now = timezone.now()
        self.case.due_at = now + timedelta(days=7)
        self.case.save()
        before = Notification.objects.count()
        with CaptureQueriesContext(connection) as queries:
            created = send_reminders(now)
        self.assertEqual(len(queries), 1)
        self.assertEqual(created, Notification.objects.count() - before)
        self.assertEqual(created, 2)
        self.assertEqual(send_reminders(now), 0)
        self.assertEqual(send_reminders(now+timedelta(days=6)), 2)
        self.assertFalse(Notification.objects.filter(user=self.pg_officer).exists())
        self.assertGreater(Notification.objects.count(), 0)
        self.case.due_at = timezone.now() - timedelta(seconds=1)
        self.case.save()
        send_reminders()
        self.client.force_authenticate(self.rb_officer)
        self.assertEqual(self.client.get('/api/notifications').data['unread'], 1)
        Membership.objects.filter(user=self.rb_officer).update(bureau=self.pg)
        self.assertEqual(self.client.get('/api/notifications').data['unread'], 0)
        self.case.status = 'disposed'
        self.case.save()
        self.client.force_authenticate(self.coord)
        self.assertEqual(self.client.get('/api/notifications').data['unread'], 0)

    def test_bureau_snapshot_is_database_enforced_and_transfer_uses_destination(self):
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO cases_caseaction (case_id,actor_id,kind,reason,changes,created_at,bureau_at_action_id) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id',
                [self.case.pk, self.coord.pk, 'note', 'SQL evidence', '{}', timezone.now(), self.pg.pk])
            action_id = cursor.fetchone()[0]
        action = CaseAction.objects.get(pk=action_id)
        self.assertEqual(action.bureau_at_action, self.rb)
        response = self.client.post(f'/api/cases/{self.case.pk}/actions',
            {'kind':'transfer', 'bureau':'PGRC', 'reason':'Route to responsible Bureau', 'expected_version':1}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.case.actions.get(kind='transfer').bureau_at_action, self.pg)
        self.assertEqual(CaseAction.objects.get(pk=action_id).bureau_at_action, self.rb)
        for mutate in [lambda: CaseAction.objects.filter(pk=action_id).update(reason='overwrite'),
                       lambda: CaseAction.objects.filter(pk=action_id).delete()]:
            with self.assertRaises(DatabaseError), transaction.atomic(): mutate()
        history = self.client.get(f'/api/cases/{self.case.pk}').data['actions']
        self.assertEqual([a['bureau_at_action'] for a in history], ['RB', 'PGRC'])
        csv = b''.join(self.client.get('/api/movements.csv').streaming_content).decode()
        self.assertIn('Bureau at action', csv.splitlines()[0])

    def test_source_history_pagination_conflicts_and_current_permissions(self):
        jobs = [ImportJob.objects.create(owner=self.coord, kind='complaints', filename=f'upload-{i}.csv',
            source_system='legacy-rb', source_bureau=self.rb) for i in range(25)]
        for number in [1, 2]: ImportRow.objects.create(job=jobs[0], number=number, state='conflict')
        first = self.client.get('/api/source-intake/jobs?source=legacy-rb').data
        second = self.client.get('/api/source-intake/jobs?source=legacy-rb&page=2').data
        self.assertEqual((first['count'], len(first['results']), len(second['results'])), (25,20,5))
        self.assertFalse({j['id'] for j in first['results']} & {j['id'] for j in second['results']})
        conflict = self.client.get('/api/source-intake/jobs?source=legacy-rb&conflicts=true').data
        self.assertEqual(conflict['count'], 1)
        self.assertEqual(conflict['results'][0]['unresolved_conflicts'], 2)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.client.get('/api/source-intake/jobs?bureau=RB').data['count'], 25)
        self.client.force_authenticate(self.rb_officer)
        self.assertEqual(self.client.get('/api/source-intake/jobs').data['count'], 0)


class HistoricalMigrationTests(TransactionTestCase):
    _user = classmethod(_Base._user.__func__)
    _case = classmethod(_Base._case.__func__)
    def test_existing_actions_remain_unknown_and_count_is_preserved(self):
        # Fixtures are created only in Django's isolated test database.
        _Base.setUpTestData.__func__(self.__class__)
        case = self._case(self.rb)
        CaseAction.objects.create(case=case, actor=self.coord, kind='note', reason='Legacy action')
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes('cases')
        old = [('cases', '0012_complaint_source_bureau_complaint_source_import_and_more')]
        new = [('cases', '0013_caseaction_bureau_at_action')]
        try:
            executor.migrate(old)
            executor = MigrationExecutor(connection)
            executor.migrate(new)
            self.assertEqual(CaseAction.objects.count(), 1)
            self.assertIsNone(CaseAction.objects.get().bureau_at_action)
        finally:
            MigrationExecutor(connection).migrate(latest)
