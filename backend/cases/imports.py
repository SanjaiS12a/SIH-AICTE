"""Validated, resumable spreadsheet ingestion. Source rows never replace allegations."""
import csv
import hashlib
import io
import json
import uuid
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_q.tasks import async_task
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .access import role, scoped_cases, writable, coordination
from .models import ImportJob, ImportRow, SummaryRecord, Institution, Bureau, Complaint, CaseAction, AuditEvent
from .serializers import CreateCaseSerializer

FIELDS = {
 'complaints': ['source_reference','institution_permanent_id','bureau','category','summary','description','received_at','status','incident_date','due_at','disposed_at','resolution_note','source_system'],
 'monthly': ['month','institution_permanent_id','bureau','category','received','disposed'],
 'snapshot': ['snapshot_date','institution_permanent_id','bureau','category','registered','under_review','awaiting_response','disposed','overdue'],
}
REQUIRED = {'complaints': FIELDS['complaints'][:8], 'monthly': FIELDS['monthly'], 'snapshot': FIELDS['snapshot']}
MAX_ROWS = 10000

def digest(value):
 return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

def cell(value):
 if isinstance(value, datetime) and not any([value.hour,value.minute,value.second,value.microsecond]): return value.date().isoformat()
 if isinstance(value, (date, datetime)): return value.isoformat()
 return '' if value is None else str(value).strip()

def parse_file(file):
 if file.size > 20 * 1024 * 1024: raise ValidationError('Maximum upload size is 20 MB.')
 suffix = Path(file.name).suffix.lower()
 try:
  if suffix == '.csv':
   raw = file.read().decode('utf-8-sig')
   if '\x00' in raw: raise ValueError('Null bytes are not allowed.')
   reader = csv.reader(io.StringIO(raw), strict=True)
   rows = []
   for row in reader:
    rows.append(row)
    if len(rows) > MAX_ROWS + 1: raise ValueError('Maximum 10,000 data rows.')
  elif suffix == '.xlsx':
   from openpyxl import load_workbook
   with zipfile.ZipFile(file) as archive:
    if len(archive.infolist()) > 2000 or sum(x.file_size for x in archive.infolist()) > 80 * 1024 * 1024:
     raise ValueError('Workbook expands beyond the safe limit.')
    if any('vbaproject' in x.filename.lower() or 'externallinks/' in x.filename.lower() for x in archive.infolist()):
     raise ValueError('Macros and external workbook links are not supported.')
   file.seek(0)
   book = load_workbook(file, read_only=True, data_only=False, keep_links=False)
   try:
    if len(book.worksheets) != 1: raise ValueError('Upload one data sheet at a time.')
    sheet = book.worksheets[0]
    if (sheet.max_row or 0) > MAX_ROWS + 1 or (sheet.max_column or 0) > 80: raise ValueError('Workbook exceeds row or column limits.')
    rows = []
    for row in sheet.iter_rows():
     if any(c.data_type == 'f' for c in row): raise ValueError('Formulas are not accepted; paste values first.')
     rows.append([cell(c.value) for c in row])
     if len(rows) > MAX_ROWS + 1: raise ValueError('Maximum 10,000 data rows.')
   finally: book.close()
  else: raise ValueError('Use .xlsx or UTF-8 .csv; macros and legacy .xls are not supported.')
  if len(rows) < 2: raise ValueError('Include a header and at least one data row.')
  headers = [cell(x) for x in rows[0]]
  if len(headers) > 80 or not all(headers) or len(set(headers)) != len(headers): raise ValueError('Use unique, nonempty headers; maximum 80 columns.')
  result=[]
  for n, row in enumerate(rows[1:], 2):
   if not any(cell(x) for x in row): continue
   if len(row) != len(headers): raise ValueError(f'Row {n}: column count does not match the header.')
   values=[cell(x) for x in row]
   if any(len(x)>12000 or x.lstrip().startswith(('=', '+', '@')) for x in values): raise ValueError(f'Row {n}: formulas or oversized cells are not accepted.')
   result.append((n,dict(zip(headers,values))))
  if not result: raise ValueError('No data rows found.')
  return headers,result
 except (ValueError, UnicodeError, zipfile.BadZipFile, KeyError, OSError, csv.Error) as exc:
  raise ValidationError(str(exc)) from exc
 except Exception as exc:
  raise ValidationError('The workbook is malformed or unsupported.') from exc

def accessible_jobs(user):
 qs=ImportJob.objects.all().order_by('-created_at')
 if coordination(user): return qs
 if role(user) != 'officer': return qs.none()
 # A transferred case must not remain readable through its original import.
 if not user.membership.bureau_id:return qs.none()
 forbidden=ImportRow.objects.filter(data__has_key='bureau_id').exclude(data__bureau_id=user.membership.bureau_id).values('job_id')
 return qs.filter(owner=user).exclude(pk__in=forbidden).exclude(rows__case__in=Complaint.objects.exclude(bureau_id=user.membership.bureau_id)).distinct()

def get_job(user,job_id):
 return get_object_or_404(accessible_jobs(user),pk=job_id)

def parse_date(value, label):
 try: return date.fromisoformat(value)
 except (ValueError,TypeError): raise ValidationError(f'{label}: use YYYY-MM-DD.')

def validate_rows(job, mapping):
 if not isinstance(mapping,dict) or any(k not in FIELDS[job.kind] or v not in job.headers for k,v in mapping.items()): raise ValidationError('Invalid column mapping.')
 if any(k not in mapping for k in REQUIRED[job.kind]): raise ValidationError('Map every required column.')
 if len(set(mapping.values())) != len(mapping): raise ValidationError('Each source column can be mapped only once.')
 institutions={i.permanent_id:i for i in Institution.objects.all()}
 bureaus={b.code:b for b in Bureau.objects.all()}
 existing = {(c.source_system,c.source_reference):c for c in Complaint.objects.filter(source_reference__in=[r.raw.get(mapping.get('source_reference',''),'') for r in job.rows.all()])} if job.kind=='complaints' else {}
 from .matching import tokenizer
 summary_tokenizer=tokenizer() if job.kind=='complaints' else None
 seen=set(); output=[]
 for row in job.rows.order_by('number'):
  data={key:row.raw[value] for key,value in mapping.items()}
  row.case=None; row.error=''; row.state='ready'
  try:
   inst=institutions.get(data['institution_permanent_id']); bureau=bureaus.get(data['bureau'])
   if not inst: raise ValidationError('Unknown institution permanent ID; select a canonical institution.')
   if not bureau: raise ValidationError('Unknown bureau code.')
   if role(job.owner)=='officer' and bureau.pk!=job.owner.membership.bureau_id: raise PermissionDenied('Officer imports must belong to their own bureau.')
   if data['category'] not in dict(Complaint.CATEGORIES): raise ValidationError('Unknown category.')
   if job.kind=='complaints':
    payload={key:value for key,value in data.items() if key in CreateCaseSerializer().fields and value}
    payload.update(submission_id=str(uuid.uuid5(job.id,str(row.number))),institution=str(inst.pk),bureau=bureau.code)
    payload.setdefault('source_system','spreadsheet')
    form=CreateCaseSerializer(data=payload,context={'tokenizer':summary_tokenizer})
    form.fields['institution']=serializers.ChoiceField(choices=[str(inst.pk)])
    form.fields['bureau']=serializers.ChoiceField(choices=[bureau.code])
    form.is_valid(raise_exception=True)
    normal=json.loads(json.dumps(form.validated_data,default=str)); normal.pop('submission_id')
    normal['bureau_id']=bureau.pk; normal['institution_id']=normal.pop('institution'); normal.pop('bureau')
    status=data['status']
    if status not in dict(Complaint.STATUSES): raise ValidationError('Unknown status.')
    normal['status']=status
    due=serializers.DateTimeField().run_validation(data['due_at']) if data.get('due_at') else form.validated_data['received_at']+timedelta(days=settings.DEMO_DEADLINE_DAYS)
    if due<form.validated_data['received_at']: raise ValidationError('Deadline must not precede receipt.')
    normal['due_at']=due.isoformat()
    normal['disposed_at']=None; normal['resolution_note']=''
    if status=='disposed':
     if not data.get('resolution_note') or len(data['resolution_note'])>4000 or not data.get('disposed_at'): raise ValidationError('Disposed cases require a resolution note (maximum 4,000 characters) and disposal date.')
     disposed=serializers.DateTimeField().run_validation(data['disposed_at'])
     if disposed<form.validated_data['received_at'] or disposed>timezone.now(): raise ValidationError('Disposal must fall between receipt and now.')
     normal.update(disposed_at=disposed.isoformat(),resolution_note=data['resolution_note'])
    key=(normal['source_system'],normal['source_reference'])
    fingerprint=digest(normal)
    if key in seen: raise ValidationError('Repeated source reference within this file; remove or reconcile it.')
    seen.add(key)
    old=existing.get(key)
    if old:
     if old.submission_fingerprint!=fingerprint: raise ValidationError('Source reference already exists with different content; review the conflict.')
     if not scoped_cases(job.owner).filter(pk=old.pk).exists(): raise ValidationError('Source reference is unavailable for import.')
     row.state='duplicate'; row.case=old
    row.data={**normal,'fingerprint':fingerprint}
   else:
    field='month' if job.kind=='monthly' else 'snapshot_date'
    value=data[field]
    if job.kind=='monthly':
     value=value+'-01' if len(value)==7 else value
     if len(value)!=10 or not value.endswith('-01'):raise ValidationError('Month: use YYYY-MM or an Excel date on the first day of the month.')
    period=parse_date(value,field)
    if period>timezone.localdate(): raise ValidationError('Reporting period cannot be in the future.')
    keys=['received','disposed'] if job.kind=='monthly' else ['registered','under_review','awaiting_response','disposed','overdue']
    counts={k:serializers.IntegerField(min_value=0,max_value=1000000000).run_validation(data[k]) for k in keys}
    if job.kind=='snapshot' and counts['overdue']>sum(counts[k] for k in ['registered','under_review','awaiting_response']): raise ValidationError('Overdue count exceeds active cases.')
    key=digest([job.kind,str(inst.pk),bureau.pk,data['category'],str(period)])
    if key in seen: raise ValidationError('Repeated summary dimensions and period in this file.')
    seen.add(key)
    old=SummaryRecord.objects.filter(fingerprint=key).first()
    if old:
     if old.counts!=counts: raise ValidationError('Summary already exists with different counts; review the conflict.')
     row.state='duplicate'
    row.data={'institution_id':str(inst.pk),'bureau_id':bureau.pk,'category':data['category'],'period':str(period),'counts':counts,'fingerprint':key}
  except (ValidationError,PermissionDenied) as exc:
   row.state='rejected'; row.error=str(exc.detail)[:1000]; row.data={}
  output.append(row)
 ImportRow.objects.bulk_update(output,['data','state','error','case'],batch_size=100)
 job.mapping=mapping; job.error=''; job.save(update_fields=['mapping','error','updated_at'])

def job_data(job):
 counts=dict(job.rows.values_list('state').annotate(n=Count('id')).values_list('state','n'))
 cases=Complaint.objects.filter(importrow__job=job).distinct()
 matching=dict(cases.order_by().values_list('matching_state').annotate(n=Count('id')).values_list('matching_state','n'))
 state=job.state
 if state=='matching' and not matching.get('pending',0): state='complete' if not matching.get('failed',0) else 'matching_failed'
 events={x.kind:x.created_at for x in AuditEvent.objects.filter(detail__import=str(job.pk),kind__in=['import_confirmed','import_started','import_registered','import_matching_started','import_matching_finished']).order_by('created_at')}
 timings={}
 for name,start,end in [('queue_seconds','import_confirmed','import_started'),('registration_seconds','import_started','import_registered'),('matching_queue_seconds','import_registered','import_matching_started'),('matching_seconds','import_matching_started','import_matching_finished')]:
  if start in events and end in events:timings[name]=max(0,(events[end]-events[start]).total_seconds())
 return {'timings':timings,'id':str(job.pk),'kind':job.kind,'filename':job.filename,'headers':job.headers,'mapping':job.mapping,'fields':FIELDS[job.kind],'required':REQUIRED[job.kind],
  'state':state,'error':job.error,'created_at':job.created_at,'counts':counts,'total':sum(counts.values()),'matching':matching,
  'preview':list(job.rows.order_by('number').values('number','raw','state','error')[:20])}

@api_view(['GET','POST'])
def imports(request):
 if request.method=='GET': return Response([job_data(x) for x in accessible_jobs(request.user)[:20]])
 writable(request.user)
 kind=request.data.get('kind','complaints')
 if kind not in FIELDS: raise ValidationError('Unknown import type.')
 file=request.FILES.get('file')
 if not file: raise ValidationError('Choose a spreadsheet.')
 headers,rows=parse_file(file)
 with transaction.atomic():
  job=ImportJob.objects.create(owner=request.user,kind=kind,filename=Path(file.name).name[:180],headers=headers)
  ImportRow.objects.bulk_create([ImportRow(job=job,number=n,raw=raw) for n,raw in rows],batch_size=100)
  mapping={k:k for k in FIELDS[kind] if k in headers}
  if all(k in mapping for k in REQUIRED[kind]): validate_rows(job,mapping)
  AuditEvent.objects.create(actor=request.user,kind='import_preview',detail={'import':str(job.pk),'rows':len(rows)})
 return Response(job_data(job),status=201)

@api_view(['GET','POST'])
def import_detail(request,job_id):
 job=get_job(request.user,job_id)
 if request.method=='GET': return Response(job_data(job))
 writable(request.user)
 if job.owner_id!=request.user.pk and role(request.user)!='coordinator': raise PermissionDenied()
 with transaction.atomic():
  job=ImportJob.objects.select_for_update().get(pk=job.pk)
  action=request.data.get('action')
  if action=='preview':
   if job.state!='preview': raise ValidationError('Only unconfirmed imports can be remapped.')
   validate_rows(job,request.data.get('mapping',{}))
  elif action=='confirm':
   if job.state=='preview':
    if not job.mapping or job.rows.filter(state='pending').exists(): raise ValidationError('Validate the mapping first.')
    job.state='importing'; job.save(update_fields=['state','updated_at'])
    async_task('cases.imports.process_import',str(job.pk))
    AuditEvent.objects.create(actor=request.user,kind='import_confirmed',detail={'import':str(job.pk)})
  elif action=='retry':
   if job.state not in ('failed','matching','complete'): raise ValidationError('This job cannot be retried yet.')
   job.state='importing'; job.error=''; job.save(update_fields=['state','error','updated_at'])
   async_task('cases.imports.process_import',str(job.pk))
   ids=list(job.rows.filter(case__matching_state='failed').values_list('case_id',flat=True))
   Complaint.objects.filter(pk__in=ids).update(matching_state='pending')
   for offset in range(0,len(ids),32): async_task('cases.matching.match_batch',[str(x) for x in ids[offset:offset+32]])
  else: raise ValidationError('Use preview, confirm or retry.')
 return Response(job_data(job))

def process_import(job_id):
 try:
  with transaction.atomic():
   job=ImportJob.objects.select_for_update(of=('self',)).select_related('owner__membership').get(pk=job_id)
   if job.state!='importing': return
   if role(job.owner) not in ('officer','coordinator'): raise ValueError('Import owner no longer has write access.')
   if not AuditEvent.objects.filter(kind='import_started',detail__import=str(job.pk)).exists():
    AuditEvent.objects.create(actor=job.owner,kind='import_started',detail={'import':str(job.pk)})
   rows=list(job.rows.filter(state='ready').order_by('number')[:250]); ids=[]
   for row in rows:
    data=dict(row.data); fingerprint=data.pop('fingerprint')
    if role(job.owner)=='officer' and data['bureau_id']!=job.owner.membership.bureau_id: raise ValueError('Import owner bureau changed; coordinator review required.')
    try:
     with transaction.atomic():
      if job.kind=='complaints':
       note=data.pop('resolution_note');
       case,created=Complaint.objects.get_or_create(source_system=data['source_system'],source_reference=data['source_reference'],defaults={**data,
        'submission_id':uuid.uuid5(job.id,str(row.number)),'submission_fingerprint':fingerprint,'created_by':job.owner,
        'reference':f'C-{timezone.now():%y%m}-{uuid.uuid4().hex[:12].upper()}'})
       if case.submission_fingerprint!=fingerprint: raise ValueError('Concurrent source conflict; existing content preserved.')
       if not scoped_cases(job.owner).filter(pk=case.pk).exists(): raise ValueError('Source record unavailable in current permission scope.')
       row.case=case; row.state='imported' if created else 'duplicate'
       if created:
        CaseAction.objects.create(case=case,actor=job.owner,kind='imported',reason=note or 'Spreadsheet registration',changes={'import':str(job.pk),'row':row.number,'status':case.status})
        ids.append(str(case.pk))
      else:
       obj,created=SummaryRecord.objects.get_or_create(fingerprint=fingerprint,defaults={**data,'job':job})
       if obj.counts!=data['counts']: raise ValueError('Concurrent summary conflict; existing counts preserved.')
       row.state='imported' if created else 'duplicate'
    except (IntegrityError,ValueError) as exc:
     row.state='rejected';row.error=str(exc)[:1000]
    row.save(update_fields=['state','error','case'])
   if job.rows.filter(state='ready').exists(): async_task('cases.imports.process_import',str(job.pk))
   else:
    job.state='matching' if job.kind=='complaints' else 'complete'
    AuditEvent.objects.create(actor=job.owner,kind='import_registered',detail={'import':str(job.pk)})
    if job.kind=='complaints': async_task('cases.imports.process_import_matching',str(job.pk))
   job.save(update_fields=['state','updated_at'])
   from django.core.cache import caches
   caches['dashboard'].clear()
 except Exception:
  ImportJob.objects.filter(pk=job_id).update(state='failed',error='Import stopped; committed batches are safe. Retry after checking worker logs.')
  raise

@api_view(['GET'])
def import_errors(request,job_id):
 job=get_job(request.user,job_id)
 out=io.StringIO(); writer=csv.writer(out);writer.writerow(['row','error'])
 for row in job.rows.filter(state='rejected').order_by('number'): writer.writerow([row.number,"'"+row.error])
 AuditEvent.objects.create(actor=request.user,kind='import_errors_export',detail={'import':str(job.pk)})
 return HttpResponse(out.getvalue(),content_type='text/csv',headers={'Content-Disposition':'attachment; filename="import-errors.csv"'})

@api_view(['GET'])
def template(request,kind):
 if kind not in FIELDS: raise ValidationError('Unknown template.')
 out=io.StringIO(); csv.writer(out).writerow(FIELDS[kind])
 return HttpResponse(out.getvalue(),content_type='text/csv',headers={'Content-Disposition':f'attachment; filename="{kind}-template.csv"'})

@api_view(['GET'])
def import_report(request,job_id):
 job=get_job(request.user,job_id)
 if job.kind=='complaints':
  from .api import dashboard_data
  from types import SimpleNamespace
  params=request.query_params.copy(); params['import_id']=str(job.pk)
  return Response(dashboard_data(SimpleNamespace(user=request.user,query_params=params)))
 data=summary_data(job,request.query_params.get('period'))
 data['row_count']=len(data['rows']);data['rows']=data['rows'][:100]
 return Response(data)

def summary_data(job,selected_period=None):
 # Duplicate summary uploads use their validated dimensions, without adding to the global corpus.
 data=list(job.rows.filter(state__in=['imported','duplicate']).values_list('data',flat=True))
 period=selected_period or (max([x['period'] for x in data]) if data else '')
 if job.kind=='snapshot': data=[x for x in data if x['period']==period]
 institutions=dict(Institution.objects.values_list('pk','name'));bureaus=dict(Bureau.objects.values_list('pk','code'))
 return {'kind':job.kind,'job':job_data(job),'period':period,'periods':sorted(set(x['period'] for x in job.rows.filter(state__in=['imported','duplicate']).values_list('data',flat=True))),
  'rows':[{'institution':institutions[uuid.UUID(x['institution_id'])],'bureau':bureaus[x['bureau_id']],**x} for x in data],
  'totals':{k:sum(x['counts'].get(k,0) for x in data) for k in (['received','disposed'] if job.kind=='monthly' else ['registered','under_review','awaiting_response','disposed','overdue'])},
  'generated_at':timezone.now()}


@api_view(['GET'])
def import_summary_csv(request,job_id):
 job=get_job(request.user,job_id)
 if job.kind=='complaints': raise ValidationError('Use the case CSV export for individual complaints.')
 data=summary_data(job,request.query_params.get('period'))
 from .exports import safe
 out=io.StringIO();writer=csv.writer(out);keys=list(data['totals']);writer.writerow(['period','institution','bureau','category',*keys])
 for row in data['rows']:writer.writerow([safe(x) for x in [row['period'],row['institution'],row['bureau'],row['category'],*[row['counts'][k] for k in keys]]])
 AuditEvent.objects.create(actor=request.user,kind='summary_export',detail={'import':str(job.pk),'period':data['period']})
 return HttpResponse(out.getvalue(),content_type='text/csv',headers={'Content-Disposition':'attachment; filename="summary-report.csv"'})


def process_import_matching(job_id):
 from .matching import match_batch
 job=ImportJob.objects.get(pk=job_id)
 ids=list(job.rows.filter(case__matching_state='pending').order_by('number').values_list('case_id',flat=True)[:64])
 if not ids:return
 if not AuditEvent.objects.filter(kind='import_matching_started',detail__import=str(job.pk)).exists():
  AuditEvent.objects.create(actor=job.owner,kind='import_matching_started',detail={'import':str(job.pk)})
 try:
  match_batch([str(pk) for pk in ids])
 finally:
  # A failed batch cannot strand later records; failures remain explicitly retryable.
  if job.rows.filter(case__matching_state='pending').exists():async_task('cases.imports.process_import_matching',str(job.pk))
  else:AuditEvent.objects.create(actor=job.owner,kind='import_matching_finished',detail={'import':str(job.pk)})
