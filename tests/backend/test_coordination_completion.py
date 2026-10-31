import uuid
import csv
import io
from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone
from django.test import TestCase
from django.test import override_settings
from django.core.management import call_command
from django.test.utils import CaptureQueriesContext
from django.db import connection
from pathlib import Path
from tempfile import TemporaryDirectory
from django.db import transaction, IntegrityError
from rest_framework.test import APIClient
from cases.models import Institution, OverlapCandidate, CaseAction, Membership, Complaint
from .test_workflow import WorkflowTests

class CoordinationCompletionTests(TestCase):
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)
    @classmethod
    def setUpTestData(cls): WorkflowTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.coordinator)
    def payload(self, **extra):
        return {'left':str(self.case.pk),'right':str(self.hidden.pk),'decision':'related_issue','reason':'Reviewed original references and dates',**extra}
    def test_manual_pair_normalizes_and_retries_without_duplicate_history(self):
        with patch('cases.matching.encoder',side_effect=RuntimeError('offline')):
            response=self.client.post('/api/relationships',self.payload(),format='json')
        self.assertEqual(response.status_code,201,response.data)
        pair=OverlapCandidate.objects.get();self.assertLess(pair.left_id,pair.right_id)
        self.assertEqual(pair.origin,'manual');self.assertIsNone(pair.score)
        self.assertEqual(CaseAction.objects.count(),2)
        reverse=self.payload(left=str(self.hidden.pk),right=str(self.case.pk))
        self.assertEqual(self.client.post('/api/relationships',reverse,format='json').status_code,200)
        self.assertEqual(CaseAction.objects.count(),2)
        self.assertEqual(self.client.post('/api/relationships',self.payload(reason='Changed'),format='json').status_code,409)
        self.assertEqual(self.client.post(f'/api/overlaps/{pair.pk}/review',{'expected_version':1,'decision':'unrelated','reason':'Separate incidents confirmed'},format='json').status_code,200)
        self.assertEqual(CaseAction.objects.count(),4)
    def test_same_institution_and_reason_validation(self):
        for extra in [{'right':str(self.case.pk)},{'reason':' '},{'decision':'duplicate'}]:
            self.assertEqual(self.client.post('/api/relationships',self.payload(**extra),format='json').status_code,400)
        other=Institution.objects.create(name='Other',permanent_id='OTHER',region='South',district='Other')
        self.hidden.institution=other;self.hidden.save()
        self.assertEqual(self.client.post('/api/relationships',self.payload(),format='json').status_code,400)
        self.assertFalse(OverlapCandidate.objects.exists())
    def test_existing_semantic_evidence_and_scores_are_preserved(self):
        left,right=sorted([self.case.pk,self.hidden.pk]);pair=OverlapCandidate.objects.create(left_id=left,right_id=right,score=.91,model_revision='original',evidence={'scope':'original'})
        self.assertEqual(self.client.post('/api/relationships',self.payload(expected_version=1),format='json').status_code,200)
        pair.refresh_from_db();self.assertEqual((pair.score,pair.origin,pair.model_revision,pair.evidence),(.91,'semantic','original',{'scope':'original'}))
    def test_history_rollback_and_officer_redaction(self):
        original=CaseAction.objects.create;count=0
        def fail_second(*args,**kwargs):
            nonlocal count
            count+=1
            if count==2:raise RuntimeError('Second history unavailable')
            return original(*args,**kwargs)
        with patch('cases.relationships.CaseAction.objects.create',side_effect=fail_second),self.assertRaises(RuntimeError):
            self.client.post('/api/relationships',self.payload(),format='json')
        self.assertFalse(OverlapCandidate.objects.exists());self.assertFalse(CaseAction.objects.exists())
        self.client.post('/api/relationships',self.payload(),format='json')
        for user in [self.officer,self.auditor]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.post('/api/relationships',self.payload(),format='json').status_code,403)
        self.client.force_authenticate(self.officer)
        data=str(self.client.get(f'/api/cases/{self.case.pk}').data['actions'])
        self.assertNotIn('overlap_id',data);self.assertNotIn('Reviewed original',data)
        self.assertEqual(self.client.get('/api/overlaps').status_code,403)
        Membership.objects.filter(user=self.officer).update(bureau=self.pg)
        self.assertEqual(self.client.get(f'/api/cases/{self.case.pk}').status_code,404)

    def test_all_time_notices_ignore_receipt_category_and_bureau_filters(self):
        self.hidden.category='admissions';self.hidden.received_at=timezone.now()-timedelta(days=500);self.hidden.save()
        response=self.client.get('/api/coordination-notices?from=2099-01-01&category=refunds&bureau=RB')
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(response.data['count'],1)
        row=response.data['results'][0]
        self.assertEqual((row['count'],row['bureaus']),(2,2))
        self.assertEqual({b['code'] for b in row['bureau_details']},{'RB','PGRC'})
        self.assertEqual({c['reference'] for c in row['cases']},{'A','B'})
        d=self.client.get('/api/dashboard?from=2099-01-01').data
        self.assertEqual(d['total'],0);self.assertEqual(d['coordination_institutions'],1)
        for user in [self.officer,self.other]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get('/api/coordination-notices').status_code,403)
            self.assertNotIn('coordination_notices',self.client.get('/api/dashboard').data)
    def test_notices_follow_current_ownership_closure_and_reopening(self):
        self.hidden.bureau=self.rb;self.hidden.save()
        CaseAction.objects.create(case=self.hidden,actor=self.coordinator,kind='transfer',reason='Historical transfer',changes={'bureau':{'before':'PGRC','after':'RB'}})
        self.assertEqual(self.client.get('/api/coordination-notices').data['count'],0)
        self.hidden.bureau=self.pg;self.hidden.save()
        self.assertEqual(self.client.get('/api/coordination-notices').data['count'],1)
        self.hidden.status='disposed';self.hidden.save()
        self.assertEqual(self.client.get('/api/coordination-notices').data['count'],0)
        self.hidden.status='under_review';self.hidden.save()
        third=self.make_user('third-coordinator','coordinator')
        from cases.models import Bureau
        other=Bureau.objects.create(code='OTHER',name='Other registered Bureau')
        self.make_case(other,'THIRD')
        with patch('cases.matching.encoder',side_effect=RuntimeError('unavailable')):
            self.assertEqual(self.client.get('/api/coordination-notices').data['results'][0]['bureaus'],3)
    def test_management_kpis_boundaries_and_closed_escalations(self):
        now=timezone.now()
        for name,delta in [('NOW',0),('WEEK',7*86400),('LATER',7*86400+1),('PAST',-1)]:
            c=self.make_case(self.rb,name);c.due_at=now+timedelta(seconds=delta);c.save()
        esc=self.client.post(f'/api/cases/{self.hidden.pk}/escalations',{'submission_id':str(uuid.uuid4()),'expected_version':1,'reason':'Supervision'},format='json')
        self.assertEqual(esc.status_code,201)
        self.hidden.refresh_from_db();self.hidden.status='disposed';self.hidden.save()
        with patch('django.utils.timezone.now',return_value=now):
            d=self.client.get('/api/dashboard').data
            self.assertEqual((d['total'],d['pending'],d['disposed'],d['overdue'],d['approaching'],d['institutions'],d['unresolved_escalations']),(6,5,1,2,2,1,1))
            self.assertAlmostEqual(d['closed_share'],1/6)
            self.assertEqual(self.client.get('/api/cases?approaching=true').data['count'],2)
            self.assertEqual(self.client.get('/api/cases?overdue=true&approaching=true').data['count'],0)
            self.assertEqual(self.client.get('/api/cases?status=registered&closed=true').data['count'],0)
        self.assertEqual(sum(c['count'] for c in d['management']['classifications']),6)
    def test_action_period_does_not_use_receipt_cohort_and_exports_match(self):
        CaseAction.objects.create(case=self.case,actor=self.coordinator,kind='transfer',reason='A current movement on an older case')
        today=timezone.localdate().isoformat()
        d=self.client.get(f'/api/dashboard?from={today}&to={today}').data
        self.assertEqual(d['total'],0)
        self.assertEqual(next(r['count'] for r in d['management']['movement_counts'] if r['event']=='transfer'),1)
        url=f'/api/movements?from={today}&to={today}&event=transfer'
        self.assertEqual(self.client.get(url).data['count'],1)
        exported=b''.join(self.client.get(url.replace('/api/movements?','/api/movements.csv?')).streaming_content).decode()
        self.assertEqual(len(list(csv.reader(io.StringIO(exported))))-1,1)
        self.assertEqual(self.client.get('/api/movements?event=invalid').status_code,400)
    def test_exact_district_and_institution_cohort_drilldown(self):
        other=Institution.objects.create(name='Similar district',permanent_id='DIST-LONG',region='South',district='New Fictional')
        self.hidden.institution=other;self.hidden.save()
        self.assertEqual(self.client.get('/api/cases?district=Fictional').data['count'],2)
        self.assertEqual(self.client.get('/api/cases?district=Fictional&district_exact=true').data['count'],1)
        self.assertEqual(self.client.get('/api/institution-registry?with_cases=true&q=A&district=Fictional&district_exact=true').data['count'],1)
        self.assertEqual(self.client.get('/api/institution-registry?with_cases=true&from=2099-01-01').data['count'],0)
    def test_relationship_export_and_action_export_never_leak_to_officers(self):
        self.client.post('/api/relationships',self.payload(),format='json')
        response=self.client.get('/api/relationships.csv?decision=all')
        content=b''.join(response.streaming_content).decode()
        self.assertIn('manual,Not model-scored',content)
        for user in [self.officer,self.other]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get('/api/relationships.csv').status_code,403)
            actions=self.client.get('/api/movements').data
            self.assertEqual(actions['count'],1)
            self.assertNotIn('overlap_id',str(actions));self.assertNotIn('Reviewed original',str(actions))
            csvdata=b''.join(self.client.get('/api/movements.csv').streaming_content).decode()
            self.assertNotIn('overlap_id',csvdata)
        no_bureau=self.make_user('no-bureau','officer')
        self.client.force_authenticate(no_bureau)
        self.assertEqual(self.client.get('/api/cases').data['count'],0)
        self.assertEqual(self.client.get('/api/movements').data['count'],0)

    def test_pair_page_query_count_does_not_grow_per_case(self):
        for i in range(21):
            other=self.make_case(self.rb,f'PAIR-{i}')
            left,right=sorted([self.case.pk,other.pk])
            OverlapCandidate.objects.create(left_id=left,right_id=right,score=.8,model_revision='fixture')
        with CaptureQueriesContext(connection) as queries:
            response=self.client.get('/api/overlaps?decision=all')
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.data['results']),20)
        self.assertLessEqual(len(queries),12)
    def test_presentation_seed_is_deterministic_and_preserves_played_work(self):
        from cases.models import Attachment
        with TemporaryDirectory() as directory, override_settings(RESULTS_DIR=Path(directory),MEDIA_ROOT=Path(directory)/'private'),patch('cases.management.commands.seed_demo.Path') as root:
            root.return_value=Path(directory)
            call_command('seed_demo',verbosity=0)
            call_command('seed_sih_demo',verbosity=0)
            case=Complaint.objects.get(source_system='sih-demo',source_reference='SIH-26264-REFUND-RB')
            case.classification='regulatory_compliance';case.save()
            before=(Complaint.objects.count(),CaseAction.objects.count(),Attachment.objects.count())
            call_command('seed_sih_demo',verbosity=0)
            self.assertEqual(before,(Complaint.objects.count(),CaseAction.objects.count(),Attachment.objects.count()))
            case.refresh_from_db();self.assertEqual(case.classification,'regulatory_compliance')
            self.assertEqual(Complaint.objects.filter(source_system='sih-demo').count(),4)
