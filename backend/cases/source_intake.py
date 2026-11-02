"""Bureau uploads are snapshots; changed source content never overwrites a case."""
import json
from django.db import transaction
from django.db.models import Count, Max, Q, Exists, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from .access import role, coordination, scoped_cases, current_bureau_id, writable
from .api import Conflict, page
from .models import Bureau, ImportJob, ImportRow, CaseAction, AuditEvent, Complaint, Institution
from .serializers import CaseSerializer


class SourceConflict(ValidationError):
    pass


class SourceConfig(serializers.Serializer):
    source_system = serializers.RegexField(r'^[A-Za-z0-9._-]+$', max_length=40)
    source_bureau = serializers.SlugRelatedField(slug_field='code', queryset=Bureau.objects.all())
    status_mapping = serializers.DictField(child=serializers.ChoiceField(choices=['registered', 'under_review', 'awaiting_response', 'disposed']), default=dict)
    def validate_status_mapping(self, value):
        if len(value) > 50 or any(not k.strip() or len(k) > 80 or k != k.strip() for k in value):
            raise ValidationError('Use at most 50 distinct source labels, each 1–80 characters without surrounding spaces.')
        return value


def configuration(request, kind):
    if not any(request.data.get(k) for k in ['source_system', 'source_bureau', 'status_mapping']): return {}
    if kind != 'complaints': raise ValidationError('Bureau-source intake is for individual complaints, not summary totals.')
    raw = request.data.get('status_mapping', '{}')
    try: mapping = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError): raise ValidationError('Invalid source status mapping.')
    form = SourceConfig(data={'source_system': request.data.get('source_system'), 'source_bureau': request.data.get('source_bureau'), 'status_mapping': mapping})
    form.is_valid(raise_exception=True)
    data = form.validated_data
    if role(request.user) == 'officer' and data['source_bureau'].pk != current_bureau_id(request.user):
        raise PermissionDenied('Source intake must belong to your current Bureau.')
    return data


class RowSerializer(serializers.ModelSerializer):
    current_case = serializers.SerializerMethodField()
    differences = serializers.SerializerMethodField()
    resolution = serializers.SerializerMethodField()
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', default=None)
    def get_current_case(self, row):
        case = self.context['cases'].get(row.case_id)
        return CaseSerializer(case).data if case else None
    def get_differences(self, row):
        case=self.context['cases'].get(row.case_id)
        return differences(row,case,row.job) if case else []
    def get_resolution(self, row):
        return self.context['resolutions'].get(row.number)
    class Meta:
        model = ImportRow
        fields = ['number', 'raw', 'data', 'state', 'error', 'version', 'current_case', 'resolution_reason', 'resolved_at', 'resolved_by_name','differences','resolution']


def differences(row, case, job):
    """Only explicit source values can replace metadata; intake defaults are creation-only."""
    result=[]
    def add(field,before,after,eligible,explanation=''):
        if before!=after:
            result.append({'field':field,'before':before,'after':after,'eligible':eligible,'explanation':explanation})
    for field in ['category','classification','due_at']:
        explicit=bool(job.mapping.get(field) and row.raw.get(job.mapping[field],''))
        before=getattr(case,field);after=row.data.get(field)
        if field=='due_at' and after:
            after=serializers.DateTimeField().run_validation(after)
        if before==after:continue
        add(field,before.isoformat() if hasattr(before,'isoformat') else before,
            after.isoformat() if hasattr(after,'isoformat') else after,explicit,
            '' if explicit else 'Not supplied explicitly; intake defaults cannot reset this case.')
    status=row.data.get('status')
    before={'status':case.status,'disposed_at':case.disposed_at.isoformat() if case.disposed_at else None}
    after={'status':status,'disposed_at':row.data.get('disposed_at')}
    if status=='disposed':after['resolution_note']=row.data.get('resolution_note')
    add('status',before,after,True,'Closure includes its source disposal date and resolution note.')
    for field,key in [('summary','summary'),('description','description'),('institution_id','institution_id'),
                      ('source_system','source_system'),('source_reference','source_reference'),('received_at','received_at'),
                      ('bureau_id','bureau_id'),('incident_date','incident_date')]:
        before=getattr(case,field);after=row.data.get(key)
        if field in ('received_at',) and after:after=serializers.DateTimeField().run_validation(after)
        if before==after:continue
        before=before.isoformat() if hasattr(before,'isoformat') else str(before) if before is not None else None
        after=after.isoformat() if hasattr(after,'isoformat') else str(after) if after is not None else None
        add(field,before,after,False,'Original identity/allegations are retained. Use the existing case workflow for ownership changes.')
    return result


@api_view(['GET'])
def rows(request, job_id):
    from .imports import get_job
    job = get_job(request.user, job_id)
    state = request.query_params.get('state', 'all')
    if state not in ['all', 'pending', 'ready', 'imported', 'duplicate', 'rejected', 'conflict', 'resolved']:
        raise ValidationError('Unknown import row state.')
    qs = job.rows.select_related('resolved_by','job').order_by('number')
    if state != 'all': qs = qs.filter(state=state)
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination(); records = paginator.paginate_queryset(qs, request)
    cases = {c.pk: c for c in scoped_cases(request.user).filter(pk__in=[r.case_id for r in records if r.case_id])}
    resolutions={a.changes['row']:a.changes for a in CaseAction.objects.filter(case_id__in=cases,kind='source_conflict',changes__import=str(job.pk),changes__row__in=[r.number for r in records]).order_by('id')}
    return paginator.get_paginated_response(RowSerializer(records, many=True, context={'cases': cases,'resolutions':resolutions}).data)


class Resolution(serializers.Serializer):
    expected_version = serializers.IntegerField(min_value=1)
    expected_case_version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=2000)
    decision = serializers.ChoiceField(choices=['keep_portal_record','apply_selected_updates'])
    fields = serializers.ListField(child=serializers.ChoiceField(choices=['status','category','classification','due_at']),default=list,allow_empty=True)
    confirm_reopen = serializers.BooleanField(default=False)
    retain_unselected = serializers.BooleanField(default=False)

    def validate(self,data):
        if len(set(data['fields']))!=len(data['fields']):raise ValidationError('Select each field once.')
        data['fields']=sorted(data['fields'])
        if data['decision']=='apply_selected_updates' and (not data['fields'] or not data['retain_unselected']):
            raise ValidationError('Select updates and explicitly retain original allegations and unchecked fields.')
        if data['decision']=='keep_portal_record' and data['fields']:raise ValidationError('Keeping a record cannot apply fields.')
        return data


@api_view(['POST'])
def resolve(request, job_id, number):
    from .imports import get_job
    writable(request.user)
    job = get_job(request.user, job_id)
    if job.owner_id != request.user.pk and role(request.user) != 'coordinator': raise PermissionDenied()
    form = Resolution(data=request.data); form.is_valid(raise_exception=True); data = form.validated_data
    if data['decision']=='apply_selected_updates' and role(request.user)!='coordinator':raise PermissionDenied('Applying source updates requires a coordinator.')
    original=get_object_or_404(job.rows,number=number)
    initial=get_object_or_404(scoped_cases(request.user),pk=original.case_id)
    with transaction.atomic():
        Institution.objects.select_for_update().get(pk=initial.institution_id)
        writable(request.user)
        if data['decision']=='apply_selected_updates' and role(request.user)!='coordinator':raise PermissionDenied()
        get_job(request.user,job_id)
        job = ImportJob.objects.select_for_update().get(pk=job.pk)
        if not job.registered_at: raise ValidationError('Confirm this intake and wait for registration to finish before reviewing conflicts.')
        row = get_object_or_404(ImportRow.objects.select_for_update(), job=job, number=number)
        case = get_object_or_404(scoped_cases(request.user).select_for_update(of=('self',)), pk=row.case_id)
        if case.pk!=initial.pk or case.institution_id!=initial.institution_id:raise Conflict()
        if row.state == 'resolved' and row.resolved_by_id == request.user.pk and row.resolution_reason == data['reason'] and row.version in (data['expected_version'], data['expected_version'] + 1):
            previous=CaseAction.objects.filter(case=case,kind='source_conflict',changes__import=str(job.pk),changes__row=number).order_by('-id').first()
            if previous and (previous.changes.get('request')==data or ('request' not in previous.changes and data['decision']=='keep_portal_record')):
                return Response({'state':row.state,'version':row.version,'case_version':previous.changes.get('case_version',case.version)})
            raise Conflict()
        if row.version != data['expected_version'] or case.version != data['expected_case_version']: raise Conflict()
        if row.state != 'conflict' or not job.source_system: raise ValidationError('Only a source-conflict row can be reviewed.')
        comparison=differences(row,case,job); eligible={d['field'] for d in comparison if d['eligible']}
        changes={}
        if data['decision']=='apply_selected_updates':
            if not set(data['fields'])<=eligible:raise ValidationError('A selected field is unchanged, protected or was not explicitly supplied.')
            for field in data['fields']:
                if field=='status':
                    target=serializers.ChoiceField(choices=Complaint.STATUSES).run_validation(row.data['status'])
                    if case.status=='disposed' and target!='disposed' and not data['confirm_reopen']:raise ValidationError('Explicitly confirm reopening this closed case.')
                    disposal=None
                    if target=='disposed':
                        note=serializers.CharField(max_length=4000).run_validation(row.data.get('resolution_note'))
                        disposal=serializers.DateTimeField().run_validation(row.data.get('disposed_at'))
                        if disposal<case.received_at or disposal>timezone.now():raise ValidationError('Disposal must fall between the original case receipt and now.')
                        changes['resolution_note']={'before':None,'after':note}
                        for key,value in [('next_action',''),('next_action_date',None)]:
                            old=getattr(case,key);changes[key]={'before':old.isoformat() if hasattr(old,'isoformat') else old,'after':value};setattr(case,key,value)
                    for key,value in [('status',target),('disposed_at',disposal),('source_status',row.data.get('source_status',case.source_status))]:
                        old=getattr(case,key);changes[key]={'before':old.isoformat() if hasattr(old,'isoformat') else old,'after':value.isoformat() if hasattr(value,'isoformat') else value};setattr(case,key,value)
                else:
                    value=row.data[field]
                    if field=='due_at':
                        value=serializers.DateTimeField().run_validation(value)
                        if value<case.received_at:raise ValidationError('Deadline must not precede the original receipt.')
                    else:value=serializers.ChoiceField(choices=Complaint.CATEGORIES if field=='category' else Complaint.CLASSIFICATIONS).run_validation(value)
                    old=getattr(case,field);changes[field]={'before':old.isoformat() if hasattr(old,'isoformat') else old,'after':value.isoformat() if hasattr(value,'isoformat') else value};setattr(case,field,value)
            case.version+=1;case.source_import=job;case.source_last_seen_at=job.registered_at;case.save()
        row.state = 'resolved'; row.resolution_reason = data['reason']; row.resolved_by = request.user; row.resolved_at = timezone.now(); row.version += 1
        row.save(update_fields=['state', 'resolution_reason', 'resolved_by', 'resolved_at', 'version'])
        CaseAction.objects.create(case=case, actor=request.user, kind='source_conflict', reason=data['reason'], changes={'import': str(job.pk), 'row': row.number, 'decision': data['decision'], 'incoming_fingerprint': row.data.get('fingerprint'),
            'request':data,'applied_fields':data['fields'],'updates':changes,'retained_fields':[d['field'] for d in comparison if d['field'] not in data['fields']], 'case_version':case.version})
        AuditEvent.objects.create(actor=request.user, kind='source_conflict_review', detail={'import': str(job.pk), 'row': row.number, 'case': str(case.pk)})
    return Response({'state': row.state, 'version': row.version,'case_version':case.version})


class SourceSerializer(serializers.Serializer):
    source_system = serializers.CharField()
    source_bureau__code = serializers.CharField()
    source_bureau__name = serializers.CharField()
    uploads = serializers.IntegerField()
    last_uploaded_at = serializers.DateTimeField()
    last_registered_at = serializers.DateTimeField(allow_null=True)
    last_success_at = serializers.DateTimeField(allow_null=True)
    unresolved_conflict_rows = serializers.IntegerField()
    latest_job = serializers.UUIDField()


class SourceJobSerializer(serializers.ModelSerializer):
    source_bureau = serializers.CharField(source='source_bureau.code')
    unresolved_conflicts = serializers.IntegerField()
    total_rows = serializers.IntegerField()
    class Meta:
        model = ImportJob
        fields = ['id', 'filename', 'source_system', 'source_bureau', 'state', 'created_at', 'registered_at', 'unresolved_conflicts', 'total_rows']


@api_view(['GET'])
def jobs(request):
    from .imports import accessible_jobs
    qs = accessible_jobs(request.user).exclude(source_system='').filter(source_bureau__isnull=False).select_related('source_bureau')
    for key, field, limit in [('source', 'source_system', 40), ('bureau', 'source_bureau__code', 20)]:
        value = serializers.CharField(max_length=limit, allow_blank=True).run_validation(request.query_params.get(key, ''))
        if value: qs = qs.filter(**{field: value})
    qs = qs.annotate(unresolved_conflicts=Count('rows', filter=Q(rows__state='conflict')), total_rows=Count('rows'))
    if 'conflicts' in request.query_params and serializers.BooleanField().run_validation(request.query_params['conflicts']):
        qs = qs.filter(unresolved_conflicts__gt=0)
    return page(request, qs.order_by('-created_at', '-id'), SourceJobSerializer)


@api_view(['GET'])
def sources(request):
    from .imports import accessible_jobs
    jobs = accessible_jobs(request.user).exclude(source_system='').filter(source_bureau__isnull=False)
    text = serializers.CharField(max_length=80, allow_blank=True).run_validation(request.query_params.get('q', ''))
    if text: jobs = jobs.filter(source_system__icontains=text)
    errors = ImportRow.objects.filter(job_id=OuterRef('pk'), state__in=['rejected', 'conflict', 'resolved'])
    latest = jobs.filter(source_system=OuterRef('source_system'), source_bureau_id=OuterRef('source_bureau_id')).order_by('-created_at', '-id')
    qs = jobs.annotate(has_errors=Exists(errors)).values('source_system', 'source_bureau_id', 'source_bureau__code', 'source_bureau__name').annotate(
        uploads=Count('id', distinct=True), last_uploaded_at=Max('created_at'), last_registered_at=Max('registered_at'),
        last_success_at=Max('registered_at', filter=Q(has_errors=False)),
        unresolved_conflict_rows=Count('rows', filter=Q(rows__state='conflict')),
        latest_job=Subquery(latest.values('id')[:1])).order_by('source_system', 'source_bureau_id')
    return page(request, qs, SourceSerializer)
