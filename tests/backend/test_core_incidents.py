import csv
import hashlib
import io
import uuid
from datetime import timedelta
from django.db import connection, transaction, DatabaseError
from django.test import TestCase, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient
from cases.models import Complaint, CaseAction, IncidentGroup, IncidentMembership, OverlapCandidate, CoordinationRecord
from .test_workflow import WorkflowTests


@override_settings(ENABLE_INCIDENT_GROUPS=True,ENABLE_REVIEWED_FACTS=True)
class CoreIncidentTests(TestCase):
    setUpTestData = classmethod(WorkflowTests.setUpTestData.__func__)
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)

    def setUp(self):
        self.client=APIClient(); self.client.force_authenticate(self.coordinator)

    def group(self, cases=None, **extra):
        payload={'submission_id':str(uuid.uuid4()),'institution':str(self.institution.pk),'title':'Reviewed refund incident',
            'reason':'Explicit incident evidence checked by coordinator','cases':[str(c.pk) for c in (cases or [self.case,self.hidden])],**extra}
        r=self.client.post('/api/incident-groups',payload,format='json'); self.assertEqual(r.status_code,201,r.data)
        return r.data,payload

    def counts(self, query=''):
        r=self.client.get('/api/incident-summary'+query); self.assertEqual(r.status_code,200,r.data); return r.data['counts']

    def rows(self,metric,query=''):
        r=self.client.get('/api/incident-summary/records?metric='+metric+query);self.assertEqual(r.status_code,200,r.data);return r.data

    def test_six_cases_one_group_distinct_counts_and_lifecycle_unchanged(self):
        cases=[self.case,self.hidden]+[self.make_case(self.rb,f'SIX-{i}') for i in range(4)]
        before=list(Complaint.objects.order_by('pk').values('id','bureau_id','status','due_at','version'))
        ids=sorted([c.pk for c in cases])
        for left,right in zip(ids,ids[1:]): OverlapCandidate.objects.create(left_id=left,right_id=right,score=.9)
        counts=self.counts();self.assertEqual(counts['complaints'],6);self.assertEqual(counts['pending_pairs'],5);self.assertEqual(counts['suggested_cases'],6)
        self.assertEqual(counts['confirmed_groups'],0)
        group,_=self.group(cases)
        counts=self.counts();self.assertEqual((counts['confirmed_groups'],counts['grouped_cases'],counts['ungrouped_cases']),(1,6,0))
        self.assertEqual(len(self.rows('confirmed_groups')['results'][0]['cases']),6)
        self.assertEqual(before,list(Complaint.objects.order_by('pk').values('id','bureau_id','status','due_at','version')))
        self.assertEqual(CaseAction.objects.filter(changes__group_id=group['id']).count(),6)

    def test_overlapping_groups_and_receipt_scope_use_unique_cases(self):
        third=self.make_case(self.rb,'THIRD')
        self.group();self.group([self.case,third])
        c=self.counts();self.assertEqual((c['confirmed_groups'],c['grouped_cases']),(2,3))
        Complaint.objects.filter(pk=self.case.pk).update(received_at=timezone.now())
        query='?from='+timezone.now().date().isoformat()
        c=self.counts(query);self.assertEqual((c['complaints'],c['confirmed_groups'],c['grouped_cases']),(1,2,1))
        row=self.rows('confirmed_groups','&from='+timezone.now().date().isoformat())['results'][0]
        self.assertEqual((row['scope_case_count'],row['all_time_case_count']),(1,2))

    def test_retirement_corrections_history_and_stale_versions(self):
        group,data=self.group();third=self.make_case(self.rb,'THIRD')
        update={**data,'expected_version':1,'cases':[str(self.case.pk),str(third.pk)],'reason':'Corrected membership after source review'}
        url='/api/incident-groups/'+group['id']
        r=self.client.patch(url,update,format='json');self.assertEqual(r.status_code,200,r.data)
        self.assertEqual(self.client.patch(url,update,format='json').status_code,409)
        self.assertFalse(IncidentMembership.objects.get(group_id=group['id'],case=self.hidden).active)
        r=self.client.patch(url,{**update,'expected_version':2,'state':'retired','reason':'Incident grouping superseded by corrected review'},format='json')
        self.assertEqual(r.status_code,200,r.data);self.assertIsNotNone(r.data['retired_at'])
        self.assertEqual(self.counts()['confirmed_groups'],0)
        history=self.client.get(url+'/history').data;self.assertEqual(history['count'],7)
        self.assertEqual(self.client.patch(url,{**update,'expected_version':3},format='json').status_code,400)
        with self.assertRaises(DatabaseError),transaction.atomic():
            IncidentMembership.objects.filter(group_id=group['id']).delete()

    def test_support_change_excludes_provisional_groups_without_deleting_members(self):
        a,b=sorted([self.case.pk,self.hidden.pk])
        pair=OverlapCandidate.objects.create(left_id=a,right_id=b,origin='manual',score=None,decision='same_incident',reviewer=self.coordinator)
        group,_=self.group(supporting_relationship=pair.pk)
        r=self.client.post(f'/api/overlaps/{pair.pk}/review',{'expected_version':1,'decision':'related_issue','reason':'Different events with the same concern'},format='json')
        self.assertEqual(r.status_code,200,r.data);self.assertEqual(self.counts()['confirmed_groups'],0)
        self.assertTrue(IncidentGroup.objects.get(pk=group['id']).needs_review)
        self.assertEqual(IncidentMembership.objects.filter(group_id=group['id'],active=True).count(),2)

    def test_missing_and_failed_matching_are_not_a_confirmed_zero(self):
        Complaint.objects.filter(pk=self.case.pk).update(matching_state='failed')
        Complaint.objects.filter(pk=self.hidden.pk).update(matching_state='complete',embedding=None)
        c=self.counts();self.assertEqual((c['matching_complete'],c['matching_failed'],c['matching_not_processed']),(0,1,1))
        self.assertEqual(sum(c[k] for k in ['matching_complete','matching_pending','matching_failed','matching_not_processed']),c['complaints'])

    def test_all_lists_and_csv_reconcile_and_formula_text_is_escaped(self):
        self.group(title='=dangerous spreadsheet formula')
        c=self.counts()
        for metric,count in c.items():
            rows=self.rows(metric);self.assertEqual(rows['count'],count,metric)
            response=self.client.get('/api/incident-summary.csv?metric='+metric)
            self.assertEqual(response.status_code,200)
            text=b''.join(response.streaming_content).decode()
            self.assertEqual(len(list(csv.DictReader(io.StringIO(text)))),count,metric)
            if metric=='confirmed_groups':self.assertIn("'=dangerous",text)

    def test_group_and_history_paginate_beyond_twenty_without_queries_per_row(self):
        for i in range(22):self.group(title=f'Explicit independent grouping {i}')
        with CaptureQueriesContext(connection) as captured:
            rows=self.rows('confirmed_groups')
        self.assertEqual(rows['count'],22);self.assertEqual(len(rows['results']),20);self.assertLess(len(captured),20)
        self.assertEqual(len(self.rows('confirmed_groups','&page=2')['results']),2)

    def test_officer_cannot_infer_counts_or_export_and_auditor_is_read_only(self):
        group,data=self.group()
        for user in [self.officer,self.other]:
            self.client.force_authenticate(user)
            for path in ['/api/incident-summary','/api/incident-summary/records','/api/incident-summary.csv',f'/api/incident-groups/{group["id"]}',f'/api/incident-groups/{group["id"]}/history',f'/api/cases?incident_group={group["id"]}']:
                self.assertEqual(self.client.get(path).status_code,403,path)
        self.client.force_authenticate(self.auditor);self.assertEqual(self.counts()['grouped_cases'],2)
        self.assertEqual(self.client.patch('/api/incident-groups/'+group['id'],{**data,'expected_version':1},format='json').status_code,403)

    def coordination_data(self,group):
        return {'submission_id':str(uuid.uuid4()),'institution':str(self.institution.pk),'incident_group':group['id'],'expected_group_version':group['version'],
            'cases':[str(self.case.pk),str(self.hidden.pk)],'lead_bureau':'RB','lead_officer':self.officer.pk,'reason':'Avoid independent duplicate official requests',
            'participants':[{'bureau':'RB','officer':self.officer.pk,'instruction':'Inspect source evidence'},{'bureau':'PGRC','officer':self.other.pk,'instruction':'Coordinate the response'}]}

    def test_coordination_snapshots_reviewed_group_and_does_not_change_case_lifecycle(self):
        group,_=self.group();data=self.coordination_data(group)
        r=self.client.post('/api/coordination-records',data,format='json');self.assertEqual(r.status_code,201,r.data)
        self.assertEqual((r.data['incident_group_id'],r.data['incident_group_version']),(group['id'],1))
        self.assertEqual(self.client.post('/api/coordination-records',data,format='json').status_code,200)
        self.assertEqual(self.client.get('/api/coordination-records?incident_group='+group['id']).data['count'],1)
        self.case.refresh_from_db();self.assertEqual(self.case.status,'registered')
        record=CoordinationRecord.objects.get(pk=r.data['id'])
        with self.assertRaises(DatabaseError),transaction.atomic():
            CoordinationRecord.objects.filter(pk=record.pk).update(incident_group_version=2)

    def test_stale_group_cannot_silently_open_coordination(self):
        group,data=self.group();payload=self.coordination_data(group)
        self.client.patch('/api/incident-groups/'+group['id'],{**data,'expected_version':1,'reason':'Updated evidence'},format='json')
        r=self.client.post('/api/coordination-records',payload,format='json');self.assertEqual(r.status_code,409)
        self.assertFalse(CoordinationRecord.objects.exists())

    def test_literal_extended_fact_types_preserve_source_and_unknown_year(self):
        text=self.case.description
        for kind in ['academic_year','allegation','topic']:
            data={'submission_id':str(uuid.uuid4()),'kind':kind,'source_field':'description','span_start':0,'span_end':len(text),
                'quote':text,'value':text,'source_digest':hashlib.sha256(text.encode()).hexdigest()}
            r=self.client.post(f'/api/cases/{self.case.pk}/facts',data,format='json');self.assertEqual(r.status_code,201,r.data)
            self.assertEqual(r.data['state'],'pending');self.assertEqual(r.data['value'],text)
            data['submission_id']=str(uuid.uuid4());data['value']='Invented incident date 2026-08-01'
            self.assertEqual(self.client.post(f'/api/cases/{self.case.pk}/facts',data,format='json').status_code,400)


@override_settings(ENABLE_INCIDENT_GROUPS=True)
class IncidentConcurrencyTests(TransactionTestCase):
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)

    def test_concurrent_group_corrections_preserve_one_version_and_history(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        from django.contrib.auth.models import User
        WorkflowTests.setUpTestData.__func__(self.__class__)
        client=APIClient();client.force_authenticate(self.coordinator)
        payload={'submission_id':str(uuid.uuid4()),'institution':str(self.institution.pk),'title':'Concurrent group',
            'reason':'Explicitly reviewed synthetic event','cases':[str(self.case.pk),str(self.hidden.pk)]}
        group=client.post('/api/incident-groups',payload,format='json').data
        barrier=Barrier(2)
        def correct(state):
            close_old_connections()
            try:
                c=APIClient();c.force_authenticate(User.objects.get(pk=self.coordinator.pk));barrier.wait(timeout=10)
                return c.patch('/api/incident-groups/'+group['id'],{**payload,'expected_version':1,'state':state,'reason':'Concurrent authorized correction'},format='json').status_code
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(correct,['active','retired']))
        self.assertEqual(sorted(results),[200,409])
        self.assertEqual(IncidentGroup.objects.get(pk=group['id']).version,2)
        self.assertEqual(CaseAction.objects.filter(changes__group_id=group['id']).count(),4)
