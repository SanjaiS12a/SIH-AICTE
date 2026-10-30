import io
import json
import uuid
from datetime import timedelta
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from django_q.models import OrmQ
from rest_framework.test import APIClient
from .models import Institution, Bureau, Membership, Complaint, CaseAction, OverlapCandidate, Attachment, Notification, AuditEvent
from .tasks import send_reminders

class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rb = Bureau.objects.create(code='RB',name='Regulation demo')
        cls.pg = Bureau.objects.create(code='PGRC',name='Grievance demo')
        cls.institution = Institution.objects.create(name='Fictional College',permanent_id='DEMO-001',region='South',district='Fictional')
        cls.coordinator = cls.make_user('coordinator','coordinator')
        cls.officer = cls.make_user('officer','officer',cls.rb)
        cls.other = cls.make_user('other','officer',cls.pg)
        cls.auditor = cls.make_user('auditor','auditor')
        cls.case = cls.make_case(cls.rb,'A')
        cls.hidden = cls.make_case(cls.pg,'B')

    @classmethod
    def make_user(cls,name,role,bureau=None):
        u = User.objects.create_user(name,password='test-password-123',first_name=name)
        Membership.objects.create(user=u,role=role,bureau=bureau)
        return u

    @classmethod
    def make_case(cls,bureau,ref):
        now=timezone.now()
        return Complaint.objects.create(reference=ref,submission_id=uuid.uuid4(),source_reference=ref,
            institution=cls.institution,bureau=bureau,created_by=cls.coordinator,category='refunds',
            summary='Fee refund was withheld.',description='A fictional test complaint.',received_at=now-timedelta(days=35),due_at=now-timedelta(days=5))

    def setUp(self):
        self.client=APIClient()
        self.client.force_authenticate(self.coordinator)

    def payload(self):
        return {'submission_id':str(uuid.uuid4()),'institution':str(self.institution.id),'bureau':'RB',
                'source_reference':'NEW-001','summary':'The college withheld the fee refund.','description':'Fictional complaint.','category':'refunds'}

    @patch('cases.serializers.CreateCaseSerializer.validate_summary',lambda self,value:value)
    def test_creation_is_atomic_and_retries_are_idempotent(self):
        payload=self.payload()
        response=self.client.post('/api/cases',payload,format='json')
        self.assertEqual(response.status_code,201,response.data)
        case=Complaint.objects.get(pk=response.data['id'])
        self.assertEqual(case.actions.count(),1)
        self.assertEqual(OrmQ.objects.count(),1)
        self.assertEqual(case.due_at-case.received_at,timedelta(days=30))
        self.assertEqual(self.client.post('/api/cases',payload,format='json').status_code,200)
        self.assertEqual(Complaint.objects.count(),3)
        self.client.post(f'/api/cases/{case.id}/actions',{'kind':'transfer','bureau':'PGRC','reason':'Test ownership change','expected_version':1},format='json')
        self.assertEqual(self.client.post('/api/cases',payload,format='json').status_code,200)
        payload['summary']='Changed content'
        self.assertEqual(self.client.post('/api/cases',payload,format='json').status_code,409)

    @patch('cases.serializers.CreateCaseSerializer.validate_summary',lambda self,value:value)
    @patch('cases.api.async_task',side_effect=RuntimeError('queue unavailable'))
    def test_queue_failure_rolls_back_case_and_history(self,_queue):
        with self.assertRaises(RuntimeError):
            self.client.post('/api/cases',self.payload(),format='json')
        self.assertEqual(Complaint.objects.count(),2)
        self.assertEqual(CaseAction.objects.count(),0)

    def test_invalid_creation_leaves_no_partial_records(self):
        payload=self.payload();payload['institution']=str(uuid.uuid4())
        with patch('cases.serializers.CreateCaseSerializer.validate_summary',lambda self,value:value):
            self.assertEqual(self.client.post('/api/cases',payload,format='json').status_code,400)
        self.assertEqual(Complaint.objects.count(),2)
        self.assertFalse(OrmQ.objects.exists())

    @patch('cases.matching.tokenizer')
    def test_summary_token_limit_rejects_instead_of_truncating(self, tokenizer):
        tokenizer.return_value.encode.return_value.ids=list(range(257))
        response=self.client.post('/api/cases',self.payload(),format='json')
        self.assertEqual(response.status_code,400)
        self.assertEqual(Complaint.objects.count(),2)

    @patch('cases.serializers.CreateCaseSerializer.validate_summary',lambda self,value:value)
    def test_source_reference_uniqueness(self):
        p=self.payload()
        self.assertEqual(self.client.post('/api/cases',p,format='json').status_code,201)
        p['submission_id']=str(uuid.uuid4())
        self.assertEqual(self.client.post('/api/cases',p,format='json').status_code,409)

    def test_officer_cannot_access_hidden_data_through_any_read_path(self):
        self.client.force_authenticate(self.officer)
        result=self.client.get('/api/cases')
        self.assertEqual(result.data['count'],1)
        self.assertEqual(self.client.get(f'/api/cases/{self.hidden.id}').status_code,404)
        self.assertEqual(self.client.get('/api/cases?bureau=PGRC').data['count'],0)
        dashboard=self.client.get('/api/dashboard').data
        self.assertEqual(dashboard['total'],1)
        self.assertNotIn('overlap_reviews',dashboard)
        self.assertNotIn('coordination_notices',dashboard)
        csv=b''.join(self.client.get('/api/reports.csv').streaming_content).decode()
        self.assertNotIn('PGRC',csv)
        self.assertEqual(self.client.get('/api/overlaps').status_code,403)
        detail=self.client.get(f'/api/cases/{self.case.id}').data
        self.assertEqual(detail['institution_history'],[])

    def test_no_membership_denies_access_by_default(self):
        self.client.force_authenticate(User.objects.create_user('unassigned'))
        self.assertEqual(self.client.get('/api/cases').data['count'],0)
        self.assertEqual(self.client.get('/api/dashboard').data['total'],0)

    def test_transfer_history_is_atomic_and_stale_updates_conflict(self):
        self.case.assigned_to=self.officer;self.case.save()
        payload={'kind':'transfer','bureau':'PGRC','reason':'Requires the other bureau.','expected_version':1}
        self.assertEqual(self.client.post(f'/api/cases/{self.case.id}/actions',payload,format='json').status_code,200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.bureau,self.pg)
        self.assertIsNone(self.case.assigned_to)
        self.assertEqual(self.case.version,2)
        self.assertEqual(self.case.actions.get().changes['bureau'],{'before':'RB','after':'PGRC'})
        self.assertEqual(self.client.post(f'/api/cases/{self.case.id}/actions',payload,format='json').status_code,409)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get(f'/api/cases/{self.case.id}').status_code,404)

    @patch('cases.api.CaseAction.objects.create',side_effect=RuntimeError('history failure'))
    def test_failed_transfer_preserves_original_ownership(self,_action):
        with self.assertRaises(RuntimeError):
            self.client.post(f'/api/cases/{self.case.id}/actions',{'kind':'transfer','bureau':'PGRC','reason':'Test','expected_version':1},format='json')
        self.case.refresh_from_db()
        self.assertEqual(self.case.bureau,self.rb)
        self.assertEqual(self.case.version,1)

    def test_officer_cannot_transfer_assign_deadline_or_retry(self):
        self.client.force_authenticate(self.officer)
        for data in [{'kind':'transfer','bureau':'PGRC'},{'kind':'assign','assigned_to':self.officer.pk},
                     {'kind':'deadline','due_at':timezone.now().isoformat()},{'kind':'retry_matching'}]:
            result=self.client.post(f'/api/cases/{self.case.id}/actions',{**data,'reason':'Test','expected_version':1},format='json')
            self.assertEqual(result.status_code,403,result.data)

    def test_disposal_requires_reason_and_reopening_requires_coordinator(self):
        url=f'/api/cases/{self.case.id}/actions'
        self.assertEqual(self.client.post(url,{'kind':'status','status':'disposed','expected_version':1},format='json').status_code,400)
        self.assertEqual(self.client.post(url,{'kind':'status','status':'disposed','expected_version':1,'reason':'Resolution documented.'},format='json').status_code,200)
        self.case.refresh_from_db();self.assertIsNotNone(self.case.disposed_at)
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.post(url,{'kind':'status','status':'under_review','expected_version':2,'reason':'Reopen'},format='json').status_code,403)

    def test_auditor_is_read_only(self):
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.client.get('/api/cases').data['count'],2)
        self.assertEqual(self.client.post(f'/api/cases/{self.case.id}/actions',{'kind':'note','expected_version':1,'reason':'Test'},format='json').status_code,403)

    def test_assign_requires_officer_from_current_bureau(self):
        result=self.client.post(f'/api/cases/{self.case.id}/actions',{'kind':'assign','assigned_to':self.other.pk,'expected_version':1,'reason':'Assign'},format='json')
        self.assertEqual(result.status_code,400)

    def test_disposal_month_filter_uses_resolution_date(self):
        self.case.status='disposed';self.case.disposed_at=timezone.now();self.case.save()
        day=timezone.localdate().isoformat()
        rows=self.client.get(f'/api/cases?disposed_from={day}&disposed_to={day}')
        self.assertEqual(rows.data['count'],1)
        self.assertEqual(rows.data['results'][0]['id'],str(self.case.id))

    def test_reversed_date_filters_are_rejected(self):
        self.assertEqual(self.client.get('/api/cases?from=2026-10-20&to=2026-10-01').status_code,400)

    def test_review_records_both_histories_without_merging(self):
        left,right=sorted([self.case.pk,self.hidden.pk])
        pair=OverlapCandidate.objects.create(left_id=left,right_id=right,score=.9,model_revision='test')
        url=f'/api/overlaps/{pair.pk}/review'
        payload={'decision':'same_incident','reason':'Same dates and requested remedy.','expected_version':1}
        self.assertEqual(self.client.post(url,payload,format='json').status_code,200)
        self.assertEqual(Complaint.objects.count(),2)
        self.assertEqual(CaseAction.objects.filter(kind='overlap_review').count(),2)
        self.assertEqual(self.client.post(url,payload,format='json').status_code,409)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.client.post(url,payload,format='json').status_code,403)

    def test_reminders_are_idempotent_scoped_and_deadline_aware(self):
        now=timezone.now()
        self.case.due_at=now+timedelta(days=7);self.case.save()
        send_reminders(now)
        count=Notification.objects.count()
        send_reminders(now)
        self.assertEqual(count,Notification.objects.count())
        self.assertTrue(Notification.objects.filter(case=self.case,kind='due_7_days',user=self.officer).exists())
        self.assertFalse(Notification.objects.filter(case=self.case,user=self.other).exists())
        send_reminders(self.case.due_at-timedelta(days=1))
        self.assertTrue(Notification.objects.filter(case=self.case,kind='due_1_day').exists())
        send_reminders(self.case.due_at+timedelta(seconds=1))
        self.assertTrue(Notification.objects.filter(case=self.case,kind='overdue').exists())
        self.case.bureau=self.pg;self.case.save()
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get('/api/notifications').data['unread'],0)

    def test_dashboard_and_filters_have_same_case_counts(self):
        for suffix in ['', '?status=registered','?overdue=true','?bureau=RB','?age=31-60','?q=DEMO-001']:
            rows=self.client.get('/api/cases'+suffix).data
            stats=self.client.get('/api/dashboard'+suffix).data
            self.assertEqual(rows['count'],stats['total'])

    def test_csv_formula_injection_is_escaped_and_export_is_audited(self):
        self.institution.name='=HYPERLINK("bad")';self.institution.save()
        response=self.client.get('/api/reports.csv')
        self.assertIn("'=HYPERLINK",b''.join(response.streaming_content).decode())
        self.assertEqual(AuditEvent.objects.get().kind,'export')

    def test_uploads_are_validated_and_private_after_transfer(self):
        from PIL import Image
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            bad=SimpleUploadedFile('fake.png',b'not an image',content_type='image/png')
            self.assertEqual(self.client.post(f'/api/cases/{self.case.id}/attachments',{'file':bad}).status_code,400)
            large=SimpleUploadedFile('large.pdf',b'x'*(5*1024*1024+1))
            self.assertEqual(self.client.post(f'/api/cases/{self.case.id}/attachments',{'file':large}).status_code,400)
            data=io.BytesIO();Image.new('RGB',(3,3),'white').save(data,format='PNG')
            file=SimpleUploadedFile('evidence.png',data.getvalue(),content_type='application/octet-stream')
            response=self.client.post(f'/api/cases/{self.case.id}/attachments',{'file':file})
            self.assertEqual(response.status_code,201,response.data)
            attachment=Attachment.objects.get()
            self.assertNotIn('file',response.data)
            self.client.force_authenticate(self.other)
            self.assertEqual(self.client.get(f'/api/attachments/{attachment.id}').status_code,404)
            self.client.force_authenticate(self.officer)
            result=self.client.get(f'/api/attachments/{attachment.id}')
            self.assertEqual(result.status_code,200)
            self.assertIn('attachment',result['Content-Disposition'])
            result.close()

    def test_login_and_mutations_require_csrf(self):
        client=APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.post('/accounts/login/',{'username':'coordinator','password':'test-password-123'}).status_code,403)
        client.force_login(self.coordinator)
        self.assertEqual(client.post(f'/api/cases/{self.case.id}/actions',{'kind':'note','reason':'x','expected_version':1},format='json').status_code,403)

    @patch('cases.matching.encoder')
    @patch('cases.matching.runtime',return_value=('unused','test-revision',.75))
    @patch('cases.matching.threshold',return_value=.75)
    def test_matching_is_institution_filtered_and_preserves_review(self,_threshold,_revision,encoder):
        import numpy as np
        from .matching import match_case
        vec=[1.0]+[0.0]*383
        encoder.return_value.encode.return_value=np.array(vec)
        self.hidden.embedding=vec;self.hidden.model_revision='test-revision';self.hidden.save()
        foreign=Institution.objects.create(name='Other College',permanent_id='OTHER',region='North',district='Other')
        self.make_case(self.rb,'C')
        Complaint.objects.filter(reference='C').update(institution=foreign,embedding=vec,model_revision='test-revision')
        match_case(str(self.case.pk))
        pair=OverlapCandidate.objects.get();pair.decision='unrelated';pair.save()
        match_case(str(self.case.pk))
        self.assertEqual(OverlapCandidate.objects.count(),1)
        pair.refresh_from_db();self.assertEqual(pair.decision,'unrelated')
        self.case.refresh_from_db();self.assertEqual(self.case.matching_state,'complete')

    @patch('cases.matching.encoder',side_effect=RuntimeError('model unavailable'))
    def test_failed_matching_is_visible_and_retryable(self,_encoder):
        from .matching import match_case
        with self.assertRaises(RuntimeError):match_case(str(self.case.pk))
        self.case.refresh_from_db();self.assertEqual(self.case.matching_state,'failed')
        result=self.client.post(f'/api/cases/{self.case.id}/actions',{'kind':'retry_matching','expected_version':1,'reason':'Model repaired'},format='json')
        self.assertEqual(result.status_code,200)
        self.assertEqual(OrmQ.objects.count(),1)

class EvaluationTests(TestCase):
    def test_incident_families_never_cross_partitions(self):
        from .demo_data import evaluation_dataset
        data=evaluation_dataset()
        calibration={r['family'] for r in data['records'] if r['split']=='calibration'}
        test={r['family'] for r in data['records'] if r['split']=='test'}
        self.assertFalse(calibration&test)
        self.assertGreaterEqual(len(data['pairs']),150)
        self.assertIn('human review pending',data['label_provenance'])

    def test_calibration_does_not_claim_success_without_precision_floor(self):
        import numpy as np
        from .management.commands.evaluate_matching import calibrate
        self.assertIsNone(calibrate(np.array([.9,.8]),np.array([False,False])))

class ConcurrentSubmissionTests(TransactionTestCase):
    @patch('cases.serializers.CreateCaseSerializer.validate_summary',lambda self,value:value)
    def test_simultaneous_replays_create_one_case_and_one_job(self):
        from concurrent.futures import ThreadPoolExecutor
        from django.db import connections
        user=User.objects.create_user('concurrent-coordinator')
        Membership.objects.create(user=user,role='coordinator')
        bureau=Bureau.objects.create(code='RB',name='Demo')
        institution=Institution.objects.create(name='Fictional concurrent test',permanent_id='TEST-RACE',region='Demo',district='Demo')
        payload={'submission_id':str(uuid.uuid4()),'institution':str(institution.pk),'bureau':bureau.code,
                 'source_reference':'RACE','category':'refunds','summary':'A withheld refund.','description':'Synthetic concurrency check.'}
        def submit(_):
            try:
                client=APIClient();client.force_authenticate(user)
                response=client.post('/api/cases',payload,format='json')
                return response.status_code,response.data
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(submit,range(2)))
        self.assertEqual(sorted(x[0] for x in results),[200,201],results)
        self.assertEqual(results[0][1]['id'],results[1][1]['id'])
        self.assertEqual(Complaint.objects.count(),1)
        self.assertEqual(CaseAction.objects.count(),1)
        self.assertEqual(OrmQ.objects.count(),1)
