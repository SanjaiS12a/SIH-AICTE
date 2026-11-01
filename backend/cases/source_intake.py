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
from .models import Bureau, ImportJob, ImportRow, CaseAction, AuditEvent
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
    resolved_by_name = serializers.CharField(source='resolved_by.get_full_name', default=None)
    def get_current_case(self, row):
        case = self.context['cases'].get(row.case_id)
        return CaseSerializer(case).data if case else None
    class Meta:
        model = ImportRow
        fields = ['number', 'raw', 'data', 'state', 'error', 'version', 'current_case', 'resolution_reason', 'resolved_at', 'resolved_by_name']


@api_view(['GET'])
def rows(request, job_id):
    from .imports import get_job
    job = get_job(request.user, job_id)
    state = request.query_params.get('state', 'all')
    if state not in ['all', 'pending', 'ready', 'imported', 'duplicate', 'rejected', 'conflict', 'resolved']:
        raise ValidationError('Unknown import row state.')
    qs = job.rows.select_related('resolved_by').order_by('number')
    if state != 'all': qs = qs.filter(state=state)
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination(); records = paginator.paginate_queryset(qs, request)
    cases = {c.pk: c for c in scoped_cases(request.user).filter(pk__in=[r.case_id for r in records if r.case_id])}
    return paginator.get_paginated_response(RowSerializer(records, many=True, context={'cases': cases}).data)


class Resolution(serializers.Serializer):
    expected_version = serializers.IntegerField(min_value=1)
    expected_case_version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=2000)
    decision = serializers.ChoiceField(choices=['keep_portal_record'])


@api_view(['POST'])
def resolve(request, job_id, number):
    from .imports import get_job
    writable(request.user)
    job = get_job(request.user, job_id)
    if job.owner_id != request.user.pk and role(request.user) != 'coordinator': raise PermissionDenied()
    form = Resolution(data=request.data); form.is_valid(raise_exception=True); data = form.validated_data
    with transaction.atomic():
        job = ImportJob.objects.select_for_update().get(pk=job.pk)
        if not job.registered_at: raise ValidationError('Confirm this intake and wait for registration to finish before reviewing conflicts.')
        row = get_object_or_404(ImportRow.objects.select_for_update(), job=job, number=number)
        case = get_object_or_404(scoped_cases(request.user).select_for_update(of=('self',)), pk=row.case_id)
        if row.state == 'resolved' and row.resolved_by_id == request.user.pk and row.resolution_reason == data['reason'] and row.version in (data['expected_version'], data['expected_version'] + 1):
            return Response({'state': row.state, 'version': row.version})
        if row.version != data['expected_version'] or case.version != data['expected_case_version']: raise Conflict()
        if row.state != 'conflict' or not job.source_system: raise ValidationError('Only a source-conflict row can be reviewed.')
        row.state = 'resolved'; row.resolution_reason = data['reason']; row.resolved_by = request.user; row.resolved_at = timezone.now(); row.version += 1
        row.save(update_fields=['state', 'resolution_reason', 'resolved_by', 'resolved_at', 'version'])
        CaseAction.objects.create(case=case, actor=request.user, kind='source_conflict', reason=data['reason'], changes={'import': str(job.pk), 'row': row.number, 'decision': data['decision'], 'incoming_fingerprint': row.data.get('fingerprint')})
        AuditEvent.objects.create(actor=request.user, kind='source_conflict_review', detail={'import': str(job.pk), 'row': row.number, 'case': str(case.pk)})
    return Response({'state': row.state, 'version': row.version})


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
