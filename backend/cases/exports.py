"""Asynchronous, private CSV exports with permission revalidation at download."""
import csv
import hashlib
import io
from pathlib import Path
from types import SimpleNamespace
from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_q.tasks import async_task
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from .access import filtered_cases, role, coordination, scoped_cases
from .models import ReportExport, AuditEvent
from .serializers import FilterSerializer

def query(job):
 return filtered_cases(SimpleNamespace(user=job.owner,query_params=job.filters))

def scope_hash(qs):
 result=hashlib.sha256()
 for case_id in qs.order_by('id').values_list('id',flat=True).iterator(chunk_size=2000): result.update(str(case_id).encode())
 return result.hexdigest()

def safe(value):
 value=str(value)
 return "'"+value if value.lstrip().startswith(('=','+','-','@','\t','\r')) else value

@api_view(['POST'])
def exports(request):
 form=FilterSerializer(data=request.data);form.is_valid(raise_exception=True)
 # Validate import ownership before creating durable work.
 filtered_cases(SimpleNamespace(user=request.user,query_params=request.data))
 if role(request.user) not in ('officer','coordinator','auditor'): raise PermissionDenied()
 with transaction.atomic():
  job=ReportExport.objects.create(owner=request.user,filters=dict(request.data))
  async_task('cases.exports.build_export',str(job.pk))
 return Response({'id':str(job.pk),'state':job.state},status=202)

def build_export(export_id):
 job=ReportExport.objects.select_related('owner').get(pk=export_id)
 path=Path(settings.MEDIA_ROOT)/'reports'/f'{job.pk}.csv'
 path.parent.mkdir(parents=True,exist_ok=True)
 try:
  qs=query(job); initial=scope_hash(qs)
  with path.open('w',encoding='utf-8-sig',newline='') as f:
   writer=csv.writer(f);writer.writerow(['Reference','Institution','Permanent ID','Bureau','Category','Status','Received','Due','Classification','Next action','Expected action date'])
   for c in qs.iterator(chunk_size=1000): writer.writerow([safe(x) for x in [c.reference,c.institution.name,c.institution.permanent_id,c.bureau.code,c.category,c.status,c.received_at.isoformat(),c.due_at.isoformat(),c.classification,c.next_action,c.next_action_date.isoformat() if c.next_action_date else '']])
  if scope_hash(query(job))!=initial: raise ValueError('Case access changed during export; request a new report.')
  job.scope_hash=initial;job.file.name=f'reports/{job.pk}.csv';job.state='complete';job.error='';job.save()
 except Exception:
  path.unlink(missing_ok=True)
  job.state='failed';job.error='Export failed or access changed; request a new report.';job.save()
  raise

def get_export(user,export_id):
 return get_object_or_404(ReportExport,pk=export_id,owner=user)

@api_view(['GET'])
def export_detail(request,export_id):
 job=get_export(request.user,export_id)
 return Response({'id':str(job.pk),'state':job.state,'error':job.error})

def authorized_file(job,user):
 if coordination(user):return True
 permitted=scoped_cases(user)
 try:
  with job.file.storage.open(job.file.name,'rb') as binary:
   reader=csv.reader(io.TextIOWrapper(binary,encoding='utf-8-sig',newline=''));next(reader,None);references=[]
   for row in reader:
    if not row:return False
    references.append(row[0])
    if len(references)==1000:
     if permitted.filter(reference__in=references).count()!=len(set(references)):return False
     references=[]
   return not references or permitted.filter(reference__in=references).count()==len(set(references))
 except OSError:raise ValidationError('Report file is unavailable; generate a new report.')

@api_view(['GET'])
def export_download(request,export_id):
 job=get_export(request.user,export_id)
 if job.state!='complete': raise ValidationError('Report is not ready.')
 if not request.user.is_active or role(request.user) not in ('officer','coordinator','auditor') or not authorized_file(job,request.user): raise PermissionDenied('Case access changed; generate a fresh report.')
 AuditEvent.objects.create(actor=request.user,kind='export',detail={'export':str(job.pk),'filters':job.filters})
 return FileResponse(job.file.open('rb'),as_attachment=True,filename='case-report.csv')
