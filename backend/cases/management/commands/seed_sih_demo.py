"""Stable presentation records; repeating this command never resets played decisions."""
import io
import json
import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django_q.tasks import async_task
from rest_framework.test import APIClient
from cases.models import Institution,Bureau,Complaint,CaseAction,Attachment


class Command(BaseCommand):
    help='Prepare SIH-26264-DEMO and four fixed-reference fictional cases without resetting existing work.'
    def handle(self,*args,**options):
        try:
            coordinator=User.objects.get(username='coordinator')
            bureaus={b.code:b for b in Bureau.objects.filter(code__in=['RB','PGRC','DEMO'])}
            if len(bureaus)!=3:raise User.DoesNotExist()
        except User.DoesNotExist:raise CommandError('Run seed_demo first to prepare the standard demo accounts/reference data.')
        now=timezone.now();rows=[]
        specs=[('REFUND-RB','RB','refunds','grievance','under_review',23,
                'Refund request DEMO-RF-26 for the September 2026 diploma withdrawal remains unpaid. The applicant requests repayment.',
                'Await bank payment evidence','officer_rb'),
               ('REFUND-PGRC','PGRC','refunds','grievance','registered',1,
                'The diploma applicant who withdrew in September 2026 has still not received the repayment requested under DEMO-RF-26.',
                '','officer_pgrc'),
               ('LAB-DEMO','DEMO','facilities','regulatory_compliance','awaiting_response',40,
                'The mechanical laboratory emergency exit is locked and a safety inspection response is required.',
                'Request signed safety inspection report','officer_demo'),
               ('DOCUMENTS-CLOSED','RB','documents','unclassified','disposed',50,
                'Original academic documents were retained after transfer; the documents have now been returned.',
                '','officer_rb')]
        with transaction.atomic():
            inst,_=Institution.objects.get_or_create(permanent_id='SIH-26264-DEMO',defaults={'name':'Lotus Technical Institute · fictional SIH demonstration','region':'Southern','district':'Showcase district','address':'Fictional demonstration campus; not an AICTE institution'})
            Institution.objects.select_for_update().get(pk=inst.pk)
            for suffix,code,category,classification,status,days,summary,next_action,officer in specs:
                ref='SIH-26264-'+suffix;received=now-timedelta(days=days)
                case,created=Complaint.objects.get_or_create(source_system='sih-demo',source_reference=ref,defaults={
                    'id':uuid.uuid5(uuid.NAMESPACE_URL,ref),'submission_id':uuid.uuid5(uuid.NAMESPACE_DNS,ref),'reference':ref,
                    'institution':inst,'bureau':bureaus[code],'category':category,'classification':classification,
                    'summary':summary,'description':'Prepared fictional SIH demonstration record. No real complainant or institution data.',
                    'created_by':coordinator,'assigned_to':User.objects.get(username=officer),'received_at':received,
                    'due_at':received+timedelta(days=30),'status':status,'disposed_at':now-timedelta(days=15) if status=='disposed' else None,
                    'next_action':next_action,'next_action_date':timezone.localdate()+timedelta(days=2) if next_action else None})
                if created:
                    CaseAction.objects.create(case=case,actor=coordinator,kind='registered',reason='Prepared synthetic SIH demonstration',changes={'bureau':code,'classification':classification},created_at=received)
                    if status!='registered':CaseAction.objects.create(case=case,actor=coordinator,kind='status',reason='Prepared fictional case history',changes={'status':{'before':'registered','after':status}},created_at=case.disposed_at or received+timedelta(hours=1))
                    if next_action:CaseAction.objects.create(case=case,actor=coordinator,kind='next_action',reason='Prepared follow-up task',changes={'next_action':{'before':'','after':next_action},'next_action_date':{'before':None,'after':case.next_action_date.isoformat()}},created_at=received+timedelta(hours=2))
                    async_task('cases.matching.match_case',str(case.pk))
                rows.append({'id':str(case.pk),'reference':case.reference,'initial_or_current_status':case.status})
        first=Complaint.objects.get(pk=rows[0]['id'])
        if not Attachment.objects.filter(case=first,original_name='SIH synthetic receipt.pdf').exists():
            from pypdf import PdfWriter
            pdf=PdfWriter();pdf.add_blank_page(width=300,height=200);content=io.BytesIO();pdf.write(content)
            client=APIClient();client.force_authenticate(coordinator)
            response=client.post(f'/api/cases/{first.pk}/attachments',{'file':SimpleUploadedFile('SIH synthetic receipt.pdf',content.getvalue(),content_type='application/pdf')},format='multipart')
            if response.status_code!=201:raise CommandError(str(response.data))
        manifest={'permanent_id':inst.permanent_id,'institution_id':str(inst.pk),'cases':rows,'accounts':['coordinator','auditor','officer_rb','officer_pgrc','officer_demo'],'provenance':'Fictional, deterministic demonstration fixtures. Re-running preserves all subsequent decisions and actions.'}
        (settings.RESULTS_DIR/'sih-demo.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        self.stdout.write('SIH-26264-DEMO ready. Existing demonstration decisions were preserved.')
