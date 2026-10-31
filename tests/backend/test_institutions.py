from unittest.mock import patch
from tempfile import TemporaryDirectory

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from cases.models import AuditEvent, CaseAction, Complaint, Institution, Membership
from . import test_workflow as workflow


class InstitutionTests(TestCase):
    setUpTestData = classmethod(workflow.WorkflowTests.setUpTestData.__func__)
    make_user = classmethod(workflow.WorkflowTests.make_user.__func__)
    make_case = classmethod(workflow.WorkflowTests.make_case.__func__)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.coordinator)
        self.url = f'/api/institutions/{self.institution.pk}'

    def payload(self, **values):
        return {'name': 'New Fictional College', 'permanent_id': 'DEMO-NEW',
                'region': 'West', 'district': 'Fictional District',
                'official_email': 'office@example.org', 'official_phone': '+91 12345 67890',
                'address': 'Fictional campus', 'reason': 'Register official institution', **values}

    def test_create_and_duplicate_identity(self):
        result = self.client.post('/api/institution-registry', self.payload(), format='json')
        self.assertEqual(result.status_code, 201, result.data)
        self.assertEqual(result.data['version'], 1)
        event = AuditEvent.objects.get(kind='institution_created')
        self.assertEqual(event.detail['institution_id'], result.data['id'])
        self.assertEqual(event.actor, self.coordinator)
        self.assertIn(self.client.post('/api/institution-registry', self.payload(), format='json').status_code, (400, 409))
        self.assertEqual(Institution.objects.filter(permanent_id='DEMO-NEW').count(), 1)

    def test_invalid_contacts_and_unknown_fields_leave_no_records(self):
        for values in [{'official_email': 'invalid'}, {'official_phone': 'abc'}, {'version': 999}, {'permanent_id': ''}]:
            response = self.client.post('/api/institution-registry', self.payload(**values), format='json')
            self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Institution.objects.filter(permanent_id='DEMO-NEW').exists())
        self.assertFalse(AuditEvent.objects.exists())

    def test_edits_are_versioned_audited_and_stale_edits_conflict(self):
        form = {'name': 'Renamed College', 'expected_version': 1, 'reason': 'Correct registered name'}
        response = self.client.patch(self.url, form, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['version'], 2)
        event = AuditEvent.objects.get(kind='institution_updated')
        self.assertEqual(event.detail['changes']['name'], {'before': 'Fictional College', 'after': 'Renamed College'})
        self.assertEqual(self.client.patch(self.url, form, format='json').status_code, 409)
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_edits_require_reason_and_version_and_reject_identity_changes(self):
        for form in [{'name': 'Changed', 'reason': 'Correction'},
                     {'name': 'Changed', 'expected_version': 1},
                     {'permanent_id': 'DIFFERENT', 'expected_version': 1, 'reason': 'Correction'},
                     {'version': 99, 'expected_version': 1, 'reason': 'Correction'}]:
            self.assertEqual(self.client.patch(self.url, form, format='json').status_code, 400)
        self.institution.refresh_from_db()
        self.assertEqual(self.institution.version, 1)
        self.assertFalse(AuditEvent.objects.exists())

    def test_audit_failure_rolls_back_edit_and_creation(self):
        with patch('cases.institutions.AuditEvent.objects.create', side_effect=RuntimeError('audit unavailable')):
            with self.assertRaises(RuntimeError):
                self.client.patch(self.url, {'name': 'Failed', 'reason': 'Correction', 'expected_version': 1}, format='json')
            with self.assertRaises(RuntimeError):
                self.client.post('/api/institution-registry', self.payload(), format='json')
        self.institution.refresh_from_db()
        self.assertEqual(self.institution.name, 'Fictional College')
        self.assertEqual(self.institution.version, 1)
        self.assertFalse(Institution.objects.filter(permanent_id='DEMO-NEW').exists())

    def test_database_rejects_identity_updates_and_audit_mutations(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('UPDATE cases_institution SET permanent_id=%s WHERE id=%s', ['CHANGED', self.institution.pk])
        with self.assertRaises(IntegrityError), transaction.atomic():
            Institution.objects.create(name='Duplicate', permanent_id=self.institution.permanent_id, region='South', district='Test')
        action = CaseAction.objects.create(case=self.case, actor=self.coordinator, kind='note', reason='Original')
        event = AuditEvent.objects.create(actor=self.coordinator, kind='test')
        for model, pk in [(CaseAction, action.pk), (AuditEvent, event.pk)]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                model.objects.filter(pk=pk).update(**({'reason': 'Changed'} if model == CaseAction else {'kind': 'changed'}))
            with self.assertRaises(IntegrityError), transaction.atomic():
                model.objects.filter(pk=pk).delete()
        with self.assertRaises(ProtectedError):
            self.case.delete()

    def test_directory_search_pagination_and_case_filters(self):
        Institution.objects.bulk_create([Institution(name=f'College {i:02}', permanent_id=f'PAGE-{i}', region='West', district='Test') for i in range(25)])
        first = self.client.get('/api/institution-registry')
        second = self.client.get('/api/institution-registry?page=2')
        self.assertEqual(first.data['count'], 26)
        self.assertEqual(len(first.data['results']), 20)
        self.assertEqual(len(second.data['results']), 6)
        for query in ['DEMO-001', 'Fictional College']:
            result = self.client.get('/api/institution-registry', {'q': query})
            self.assertEqual(result.data['count'], 1)
        self.assertEqual(self.client.get('/api/institution-registry?region=West').data['count'], 25)
        self.assertEqual(self.client.get('/api/institution-registry?bureau=RB').data['count'], 1)
        self.assertEqual(self.client.get('/api/institution-registry?pending=false').data['count'], 26)
        self.assertEqual(self.client.get('/api/institution-registry?from=bad').status_code, 400)

    def test_district_directory_search_includes_institutions_without_cases(self):
        institution = Institution.objects.create(name='Coastal Registry College', permanent_id='DISTRICT-ONLY',
                                                 region='West', district='Coastal North')
        for user in [self.coordinator, self.auditor, self.officer]:
            self.client.force_authenticate(user)
            response = self.client.get('/api/institution-registry', {'district': 'coASTal'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['count'], 1)
            self.assertEqual(response.data['results'][0]['id'], str(institution.pk))
        self.assertEqual(self.client.get('/api/institution-registry?district=missing').data['count'], 0)
        self.assertEqual(self.client.get('/api/institution-registry', {'district': 'x' * 81}).status_code, 400)
        lookup = self.client.get('/api/institutions?q=DISTRICT-ONLY').data
        self.assertIsInstance(lookup, list)
        self.assertEqual(set(lookup[0]), {'id', 'name', 'permanent_id', 'region', 'district'})

    def test_district_case_counts_exports_and_current_membership_share_scope(self):
        other = Institution.objects.create(name='Other District College', permanent_id='DISTRICT-OTHER',
                                           region='West', district='Other District')
        self.hidden.institution = other
        self.hidden.save()
        self.assertEqual(self.client.get('/api/cases?district=fictional').data['count'], 1)
        self.assertEqual(self.client.get('/api/dashboard?district=fictional').data['total'], 1)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get('/api/cases?district=other').data['count'], 0)
        self.assertEqual(self.client.get('/api/dashboard?district=other').data['total'], 0)
        self.assertEqual(self.client.get('/api/institution-registry?district=other&bureau=PGRC').data['count'], 0)
        exported = b''.join(self.client.get('/api/reports.csv?district=other').streaming_content).decode()
        self.assertNotIn(other.name, exported)
        Membership.objects.filter(user=self.officer).update(bureau=self.pg)
        result = self.client.get('/api/cases?district=other').data
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['results'][0]['id'], str(self.hidden.pk))

    def test_profile_and_case_pages_include_closed_and_more_than_twenty_cases(self):
        for i in range(23):
            self.make_case(self.rb, f'PAGE-{i}')
        self.hidden.status = 'disposed'
        self.hidden.save()
        profile = self.client.get(self.url + '?from=2099-01-01').data
        self.assertEqual(profile['overview'], {'total': 25, 'open': 24, 'closed': 1, 'overdue': 24})
        self.assertEqual(profile['scope'], 'all_bureaus')
        self.assertEqual(profile['history_period'], 'all_time')
        one = self.client.get(profile['cases_url']).data
        two = self.client.get(profile['cases_url'] + '?page=2').data
        self.assertEqual(one['count'], 25)
        self.assertEqual(len(one['results']) + len(two['results']), 25)
        self.assertEqual(self.client.get(profile['cases_url'] + '?status=disposed').data['count'], 1)

    def test_history_paginates_authoritative_actions_with_case_references(self):
        actions = [CaseAction(case=self.case if i % 2 else self.hidden, actor=self.coordinator, kind='note', reason=f'Action {i}') for i in range(27)]
        CaseAction.objects.bulk_create(actions)
        first = self.client.get(self.url + '/history').data
        second = self.client.get(self.url + '/history?page=2').data
        self.assertEqual(first['count'], 27)
        ids = [row['id'] for row in first['results'] + second['results']]
        self.assertEqual(len(set(ids)), 27)
        self.assertEqual(ids, sorted(ids, reverse=True))
        self.assertEqual(first['results'][0]['reference'], self.hidden.reference)

    def test_officer_counts_pagination_history_and_filters_never_include_other_bureau(self):
        secret = Institution.objects.create(name='Registry-only institution', permanent_id='SECRET', region='North', district='Test')
        Complaint.objects.filter(pk=self.hidden.pk).update(institution=secret)
        CaseAction.objects.create(case=self.case, actor=self.coordinator, kind='note', reason='Visible')
        CaseAction.objects.create(case=self.hidden, actor=self.coordinator, kind='note', reason='Hidden')
        self.client.force_authenticate(self.officer)
        profile = self.client.get(self.url).data
        self.assertEqual(profile['scope'], 'current_bureau')
        self.assertEqual(profile['overview']['total'], 1)
        self.assertEqual([row['bureau__code'] for row in profile['bureaus']], ['RB'])
        self.assertEqual(self.client.get(self.url + '/cases').data['count'], 1)
        history = self.client.get(self.url + '/history').data
        self.assertEqual(history['count'], 1)
        self.assertNotIn('Hidden', str(history))
        self.assertEqual(self.client.get('/api/institution-registry?bureau=PGRC').data['count'], 0)
        # Canonical metadata is shared; existence of restricted cases is not.
        self.assertEqual(self.client.get(f'/api/institutions/{secret.pk}').data['overview']['total'], 0)

    def test_current_membership_and_ownership_are_rechecked_without_relogin(self):
        self.client.force_authenticate(self.officer)
        _ = self.officer.membership  # Deliberately populate Django's relation cache.
        Membership.objects.filter(user=self.officer).update(bureau=self.pg)
        rows = self.client.get(self.url + '/cases').data['results']
        self.assertEqual([row['id'] for row in rows], [str(self.hidden.pk)])
        Complaint.objects.filter(pk=self.hidden.pk).update(bureau=self.rb)
        self.assertEqual(self.client.get(self.url).data['overview']['total'], 0)
        Membership.objects.filter(user=self.officer).update(bureau=None)
        self.assertEqual(self.client.get(self.url + '/cases').data['count'], 0)
        Membership.objects.filter(user=self.officer).update(role='')
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_roles_and_anonymous_access(self):
        for user in [self.auditor, self.officer]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url).status_code, 200)
            self.assertEqual(self.client.post('/api/institution-registry', self.payload(), format='json').status_code, 403)
            self.assertEqual(self.client.patch(self.url, {'name': 'Changed', 'reason': 'Correction', 'expected_version': 1}, format='json').status_code, 403)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.client.get(self.url).data['overview']['total'], 2)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/institution-registry').status_code, 403)
        self.assertEqual(self.client.get(self.url + '/history').status_code, 403)

    def test_new_mutations_require_csrf_with_session_authentication(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.coordinator)
        self.assertEqual(client.post('/api/institution-registry', self.payload(), format='json').status_code, 403)
        self.assertEqual(client.patch(self.url, {'name': 'Changed', 'expected_version': 1, 'reason': 'Correction'}, format='json').status_code, 403)

    def test_relationship_history_is_redacted_for_officers_on_both_paths(self):
        CaseAction.objects.create(case=self.case, actor=self.coordinator, kind='overlap_review',
                                  reason='Restricted PGRC case details', changes={'overlap_id': 123, 'decision': 'related_issue'})
        self.client.force_authenticate(self.officer)
        for url in [self.url + '/history', f'/api/cases/{self.case.pk}']:
            result = self.client.get(url).data
            self.assertNotIn('Restricted PGRC', str(result))
            self.assertNotIn('overlap_id', str(result))
        self.client.force_authenticate(self.auditor)
        self.assertIn('Restricted PGRC', str(self.client.get(self.url + '/history').data))

    def test_lookup_contract_is_unchanged(self):
        result = self.client.get('/api/institutions?q=DEMO-001').data
        self.assertIsInstance(result, list)
        self.assertEqual(set(result[0]), {'id', 'name', 'permanent_id', 'region', 'district'})

    def test_admin_identity_protection_auditing_and_stale_edit(self):
        superuser = User.objects.create_superuser('institution-admin', 'admin@example.org', 'test-password-123')
        self.client.force_authenticate(None)
        self.client.force_login(superuser)
        url = f'/admin/cases/institution/{self.institution.pk}/change/'
        self.assertIn('permanent_id', admin.site._registry[Institution].get_readonly_fields(None, self.institution))
        form = {'name': 'Admin correction', 'region': 'South', 'district': 'Fictional', 'address': '',
                'official_email': '', 'official_phone': '', 'version': 1, 'reason': 'Official correction', '_save': 'Save'}
        response = self.client.post(url, form)
        self.assertEqual(response.status_code, 302)
        self.institution.refresh_from_db()
        self.assertEqual(self.institution.version, 2)
        self.assertEqual(self.institution.permanent_id, 'DEMO-001')
        self.assertEqual(AuditEvent.objects.get(kind='institution_updated').actor, superuser)
        response = self.client.post(url, form)
        self.assertContains(response, 'Institution changed. Reload before saving.')
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_fresh_seed_and_repeat_work_with_append_only_actions(self):
        with TemporaryDirectory() as directory, patch('cases.management.commands.seed_demo.Path') as path:
            from pathlib import Path
            path.return_value = Path(directory)
            call_command('seed_demo', verbosity=0)
            count = CaseAction.objects.count()
            call_command('seed_demo', verbosity=0)
        self.assertEqual(CaseAction.objects.count(), count)
        self.assertEqual(Complaint.objects.filter(source_system='synthetic').count(), 500)


class InstitutionMigrationTests(TransactionTestCase):
    def test_existing_institution_survives_forward_and_reverse_migrations(self):
        old = [('cases', '0004_dashboard_cache')]
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes('cases')
        try:
            executor.migrate(old)
            LegacyInstitution = executor.loader.project_state(old).apps.get_model('cases', 'Institution')
            institution = LegacyInstitution.objects.create(name='Before migration', permanent_id='LEGACY', region='South', district='Test')
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            saved = Institution.objects.get(pk=institution.pk)
            self.assertEqual(saved.name, 'Before migration')
            self.assertEqual(saved.version, 1)
            self.assertEqual(saved.official_email, '')
            executor = MigrationExecutor(connection)
            executor.migrate(old)
            self.assertTrue(LegacyInstitution.objects.filter(pk=institution.pk, permanent_id='LEGACY').exists())
        finally:
            MigrationExecutor(connection).migrate(latest)
