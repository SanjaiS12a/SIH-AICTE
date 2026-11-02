import json
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from cases.models import Complaint, CaseAction, ImportJob
from .test_source_intake import SourceIntakeTests


class OperationalTests(TestCase):
    setUpTestData=classmethod(SourceIntakeTests.setUpTestData.__func__)
    make_user=classmethod(SourceIntakeTests.make_user.__func__)
    make_case=classmethod(SourceIntakeTests.make_case.__func__)
    setUp=SourceIntakeTests.setUp
    csv=SourceIntakeTests.csv
    row=SourceIntakeTests.row
    finish=SourceIntakeTests.finish
    upload=SourceIntakeTests.upload

    def changed(self,**fields):
        original=self.upload();self.finish(original)
        case=Complaint.objects.get(source_system='demo-rb')
        job=self.upload([self.row(status='In progress',**fields)]);self.finish(job)
        return case,job,f"/api/imports/{job['id']}/rows/2/resolve"

    def approval(self,case,fields=None,**extra):
        return {'decision':'apply_selected_updates','fields':fields or ['status'],'expected_version':1,'expected_case_version':case.version,
                'reason':'Reviewed the source evidence and authorize only selected updates.','retain_unselected':True,**extra}

    def test_missing_category_and_explicit_mapping_are_not_ai_predictions(self):
        for category in ['',None]:
            data=self.row(source_reference='MISSING-'+str(category))
            if category is None:data.pop('category')
            else:data['category']=category
            with patch('cases.serializers.CreateCaseSerializer.validate_summary',lambda self,value:value):
                response=self.client.post('/api/imports',{'file':self.csv([data]),'kind':'complaints'},format='multipart')
            self.assertEqual(response.status_code,201,response.data);self.finish(response.data)
        self.assertEqual(Complaint.objects.filter(category='needs_categorization').count(),2)
        bad=self.upload([self.row(category='Hostel dispute')]);self.assertEqual(bad['counts'],{'rejected':1})
        response=self.client.post(f"/api/imports/{bad['id']}",{'action':'preview','mapping':bad['mapping'],'category_mapping':{'Hostel dispute':'other'}},format='json')
        self.assertEqual(response.status_code,200,response.data);self.finish(response.data)
        self.assertEqual(Complaint.objects.get(source_system='demo-rb').category,'other')
        row=self.client.get(f"/api/imports/{bad['id']}/rows").data['results'][0];self.assertEqual(row['raw']['category'],'Hostel dispute')

    def test_category_action_is_coordinator_only_versioned_and_preserves_vectors(self):
        for user,status in [(self.officer,403),(self.auditor,403),(self.coordinator,200)]:
            self.client.force_authenticate(user)
            response=self.client.post(f'/api/cases/{self.case.pk}/actions',{'kind':'category','category':'other','expected_version':1,'reason':'Reviewed category correction.'},format='json')
            self.assertEqual(response.status_code,status,response.data)
        self.case.refresh_from_db();self.assertEqual(self.case.category,'other');self.assertEqual(self.case.matching_state,'pending')
        self.assertEqual(self.client.post(f'/api/cases/{self.case.pk}/actions',{'kind':'category','category':'refunds','expected_version':1,'reason':'Stale'},format='json').status_code,409)

    def test_selected_updates_preserve_originals_and_replay_never_reapplies(self):
        case,job,url=self.changed(summary='Different incoming allegation, deliberately not adopted.',category='other')
        original=(case.summary,case.description,case.submission_fingerprint,case.bureau_id,case.model_revision)
        payload=self.approval(case)
        for _ in range(2):self.assertEqual(self.client.post(url,payload,format='json').status_code,200)
        case.refresh_from_db();self.assertEqual(case.status,'under_review');self.assertEqual(case.category,'refunds')
        self.assertEqual((case.summary,case.description,case.submission_fingerprint,case.bureau_id,case.model_revision),original)
        self.assertEqual(case.version,2);self.assertEqual(case.actions.filter(kind='source_conflict').count(),1)
        self.assertEqual(self.client.post(url,{**payload,'reason':'Different approval'},format='json').status_code,409)
        # An acknowledged source snapshot stays acknowledged after a later official action.
        self.client.post(f'/api/cases/{case.pk}/actions',{'kind':'status','status':'awaiting_response','reason':'New evidence requested.','expected_version':2},format='json')
        repeat=self.upload([self.row(status='In progress',summary='Different incoming allegation, deliberately not adopted.',category='other')])
        self.assertEqual(repeat['counts'],{'duplicate':1});self.finish(repeat);case.refresh_from_db()
        self.assertEqual(case.status,'awaiting_response');self.assertEqual(case.actions.filter(kind='source_conflict').count(),1)

    def test_approval_denies_non_coordinators_and_stale_versions(self):
        case,job,url=self.changed()
        for user,expected in [(self.officer,404),(self.auditor,403)]:
            self.client.force_authenticate(user);self.assertEqual(self.client.post(url,self.approval(case),format='json').status_code,expected)
        self.client.force_authenticate(self.officer);own=self.upload([self.row(status='In progress')]);self.finish(own)
        self.assertEqual(self.client.post(f"/api/imports/{own['id']}/rows/2/resolve",self.approval(case),format='json').status_code,403)
        self.client.force_authenticate(self.coordinator)
        self.assertEqual(self.client.post(url,self.approval(case,expected_case_version=999),format='json').status_code,409)
        self.assertEqual(self.client.post(url,self.approval(case,retain_unselected=False),format='json').status_code,400)
        self.assertEqual(self.client.post(url,self.approval(case,fields=['summary']),format='json').status_code,400)

    def test_derived_defaults_cannot_reset_metadata_and_failures_roll_back(self):
        case,job,url=self.changed()
        future=case.due_at+timedelta(days=9);case.due_at=future;case.classification='grievance';case.save()
        for field in ['due_at','classification']:
            self.assertEqual(self.client.post(url,self.approval(case,[field]),format='json').status_code,400)
        with patch('cases.source_intake.CaseAction.objects.create',side_effect=RuntimeError('Audit unavailable')):
            with self.assertRaises(RuntimeError):self.client.post(url,self.approval(case),format='json')
        case.refresh_from_db();self.assertEqual(case.status,'registered');self.assertEqual(case.version,1)
        self.assertEqual(ImportJob.objects.get(pk=job['id']).rows.get(number=2).state,'conflict')

    def test_closure_and_reopening_are_explicit_and_only_affect_one_case(self):
        original=self.upload();self.finish(original);case=Complaint.objects.get(source_system='demo-rb')
        case.next_action='Request evidence';case.next_action_date=timezone.localdate();case.save()
        disposed=(timezone.now()-timedelta(days=1)).isoformat()
        closed=self.upload([self.row(status='disposed',disposed_at=disposed,resolution_note='Source reports repayment; reviewed supporting receipt.')]);self.finish(closed)
        response=self.client.post(f"/api/imports/{closed['id']}/rows/2/resolve",self.approval(case),format='json');self.assertEqual(response.status_code,200,response.data)
        case.refresh_from_db();self.assertEqual(case.status,'disposed');self.assertEqual(case.next_action,'');self.assertIsNone(case.next_action_date)
        self.hidden.refresh_from_db();self.assertEqual(self.hidden.status,'registered')
        reopened=self.upload([self.row(status='In progress')]);self.finish(reopened)
        url=f"/api/imports/{reopened['id']}/rows/2/resolve"
        self.assertEqual(self.client.post(url,self.approval(case),format='json').status_code,400)
        self.assertEqual(self.client.post(url,self.approval(case,confirm_reopen=True),format='json').status_code,200)
        case.refresh_from_db();self.assertIsNone(case.disposed_at)

    @override_settings(DEMO_MODE=True)
    def test_demo_indicator_and_category_choices_are_server_provided(self):
        self.assertTrue(self.client.get('/api/session').data['user']['features']['demo_mode'])
        labels=self.client.get('/api/options').data['category_labels'];self.assertEqual(labels['needs_categorization'],'Needs categorization')

    def test_disposal_valid_for_source_but_before_original_receipt_is_rejected(self):
        original=self.upload();self.finish(original);case=Complaint.objects.get(source_system='demo-rb')
        incoming=self.row(status='disposed',received_at=(case.received_at-timedelta(days=20)).isoformat(),disposed_at=(case.received_at-timedelta(days=10)).isoformat(),resolution_note='Earlier source note cannot close a later received case.')
        job=self.upload([incoming]);self.finish(job)
        self.assertEqual(self.client.post(f"/api/imports/{job['id']}/rows/2/resolve",self.approval(case),format='json').status_code,400)
        case.refresh_from_db();self.assertEqual(case.status,'registered')


class OperationalConcurrentTests(TransactionTestCase):
    make_user=classmethod(SourceIntakeTests.make_user.__func__)
    make_case=classmethod(SourceIntakeTests.make_case.__func__)
    csv=SourceIntakeTests.csv
    row=SourceIntakeTests.row
    finish=SourceIntakeTests.finish
    upload=SourceIntakeTests.upload

    def setUp(self, setup=SourceIntakeTests.setUpTestData.__func__):
        setup(type(self))
        from rest_framework.test import APIClient
        self.client=APIClient();self.client.force_authenticate(self.coordinator)

    def test_concurrent_different_approvals_commit_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from django.db import close_old_connections
        from rest_framework.test import APIClient
        first=self.upload();self.finish(first);case=Complaint.objects.get(source_system='demo-rb')
        changed=self.upload([self.row(status='In progress')]);self.finish(changed)
        def approve(reason):
            close_old_connections()
            try:
                client=APIClient();client.force_authenticate(self.coordinator)
                return client.post(f"/api/imports/{changed['id']}/rows/2/resolve",{'decision':'apply_selected_updates','fields':['status'],
                    'expected_version':1,'expected_case_version':case.version,'reason':reason,'retain_unselected':True},format='json').status_code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(approve,['Approved after source inspection A.','Approved after source inspection B.']))
        self.assertEqual(sorted(results),[200,409]);case.refresh_from_db();self.assertEqual(case.version,2)
        self.assertEqual(case.actions.filter(kind='source_conflict').count(),1)


del SourceIntakeTests
