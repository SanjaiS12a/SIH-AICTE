import hashlib
import uuid
from unittest.mock import patch
from django.core.management import call_command
from django.db import connection, transaction, DatabaseError
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from cases.models import CaseAction, Complaint, ReviewedFact, IncidentGroup, IncidentMembership, Institution
from cases.shadow import discover
from .test_workflow import WorkflowTests


@override_settings(ENABLE_REVIEWED_FACTS=True, ENABLE_INCIDENT_GROUPS=True)
class IntelligenceTests(TestCase):
    setUpTestData = classmethod(WorkflowTests.setUpTestData.__func__)
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)

    def setUp(self):
        self.client = APIClient(); self.client.force_authenticate(self.coordinator)

    def post(self, url, data):
        return self.client.post(url, data, format='json')

    def fact_data(self, **changes):
        text = self.case.summary
        return {'submission_id':str(uuid.uuid4()),'kind':'remedy','source_field':'summary', 'span_start':0,
            'span_end':len(text),'quote':text,'source_digest':hashlib.sha256(text.encode()).hexdigest(),'value':text, **changes}

    def create_fact(self, **changes):
        response = self.post(f'/api/cases/{self.case.pk}/facts',self.fact_data(**changes))
        self.assertEqual(response.status_code,201,response.data)
        return response.data

    def group_data(self, **changes):
        return {'submission_id':str(uuid.uuid4()),'institution':str(self.institution.pk),'title':'Explicit reviewed incident',
            'reason':'Independent records remain separate','cases':[str(self.case.pk),str(self.hidden.pk)], **changes}

    def create_group(self, **changes):
        response = self.post('/api/incident-groups',self.group_data(**changes))
        self.assertEqual(response.status_code,201,response.data)
        return response.data

    def test_brief_authoritative_and_current_after_transfer(self):
        url = f'/api/cases/{self.case.pk}/brief'
        self.assertEqual(self.client.get(url).data['case']['bureau'],'RB')
        response = self.post(f'/api/cases/{self.case.pk}/actions',{'kind':'transfer','bureau':'PGRC','reason':'Destination responsibility','expected_version':1})
        self.assertEqual(response.status_code,200)
        result = self.client.get(url).data
        self.assertEqual(result['case']['bureau'],'PGRC')
        self.assertEqual(result['latest_action']['bureau_at_action'],'PGRC')
        self.assertIn('allegation',result['allegation_label'])

    def test_brief_officer_has_no_relationship_metadata_and_revokes_current_scope(self):
        self.client.force_authenticate(self.officer)
        url = f'/api/cases/{self.case.pk}/brief'
        self.assertNotIn('relationship_status',self.client.get(url).data)
        self.assertEqual(self.client.get(f'/api/cases/{self.hidden.pk}/brief').status_code,404)
        self.officer.membership.bureau=self.pg; self.officer.membership.save()
        self.assertEqual(self.client.get(url).status_code,404)
        self.officer.is_active=False; self.officer.save()
        self.assertEqual(self.client.get(f'/api/cases/{self.hidden.pk}/brief').status_code,404)

    def test_history_is_server_paginated_beyond_twenty(self):
        CaseAction.objects.bulk_create([CaseAction(case=self.case,actor=self.coordinator,kind='note',reason=f'Action {n}') for n in range(25)])
        response=self.client.get(f'/api/cases/{self.case.pk}/history')
        self.assertEqual(response.data['count'],25); self.assertEqual(len(response.data['results']),20)
        self.assertEqual(len(self.client.get(f'/api/cases/{self.case.pk}/history?page=2').data['results']),5)

    def test_feature_flags_default_to_hidden(self):
        with override_settings(ENABLE_REVIEWED_FACTS=False,ENABLE_INCIDENT_GROUPS=False):
            self.assertEqual(self.client.get(f'/api/cases/{self.case.pk}/facts').status_code,404)
            self.assertEqual(self.client.get('/api/incident-groups').status_code,404)

    def test_fact_proposal_idempotency_evidence_and_audit(self):
        d=self.fact_data(); url=f'/api/cases/{self.case.pk}/facts'
        self.assertEqual(self.post(url,d).status_code,201)
        self.assertEqual(self.post(url,d).status_code,200)
        d['value']='An invented remedy'; self.assertEqual(self.post(url,d).status_code,400)
        self.assertEqual(ReviewedFact.objects.count(),1); self.assertEqual(self.case.actions.count(),1)
        self.case.refresh_from_db(); self.assertEqual(self.case.summary,'Fee refund was withheld.')

    def test_fact_invalid_span_digest_and_ambiguous_date(self):
        url=f'/api/cases/{self.case.pk}/facts'
        for change, code in [({'quote':'Fabrication'},400),({'span_end':99999},400),({'source_digest':'0'*64},409),({'kind':'incident_date'},400)]:
            self.assertEqual(self.post(url,self.fact_data(**change)).status_code,code)
        self.assertFalse(ReviewedFact.objects.exists()); self.assertFalse(CaseAction.objects.exists())

    def test_iso_date_and_unicode_span_keep_original_allegation(self):
        text='Fictional claim 📚 on 2026-08-01; repayment requested.'
        Complaint.objects.filter(pk=self.case.pk).update(description=text)
        start=text.index('2026-08-01')
        response=self.post(f'/api/cases/{self.case.pk}/facts',self.fact_data(kind='incident_date',source_field='description',span_start=start,span_end=start+10,
            quote='2026-08-01',value='2026-08-01',source_digest=hashlib.sha256(text.encode()).hexdigest()))
        self.assertEqual(response.status_code,201,response.data)
        url=f'/api/cases/{self.case.pk}/facts/{response.data["id"]}/review'
        self.assertEqual(self.post(url,{'expected_version':1,'state':'accepted','reason':'Exact ISO source date reviewed'}).status_code,200)
        self.case.refresh_from_db(); self.assertIsNone(self.case.incident_date);self.assertEqual(self.case.description,text)
        invalid=self.fact_data();invalid['quote']='Fabricated source'
        with self.assertRaises(DatabaseError),transaction.atomic():
            ReviewedFact.objects.create(case=self.case,proposed_by=self.coordinator,**invalid)

    def test_fact_review_stale_correction_and_readonly_roles(self):
        fact=self.create_fact(); url=f'/api/cases/{self.case.pk}/facts/{fact["id"]}/review'
        data={'expected_version':1,'state':'accepted','reason':'Reviewed exact source span'}
        self.assertEqual(self.post(url,data).status_code,200)
        self.assertEqual(self.post(url,data).status_code,409)
        self.assertEqual(self.post(url,{**data,'expected_version':2,'state':'rejected','reason':'Compensating correction'}).status_code,200)
        self.assertEqual(self.case.actions.count(),3)
        for user in [self.officer,self.auditor]:
            self.client.force_authenticate(user); self.assertEqual(self.post(url,{**data,'expected_version':3}).status_code,403)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.post(f'/api/cases/{self.case.pk}/facts',self.fact_data()).status_code,403)

    def test_officer_can_propose_only_current_bureau(self):
        self.client.force_authenticate(self.officer); self.create_fact()
        self.assertEqual(self.post(f'/api/cases/{self.hidden.pk}/facts',self.fact_data()).status_code,404)

    def test_fact_database_protects_original_and_delete(self):
        fact=self.create_fact()
        for sql in ['UPDATE cases_reviewedfact SET quote=%s WHERE id=%s','DELETE FROM cases_reviewedfact WHERE quote=%s AND id=%s']:
            with self.assertRaises(DatabaseError), transaction.atomic():
                with connection.cursor() as cursor: cursor.execute(sql,['changed',fact['id']]) if sql.startswith('UPDATE') else cursor.execute(sql,[fact['quote'],fact['id']])

    def test_groups_explicit_same_institution_and_versioned_membership(self):
        d=self.group_data(); response=self.post('/api/incident-groups',d); self.assertEqual(response.status_code,201,response.data)
        group=response.data
        self.assertEqual(self.post('/api/incident-groups',d).status_code,200)
        third=self.make_case(self.rb,'C')
        update={**d,'expected_version':1,'cases':[str(self.case.pk),str(third.pk)],'reason':'Correct explicit membership'}
        url=f'/api/incident-groups/{group["id"]}'
        self.assertEqual(self.client.patch(url,update,format='json').status_code,200)
        self.assertEqual(self.client.patch(url,update,format='json').status_code,409)
        self.assertFalse(IncidentMembership.objects.get(group_id=group['id'],case=self.hidden).active)
        self.assertEqual(IncidentMembership.objects.filter(group_id=group['id']).count(),3)
        snapshot=self.case.actions.order_by('-id').first().changes['profile']
        self.assertEqual(snapshot['before']['version'],1); self.assertEqual(snapshot['after']['version'],2)
        self.case.refresh_from_db(); self.assertEqual(self.case.version,1)

    def test_group_cross_institution_rejected_without_partial_records(self):
        inst=Institution.objects.create(name='Other institution',permanent_id='OTHER',region='North',district='Demo')
        Complaint.objects.filter(pk=self.hidden.pk).update(institution=inst)
        response=self.post('/api/incident-groups',self.group_data())
        self.assertEqual(response.status_code,400); self.assertFalse(IncidentGroup.objects.exists())

    def test_group_support_requires_same_incident_and_flags_review_after_change(self):
        pair=self.post('/api/relationships',{'left':str(self.case.pk),'right':str(self.hidden.pk),'decision':'related_issue','reason':'Related matters'}).data
        response=self.post('/api/incident-groups',self.group_data(supporting_relationship=pair['id']))
        self.assertEqual(response.status_code,400)
        pair=self.post(f'/api/overlaps/{pair["id"]}/review',{'decision':'same_incident','reason':'Reviewed as same event','expected_version':pair['version']}).data
        group=self.create_group(supporting_relationship=pair['id'])
        response=self.post(f'/api/overlaps/{pair["id"]}/review',{'decision':'unrelated','reason':'Corrected on stronger evidence','expected_version':pair['version']})
        self.assertEqual(response.status_code,200,response.data)
        obj=IncidentGroup.objects.get(pk=group['id']); self.assertTrue(obj.needs_review); self.assertEqual(obj.version,2)
        self.assertEqual(obj.memberships.filter(active=True).count(),2)

    def test_group_histories_exports_and_counts_are_hidden_from_officers(self):
        group=self.create_group()
        self.client.force_authenticate(self.officer)
        self.assertEqual(self.client.get(f'/api/incident-groups?institution={self.institution.pk}').status_code,403)
        for url in [f'/api/cases/{self.case.pk}',f'/api/cases/{self.case.pk}/history',f'/api/institutions/{self.institution.pk}/history','/api/movements']:
            response=self.client.get(url); self.assertEqual(response.status_code,200,response.data)
            self.assertNotIn(group['id'],str(response.data)); self.assertNotIn('coordination_group',str(response.data))
        response=self.client.get('/api/movements.csv')
        content=b''.join(response.streaming_content).decode()
        self.assertNotIn(group['id'],content); self.assertNotIn('coordination_group',content)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.client.get(f'/api/incident-groups?institution={self.institution.pk}').data['count'],1)
        self.assertEqual(self.post('/api/incident-groups',self.group_data()).status_code,403)

    def test_group_database_integrity_and_protected_history(self):
        group=self.create_group()
        inst=Institution.objects.create(name='Other',permanent_id='OTHER',region='North',district='Demo')
        for query,values in [('DELETE FROM cases_incidentmembership WHERE group_id=%s',[group['id']]),
                             ('UPDATE cases_complaint SET institution_id=%s WHERE id=%s',[str(inst.pk),str(self.case.pk)]),
                             ('DELETE FROM cases_incidentgroup WHERE id=%s',[group['id']])]:
            with self.assertRaises(DatabaseError),transaction.atomic():
                with connection.cursor() as cursor: cursor.execute(query,values)

    @patch('cases.shadow.runtime',return_value=(None,'test-revision',0.6))
    @override_settings(SHADOW_RETRIEVAL_ENABLED=True)
    def test_shadow_lexical_reference_bounds_unknown_cosine_and_isolation(self, runtime):
        self.hidden.source_reference=self.case.source_reference; self.hidden.source_system='other'; self.hidden.save()
        result=discover(self.coordinator,self.case,budget=1)
        self.assertEqual(len(result['candidates']),1)
        self.assertIsNone(result['candidates'][0]['cosine'])
        self.assertFalse(result['candidates'][0]['passes_semantic_cutoff'])
        self.assertIn('reference',result['candidates'][0]['methods'])
        self.assertIn('to_tsvector',result['plans']['lexical'])
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied): discover(self.officer,self.case)
        self.assertEqual(discover(self.coordinator,self.case,reference_ids=[])['candidates'],[])

    def test_shadow_disabled_and_fresh_only_seeding(self):
        from rest_framework.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied): discover(self.coordinator,self.case)
        with patch('cases.management.commands.seed_if_empty.call_command') as command:
            call_command('seed_if_empty'); command.assert_not_called()


@override_settings(ENABLE_REVIEWED_FACTS=True)
class IntelligenceConcurrencyTests(TransactionTestCase):
    make_user = classmethod(WorkflowTests.make_user.__func__)
    make_case = classmethod(WorkflowTests.make_case.__func__)

    def test_simultaneous_reviews_serialize_and_one_returns_conflict(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        from django.contrib.auth.models import User
        WorkflowTests.setUpTestData.__func__(self.__class__)
        client=APIClient();client.force_authenticate(self.coordinator)
        text=self.case.summary
        data={'submission_id':str(uuid.uuid4()),'kind':'remedy','source_field':'summary','span_start':0,'span_end':len(text),
              'quote':text,'source_digest':hashlib.sha256(text.encode()).hexdigest(),'value':text}
        response=client.post(f'/api/cases/{self.case.pk}/facts',data,format='json')
        self.assertEqual(response.status_code,201,response.data)
        barrier=Barrier(2)
        def review(state):
            close_old_connections()
            try:
                actor=User.objects.get(pk=self.coordinator.pk); c=APIClient();c.force_authenticate(actor)
                barrier.wait(timeout=10)
                return c.post(f'/api/cases/{self.case.pk}/facts/{response.data["id"]}/review',
                    {'expected_version':1,'state':state,'reason':'Concurrent source review'},format='json').status_code
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(review,['accepted','rejected']))
        self.assertEqual(sorted(results),[200,409])
        self.assertEqual(CaseAction.objects.filter(kind='fact_reviewed').count(),1)
