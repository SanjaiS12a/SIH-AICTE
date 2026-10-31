"""Manual supervisory requests, independent of ownership and disposal decisions."""
from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_q.tasks import async_task
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .access import scoped_cases, filtered_cases, writable, role, coordination
from .api import Conflict, page
from .models import Escalation, CaseAction
from .serializers import CaseSerializer


class EscalationSerializer(serializers.ModelSerializer):
    case = CaseSerializer(read_only=True)
    created_by = serializers.CharField(source='created_by.get_full_name')
    resolved_by = serializers.CharField(source='resolved_by.get_full_name', default=None)

    class Meta:
        model = Escalation
        fields = ['id', 'case', 'created_by', 'reason', 'status', 'created_at',
                  'resolved_by', 'resolution_reason', 'resolved_at', 'version']


class CreateEscalationSerializer(serializers.Serializer):
    submission_id = serializers.UUIDField()
    expected_version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=4000)


class ResolveEscalationSerializer(serializers.Serializer):
    expected_version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=4000)


def records(request, cases, default_state):
    state = request.query_params.get('state', default_state)
    if state not in ('pending', 'resolved', 'all'):
        raise ValidationError('Choose pending, resolved or all escalation states.')
    qs = Escalation.objects.filter(case__in=cases).select_related('case__institution', 'case__bureau', 'case__source_bureau', 'case__assigned_to', 'created_by', 'resolved_by')
    qs = qs.prefetch_related(Prefetch('case__escalations',queryset=Escalation.objects.filter(status='pending'),to_attr='pending_escalations'))
    return qs if state == 'all' else qs.filter(status=state)


@api_view(['GET'])
def queue(request):
    if not coordination(request.user):
        raise PermissionDenied('The escalation queue requires coordination access.')
    return page(request, records(request, filtered_cases(request), 'pending'), EscalationSerializer)


@api_view(['GET', 'POST'])
def case_escalations(request, case_id):
    if request.method == 'GET':
        case = get_object_or_404(scoped_cases(request.user), pk=case_id)
        return page(request, records(request, scoped_cases(request.user).filter(pk=case.pk), 'all'), EscalationSerializer)
    writable(request.user)
    form = CreateEscalationSerializer(data=request.data)
    form.is_valid(raise_exception=True)
    data = form.validated_data
    with transaction.atomic():
        case = get_object_or_404(scoped_cases(request.user).select_for_update(of=('self',)), pk=case_id)
        existing = Escalation.objects.filter(submission_id=data['submission_id']).first()
        if existing:
            if existing.case_id != case.pk or existing.created_by_id != request.user.pk:
                raise PermissionDenied('This escalation submission identifier is already in use.')
            if existing.reason != data['reason']:
                raise Conflict('Submission ID was reused with a different escalation reason.')
            return Response(EscalationSerializer(existing).data)
        if case.version != data['expected_version']:
            raise Conflict()
        if case.status == 'disposed':
            raise ValidationError('Only active cases can be escalated.')
        if Escalation.objects.filter(case=case, status='pending').exists():
            raise Conflict('An unresolved escalation already exists for this case.')
        try:
            with transaction.atomic():
                escalation = Escalation.objects.create(case=case, created_by=request.user,
                    submission_id=data['submission_id'], reason=data['reason'])
        except IntegrityError:
            raise Conflict('An escalation request already exists; refresh before retrying.')
        case.version += 1
        case.save(update_fields=['version'])
        case.has_unresolved_escalation = True
        CaseAction.objects.create(case=case, actor=request.user, kind='escalation_created', reason=data['reason'],
            changes={'escalation_id': str(escalation.pk), 'escalation_status': {'before': None, 'after': 'pending'}})
        async_task('cases.tasks.notify_escalation', str(escalation.pk))
    return Response(EscalationSerializer(escalation).data, status=201)


@api_view(['POST'])
def resolve(request, escalation_id):
    if role(request.user) != 'coordinator':
        raise PermissionDenied('Only coordinators can resolve escalations.')
    form = ResolveEscalationSerializer(data=request.data)
    form.is_valid(raise_exception=True)
    data = form.validated_data
    record = get_object_or_404(Escalation.objects.filter(case__in=scoped_cases(request.user)), pk=escalation_id)
    with transaction.atomic():
        # Creation and resolution take the case lock first, avoiding opposite lock order.
        case = get_object_or_404(scoped_cases(request.user).select_for_update(of=('self',)), pk=record.case_id)
        escalation = Escalation.objects.select_for_update().get(pk=record.pk)
        if escalation.status == 'resolved':
            if escalation.version == data['expected_version'] + 1 and escalation.resolved_by_id == request.user.pk and escalation.resolution_reason == data['reason']:
                return Response(EscalationSerializer(escalation).data)
            raise Conflict('This escalation is already resolved. Refresh to review its history.')
        if escalation.version != data['expected_version']:
            raise Conflict()
        escalation.status = 'resolved'
        escalation.resolved_by = request.user
        escalation.resolution_reason = data['reason']
        escalation.resolved_at = timezone.now()
        escalation.version += 1
        escalation.save()
        case.version += 1
        case.save(update_fields=['version'])
        CaseAction.objects.create(case=case, actor=request.user, kind='escalation_resolved', reason=data['reason'],
            changes={'escalation_id': str(escalation.pk), 'escalation_status': {'before': 'pending', 'after': 'resolved'}})
    return Response(EscalationSerializer(escalation).data)
