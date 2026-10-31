"""Import security, resumability, isolation and reporting regression checks."""
import csv
import io
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .test_workflow import WorkflowTests
from cases.models import ImportJob, SummaryRecord, Complaint
from cases.imports import process_import, parse_file
from cases.exports import build_export

class ImportTests(TestCase):
 def test_optional_classification_defaults_and_validates_imports(self):
  job=self.upload([self.row(classification=''),self.row(source_reference='CLASSIFIED-IMPORT',classification='regulatory_compliance'),self.row(source_reference='BAD-CLASS',classification='not-valid')])
  self.assertEqual(job['counts'],{'ready':2,'rejected':1});self.finish(job)
  self.assertEqual(Complaint.objects.get(source_reference='IMPORT-1').classification,'unclassified')
  self.assertEqual(Complaint.objects.get(source_reference='CLASSIFIED-IMPORT').classification,'regulatory_compliance')
  repeat=self.upload([self.row()]);self.assertEqual(repeat['counts'],{'duplicate':1})
 @classmethod
 def setUpTestData(cls, setup=WorkflowTests.setUpTestData.__func__):
  setup(cls)
 make_user=classmethod(WorkflowTests.make_user.__func__)
 make_case=classmethod(WorkflowTests.make_case.__func__)
 def setUp(self):
  self.client=APIClient();self.client.force_authenticate(self.coordinator)
 def csv(self,rows):
  f=io.StringIO();w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  return SimpleUploadedFile('cases.csv',f.getvalue().encode(),content_type='text/csv')
 def row(self,**extra):
  return {'source_reference':'IMPORT-1','institution_permanent_id':'DEMO-001','bureau':'RB','category':'refunds','summary':'Fee refund withheld.','description':'A fictional imported allegation.','received_at':'2026-01-01T10:00:00+05:30','status':'registered',**extra}
 @patch('cases.serializers.CreateCaseSerializer.validate_summary',lambda self,value:value)
 def upload(self,rows,kind='complaints'):
  res=self.client.post('/api/imports',{'file':self.csv(rows),'kind':kind},format='multipart');self.assertEqual(res.status_code,201,res.data);return res.data
 def finish(self,job):
  result=self.client.post(f"/api/imports/{job['id']}",{'action':'confirm'},format='json');self.assertEqual(result.status_code,200,result.data)
  while ImportJob.objects.get(pk=job['id']).state=='importing':process_import(job['id'])
 def test_import_replay_conflict_report_and_transfer_isolation(self):
  job=self.upload([self.row(),self.row(source_reference='IMPORT-2',institution_permanent_id='MISSING')])
  self.assertEqual(job['counts'],{'ready':1,'rejected':1});self.finish(job)
  case=Complaint.objects.get(source_reference='IMPORT-1');self.assertEqual(case.actions.count(),1)
  process_import(job['id']);self.assertEqual(Complaint.objects.filter(source_reference='IMPORT-1').count(),1)
  report=self.client.get(f"/api/imports/{job['id']}/report");self.assertEqual(report.status_code,200,report.data);self.assertEqual(report.data['total'],1)
  repeat=self.upload([self.row()]);self.assertEqual(repeat['counts'],{'duplicate':1})
  changed=self.upload([self.row(summary='Changed text')]);self.assertEqual(changed['counts'],{'rejected':1})
  self.client.force_authenticate(self.other);self.assertEqual(self.client.get(f"/api/imports/{job['id']}").status_code,404)
 def test_officer_cannot_import_another_bureau_or_read_after_transfer(self):
  self.client.force_authenticate(self.officer)
  rejected=self.upload([self.row(bureau='PGRC')]);self.assertEqual(rejected['counts'],{'rejected':1})
  job=self.upload([self.row()]);self.finish(job)
  Complaint.objects.filter(source_reference='IMPORT-1').update(bureau=self.pg)
  self.assertEqual(self.client.get(f"/api/imports/{job['id']}").status_code,404)
  self.assertEqual(self.client.get(f"/api/dashboard?import_id={job['id']}").status_code,404)
 def test_snapshot_dates_not_summed_and_summaries_do_not_create_cases(self):
  before=Complaint.objects.count()
  common={'institution_permanent_id':'DEMO-001','bureau':'RB','category':'refunds','registered':'10','under_review':'4','awaiting_response':'2','disposed':'3','overdue':'5'}
  job=self.upload([{'snapshot_date':'2026-01-01',**common},{'snapshot_date':'2026-02-01',**common}],'snapshot');self.finish(job)
  data=self.client.get(f"/api/imports/{job['id']}/report").data;self.assertEqual(data['totals']['registered'],10);self.assertEqual(len(data['rows']),1)
  self.assertEqual(Complaint.objects.count(),before);self.assertEqual(SummaryRecord.objects.count(),2)
 def test_unknown_headers_must_be_mapped_and_rejected_rows_export(self):
  row=self.row();row['complaint']=row.pop('summary');job=self.upload([row]);self.assertEqual(job['counts'],{'pending':1})
  self.assertEqual(self.client.post(f"/api/imports/{job['id']}",{'action':'confirm'},format='json').status_code,400)
  mapping={k:k for k in row if k!='complaint'};mapping['summary']='complaint'
  with patch('cases.serializers.CreateCaseSerializer.validate_summary',lambda self,v:v):
   result=self.client.post(f"/api/imports/{job['id']}",{'action':'preview','mapping':mapping},format='json')
  self.assertEqual(result.status_code,200,result.data);self.assertEqual(result.data['counts'],{'ready':1})
 def test_formulas_macros_and_wrong_shapes_rejected(self):
  from openpyxl import Workbook
  from rest_framework.exceptions import ValidationError
  book=Workbook();book.active.append(['summary']);book.active.append(['=1+1']);stream=io.BytesIO();book.save(stream)
  with self.assertRaises(ValidationError):parse_file(SimpleUploadedFile('x.xlsx',stream.getvalue()))
  with self.assertRaises(ValidationError):parse_file(SimpleUploadedFile('x.xlsm',stream.getvalue()))
  with self.assertRaises(ValidationError):parse_file(SimpleUploadedFile('x.csv',b'a,b\n1,2,3'))
  with self.assertRaises(ValidationError):parse_file(SimpleUploadedFile('x.csv',b'a\n@SUM(A1)'))
 def test_disposed_requires_resolution_and_snapshot_overdue_bounds(self):
  job=self.upload([self.row(status='disposed')]);self.assertEqual(job['counts'],{'rejected':1})
  row={'snapshot_date':'2026-01-01','institution_permanent_id':'DEMO-001','bureau':'RB','category':'refunds','registered':'1','under_review':'0','awaiting_response':'0','disposed':'0','overdue':'2'}
  job=self.upload([row],'snapshot');self.assertEqual(job['counts'],{'rejected':1})
 def test_export_permissions_rechecked_after_transfer(self):
  self.client.force_authenticate(self.officer)
  res=self.client.post('/api/exports',{},format='json');self.assertEqual(res.status_code,202,res.data)
  build_export(res.data['id'])
  self.assertEqual(self.client.get(f"/api/exports/{res.data['id']}/download").status_code,200)
  self.make_case(self.rb,'NEW-AFTER-EXPORT')
  self.assertEqual(self.client.get(f"/api/exports/{res.data['id']}/download").status_code,200)
  Complaint.objects.filter(pk=self.case.pk).update(bureau=self.pg)
  self.assertEqual(self.client.get(f"/api/exports/{res.data['id']}/download").status_code,403)
 def test_auditor_read_only_and_confirm_idempotent(self):
  job=self.upload([self.row()]);self.finish(job)
  self.assertEqual(self.client.post(f"/api/imports/{job['id']}",{'action':'confirm'},format='json').status_code,200)
  self.client.force_authenticate(self.auditor)
  self.assertEqual(self.client.get(f"/api/imports/{job['id']}").status_code,200)
  self.assertEqual(self.client.post(f"/api/imports/{job['id']}",{'action':'retry'},format='json').status_code,403)

 def test_valid_excel_date_cells_and_cache_scope(self):
  from datetime import datetime
  from openpyxl import Workbook
  book=Workbook();sheet=book.active
  sheet.append(['snapshot_date','institution_permanent_id','bureau','category','registered','under_review','awaiting_response','disposed','overdue'])
  sheet.append([datetime(2026,1,1),'DEMO-001','RB','refunds',10,4,2,3,1]);stream=io.BytesIO();book.save(stream)
  res=self.client.post('/api/imports',{'file':SimpleUploadedFile('valid.xlsx',stream.getvalue()),'kind':'snapshot'},format='multipart')
  self.assertEqual(res.status_code,201,res.data);self.assertEqual(res.data['counts'],{'ready':1})
  initial=self.client.get('/api/dashboard');self.assertEqual(initial.data['pending'],2)
  from django.core.cache import caches
  caches['default'].set('throttle-sentinel',123)
  self.case.status='disposed';self.case.save(update_fields=['status'])
  self.assertEqual(caches['default'].get('throttle-sentinel'),123)
  self.assertEqual(self.client.get('/api/dashboard').data['pending'],1)
  self.client.force_authenticate(self.other)
  scoped=self.client.get('/api/dashboard').data
  self.assertEqual(scoped['total'],1);self.assertEqual(scoped['recent'][0]['id'],str(self.hidden.pk))

 def test_summary_import_hidden_after_membership_changes(self):
  self.client.force_authenticate(self.officer)
  row={'snapshot_date':'2026-01-01','institution_permanent_id':'DEMO-001','bureau':'RB','category':'refunds','registered':'1','under_review':'0','awaiting_response':'0','disposed':'0','overdue':'0'}
  job=self.upload([row],'snapshot');self.finish(job)
  self.officer.membership.bureau=self.pg;self.officer.membership.save()
  self.assertEqual(self.client.get(f"/api/imports/{job['id']}").status_code,404)
  self.assertEqual(self.client.get(f"/api/imports/{job['id']}/report").status_code,404)
  self.officer.membership.bureau=None;self.officer.membership.save()
  self.assertEqual(self.client.get('/api/imports').data,[])

class DashboardTests(TestCase):
 setUpTestData=classmethod(ImportTests.setUpTestData.__func__)
 make_user=classmethod(ImportTests.make_user.__func__)
 make_case=classmethod(ImportTests.make_case.__func__)
 setUp=ImportTests.setUp
 def test_attention_deadline_order_filters_and_role_scope(self):
  early=self.make_case(self.rb,'EARLY')
  early.due_at=timezone.now()-__import__('datetime').timedelta(days=10);early.save()
  data=self.client.get('/api/dashboard?bureau=RB').data
  self.assertEqual([c['reference'] for c in data['attention']],['EARLY','A'])
  self.assertEqual(data['pending'],2)
  self.assertEqual(sum(c['count'] for c in data['active_categories']),2)
  self.case.status='disposed';self.case.save()
  self.assertEqual(len(self.client.get('/api/dashboard?bureau=RB').data['attention']),1)
  self.client.force_authenticate(self.other)
  data=self.client.get('/api/dashboard').data
  self.assertEqual([c['reference'] for c in data['attention']],['B'])
  self.assertNotIn('overlap_reviews',data);self.assertNotIn('coordination_notices',data)
 def test_transfer_and_closure_refresh_dashboard_and_preserve_audit(self):
  response=self.client.post(f'/api/cases/{self.case.pk}/actions',{'kind':'transfer','bureau':'PGRC','reason':'Coordinate with grievance cell','expected_version':1},format='json')
  self.assertEqual(response.status_code,200,response.data)
  self.assertEqual(self.client.get('/api/dashboard?bureau=RB').data['pending'],0)
  self.assertEqual(self.client.get('/api/dashboard?bureau=PGRC').data['pending'],2)
  response=self.client.post(f'/api/cases/{self.case.pk}/actions',{'kind':'status','status':'disposed','reason':'Resolution recorded after review','expected_version':2},format='json')
  self.assertEqual(response.status_code,200,response.data)
  data=self.client.get('/api/dashboard?bureau=PGRC').data
  self.assertEqual(data['pending'],1);self.assertEqual(data['disposed'],1)
  self.assertNotIn(str(self.case.pk),[c['id'] for c in data['attention']])
  self.assertEqual(self.case.actions.count(),2)

 def test_overlap_filters_reuse_case_scope_and_review_keeps_histories(self):
  from cases.models import Institution,OverlapCandidate,CaseAction
  inst=Institution.objects.create(name='Other fictional college',permanent_id='OTHER',region='North',district='Demo')
  a=self.make_case(self.rb,'PAIR-A');b=self.make_case(self.pg,'PAIR-B')
  a.institution=inst;a.save();b.institution=inst;b.save()
  def pair(a,b):
   left,right=sorted([a.pk,b.pk]);return OverlapCandidate.objects.create(left_id=left,right_id=right,score=.9,model_revision='test')
  original=pair(self.case,self.hidden);other=pair(a,b)
  result=self.client.get(f'/api/overlaps?institution={inst.pk}&category=refunds').data
  self.assertEqual(result['count'],1);self.assertEqual(result['results'][0]['id'],other.pk)
  self.assertEqual(self.client.get('/api/overlaps?institution=invalid').status_code,400)
  self.client.post(f'/api/overlaps/{other.pk}/review',{'decision':'related_issue','reason':'Different remedies at one institution','expected_version':1},format='json')
  self.assertEqual(self.client.get(f'/api/dashboard?institution={inst.pk}').data['overlap_reviews'],0)
  self.assertEqual(CaseAction.objects.filter(case__in=[a,b],kind='overlap_review').count(),2)
  self.client.force_authenticate(self.auditor)
  self.assertEqual(self.client.get(f'/api/overlaps?institution={inst.pk}&decision=all').data['count'],1)
  self.assertEqual(self.client.post(f'/api/overlaps/{original.pk}/review',{'decision':'unrelated','reason':'Read only','expected_version':1},format='json').status_code,403)
  self.client.force_authenticate(self.officer)
  self.assertEqual(self.client.get('/api/overlaps').status_code,403)

class RolloutTests(TestCase):
 setUpTestData=classmethod(ImportTests.setUpTestData.__func__)
 make_user=classmethod(ImportTests.make_user.__func__)
 make_case=classmethod(ImportTests.make_case.__func__)
 setUp=ImportTests.setUp
 csv=ImportTests.csv
 row=ImportTests.row
 upload=ImportTests.upload
 finish=ImportTests.finish
 def test_matching_counts_include_every_record(self):
  from cases.imports import job_data
  job=self.upload([self.row(source_reference='COUNT-1'),self.row(source_reference='COUNT-2')]);self.finish(job)
  Complaint.objects.filter(importrow__job_id=job['id']).update(matching_state='complete')
  self.assertEqual(job_data(ImportJob.objects.get(pk=job['id']))['matching'],{'complete':2})
 def test_model_swap_rollback_and_approval_gate(self):
  from django.core.management.base import CommandError
  from cases.models import ModelRelease,StagedEmbedding,OverlapCandidate
  from cases.management.commands.model_release import swap_release
  a=[1.0]+[0.0]*383;b=[0.0,1.0]+[0.0]*382
  baseline=ModelRelease.objects.create(revision='baseline-test',path='minilm',threshold=.7,active=True,approved=True)
  candidate=ModelRelease.objects.create(revision='candidate-test',path='candidate',threshold=.8)
  for case in [self.case,self.hidden]:
   case.embedding=a;case.model_revision=baseline.revision;case.save()
   StagedEmbedding.objects.create(case=case,revision=baseline.revision,embedding=a)
   StagedEmbedding.objects.create(case=case,revision=candidate.revision,embedding=b)
  left,right=sorted([self.case.pk,self.hidden.pk]);pair=OverlapCandidate.objects.create(left_id=left,right_id=right,score=.9,model_revision='baseline-test',decision='unrelated',reason='Human reviewed')
  with self.assertRaises(CommandError):swap_release(candidate)
  candidate.approved=True;candidate.save();swap_release(candidate)
  self.case.refresh_from_db();self.assertEqual(self.case.model_revision,'candidate-test');self.assertEqual(float(self.case.embedding[1]),1)
  pair.refresh_from_db();self.assertEqual(pair.reason,'Human reviewed');self.assertEqual(pair.model_revision,'baseline-test')
  swap_release(baseline);self.case.refresh_from_db();self.assertEqual(self.case.model_revision,'baseline-test');self.assertEqual(float(self.case.embedding[0]),1)
 def test_resume_import_from_committed_checkpoint(self):
  job=self.upload([self.row(source_reference=f'RESUME-{n}') for n in range(251)])
  self.client.post(f"/api/imports/{job['id']}",{'action':'confirm'},format='json')
  process_import(job['id']);self.assertEqual(Complaint.objects.filter(importrow__job_id=job['id']).count(),250)
  process_import(job['id']);process_import(job['id'])
  self.assertEqual(Complaint.objects.filter(importrow__job_id=job['id']).count(),251)
  self.assertEqual(ImportJob.objects.get(pk=job['id']).rows.filter(state='imported').count(),251)

# Imported fixture class is not a second test suite.
del WorkflowTests
