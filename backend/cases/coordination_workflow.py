"""Explicit shared work; relationship labels never imply administrative agreement."""
import hashlib
import json
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .access import coordination, role, scoped_cases
from .api import Conflict, page
from .models import Bureau, Membership, Institution, Complaint, CaseAction, CoordinationRecord, CoordinationParticipant
from .serializers import CaseSerializer, ActionReadSerializer


class ParticipantInput(serializers.Serializer):
    bureau = serializers.SlugRelatedField(slug_field='code', queryset=Bureau.objects.all())
    officer = serializers.IntegerField(min_value=1)
    instruction = serializers.CharField(max_length=2000)
    action_date = serializers.DateField(required=False, allow_null=True)


class OpenInput(serializers.Serializer):
    submission_id = serializers.UUIDField()
    institution = serializers.UUIDField()
    cases = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=50)
    lead_bureau = serializers.SlugRelatedField(slug_field='code', queryset=Bureau.objects.all())
    lead_officer = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=4000)
    participants = ParticipantInput(many=True, allow_empty=False)

    def validate(self, data):
        ids = data['cases']
        if len(set(ids)) != len(ids):
            raise ValidationError('Select each case only once.')
        participants = data['participants']
        bureaus = [p['bureau'].pk for p in participants]
        if len(bureaus) != len(set(bureaus)) or len(bureaus) < 2:
            raise ValidationError('Choose at least two distinct participating Bureaus.')
        for p in participants:
            if not Membership.objects.filter(user_id=p['officer'], role='officer', bureau=p['bureau'], user__is_active=True).exists():
                raise ValidationError('Each responsible officer must currently belong to their participating Bureau.')
        if not any(p['bureau'] == data['lead_bureau'] and p['officer'] == data['lead_officer'] for p in participants):
            raise ValidationError('The lead must be one of the designated participating officers.')
        return data


class ParticipantSerializer(serializers.ModelSerializer):
    bureau = serializers.CharField(source='bureau.name')
    bureau_code = serializers.CharField(source='bureau.code')
    officer_name = serializers.CharField(source='officer.get_full_name')
    class Meta:
        model = CoordinationParticipant
        fields = ['id', 'bureau', 'bureau_code', 'officer_id', 'officer_name', 'instruction', 'action_date', 'acknowledged_at', 'completed_at', 'completion_note']


class RecordSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name')
    lead_bureau_name = serializers.CharField(source='lead_bureau.name')
    lead_officer_name = serializers.CharField(source='lead_officer.get_full_name')
    participants = ParticipantSerializer(many=True)
    class Meta:
        model = CoordinationRecord
        fields = ['id', 'institution_id', 'institution_name', 'lead_bureau_name', 'lead_officer_name', 'reason', 'state', 'outcome', 'version', 'created_at', 'closed_at', 'participants']


def require_management(user, write=False):
    if (write and role(user) != 'coordinator') or (not write and not coordination(user)):
        raise PermissionDenied('Coordination management access is required.')


def records():
    return CoordinationRecord.objects.select_related('institution', 'lead_bureau', 'lead_officer').prefetch_related('participants__bureau', 'participants__officer')


def filtered_records(request):
    from .serializers import FilterSerializer
    form = FilterSerializer(data=request.query_params)
    form.is_valid(raise_exception=True)
    p = form.validated_data
    qs = records()
    for key, field in [('institution','institution_id'), ('region','institution__region'), ('district','institution__district__icontains')]:
        if key == 'district' and p.get('district_exact'): field = 'institution__district'
        if p.get(key): qs = qs.filter(**{field:p[key]})
    return qs


def audit(record, user, kind, reason, changes):
    for case_id in record.cases.values_list('id', flat=True):
        CaseAction.objects.create(case_id=case_id, actor=user, kind=kind, reason=reason,
            changes={'coordination_id': str(record.pk), **changes})


@api_view(['GET', 'POST'])
def registry(request):
    require_management(request.user, request.method == 'POST')
    if request.method == 'GET':
        qs = filtered_records(request)
        if 'awaiting_ack' in request.query_params:
            awaiting = serializers.BooleanField().run_validation(request.query_params['awaiting_ack'])
            if awaiting: qs = qs.filter(state='in_coordination', participants__acknowledged_at__isnull=True).distinct()
        state = request.query_params.get('state', 'all')
        if state not in ('all', 'in_coordination', 'closed'):
            raise ValidationError('Choose all, in_coordination or closed.')
        if state != 'all': qs = qs.filter(state=state)
        return page(request, qs, RecordSerializer)
    form = OpenInput(data=request.data)
    form.is_valid(raise_exception=True)
    data = form.validated_data
    fingerprint = hashlib.sha256(json.dumps(data, default=str, sort_keys=True).encode()).hexdigest()
    with transaction.atomic():
        get_object_or_404(Institution.objects.select_for_update(), pk=data['institution'])
        existing = CoordinationRecord.objects.filter(submission_id=data['submission_id']).first()
        if existing:
            if existing.created_by_id != request.user.pk or existing.submission_fingerprint != fingerprint:
                raise Conflict('Submission ID already belongs to a different coordination request.')
            return Response(RecordSerializer(records().get(pk=existing.pk)).data)
        cases = list(scoped_cases(request.user).select_for_update(of=('self',)).filter(pk__in=data['cases'], institution_id=data['institution']))
        if len(cases) != len(data['cases']):
            raise ValidationError('All selected cases must belong to this canonical institution.')
        participants = data.pop('participants')
        if not {c.bureau_id for c in cases}.issubset({p['bureau'].pk for p in participants}):
            raise ValidationError('Include every current case-owning Bureau as a participant.')
        try:
            with transaction.atomic():
                record = CoordinationRecord.objects.create(submission_id=data['submission_id'], submission_fingerprint=fingerprint,
                    institution_id=data['institution'], lead_bureau=data['lead_bureau'], lead_officer_id=data['lead_officer'],
                    reason=data['reason'], created_by=request.user)
        except IntegrityError:
            raise Conflict('This submission was recorded concurrently. Reload before continuing.')
        record.cases.set(cases)
        for p in participants:
            CoordinationParticipant.objects.create(record=record, bureau=p['bureau'], officer_id=p['officer'], instruction=p['instruction'], action_date=p.get('action_date'))
        audit(record, request.user, 'coordination_opened', data['reason'], {'lead_bureau': data['lead_bureau'].code, 'lead_officer': data['lead_officer'], 'participants': ParticipantSerializer(record.participants.all(), many=True).data})
    return Response(RecordSerializer(records().get(pk=record.pk)).data, status=201)


@api_view(['GET'])
def detail(request, record_id):
    require_management(request.user)
    record = get_object_or_404(records(), pk=record_id)
    data = RecordSerializer(record).data
    data['cases'] = CaseSerializer(scoped_cases(request.user).filter(coordinationrecord=record), many=True).data
    return Response(data)


@api_view(['GET'])
def history(request, record_id):
    require_management(request.user)
    record = get_object_or_404(records(), pk=record_id)
    actions = CaseAction.objects.filter(case__in=record.cases.all(), changes__coordination_id=str(record.pk)).select_related('actor').order_by('-created_at', '-id')
    return page(request, actions, ActionReadSerializer)


class UpdateInput(serializers.Serializer):
    expected_version = serializers.IntegerField(min_value=1)
    action = serializers.ChoiceField(choices=['acknowledge', 'complete', 'close', 'revise'])
    note = serializers.CharField(max_length=2000, required=False)
    participant = serializers.IntegerField(min_value=1, required=False)
    officer = serializers.IntegerField(min_value=1, required=False)
    instruction = serializers.CharField(max_length=2000, required=False)
    action_date = serializers.DateField(required=False, allow_null=True)


@api_view(['POST'])
def update(request, record_id):
    form = UpdateInput(data=request.data)
    form.is_valid(raise_exception=True)
    data = form.validated_data
    management_action = data['action'] in ('close', 'revise')
    if management_action: require_management(request.user, True)
    elif role(request.user) != 'officer':
        raise PermissionDenied('Only the designated Bureau officer can acknowledge or complete their action.')
    with transaction.atomic():
        record = get_object_or_404(CoordinationRecord.objects.select_for_update(), pk=record_id)
        participant = None
        if not management_action:
            # Recalculate membership on every request; a former participant has no continuing access.
            member = Membership.objects.filter(user=request.user, role='officer', user__is_active=True).first()
            participant = get_object_or_404(record.participants, officer=request.user, bureau_id=member.bureau_id if member else None)
        if record.version != data['expected_version']: raise Conflict()
        if record.state == 'closed': raise ValidationError('This coordination record is closed.')
        now = timezone.now()
        if data['action'] == 'revise':
            if not all(data.get(k) for k in ['participant', 'officer', 'instruction', 'note']):
                raise ValidationError('Select a participant, current officer, shared instruction and reason for revision.')
            participant = get_object_or_404(record.participants, pk=data['participant'])
            if not Membership.objects.filter(user_id=data['officer'], role='officer', bureau=participant.bureau, user__is_active=True).exists():
                raise ValidationError('The new officer must currently belong to this participating Bureau.')
            participant.officer_id, participant.instruction = data['officer'], data['instruction']
            participant.action_date = data.get('action_date')
            participant.acknowledged_at = participant.completed_at = None
            participant.completion_note = ''
            if record.lead_bureau_id == participant.bureau_id: record.lead_officer_id = participant.officer_id
        elif data['action'] == 'acknowledge':
            if participant.acknowledged_at:
                return Response({'version': record.version, 'state': record.state})
            participant.acknowledged_at = now
        elif data['action'] == 'complete':
            if not participant.acknowledged_at: raise ValidationError('Acknowledge your action before completing it.')
            if not data.get('note'): raise ValidationError('A completion note is required.')
            if participant.completed_at: raise ValidationError('This action is already complete.')
            participant.completed_at, participant.completion_note = now, data['note']
        else:
            if not data.get('note'): raise ValidationError('A coordination outcome is required.')
            if record.participants.filter(completed_at__isnull=True).exists():
                raise ValidationError('Every participating Bureau must acknowledge and complete its agreed action first.')
            record.state, record.outcome, record.closed_at = 'closed', data['note'], now
        if participant: participant.save()
        record.version += 1
        record.save()
        audit(record, request.user, 'coordination_' + data['action'], data.get('note', 'Bureau action acknowledged'),
            {'participant': ParticipantSerializer(participant).data if participant else None, 'state': record.state})
    return Response({'version': record.version, 'state': record.state})


class RequestSerializer(serializers.ModelSerializer):
    coordination_id = serializers.UUIDField(source='record_id')
    version = serializers.IntegerField(source='record.version')
    state = serializers.CharField(source='record.state')
    class Meta:
        model = CoordinationParticipant
        # These instructions are explicitly addressed to this officer. No other-case metadata is included.
        fields = ['id', 'coordination_id', 'version', 'state', 'instruction', 'action_date', 'acknowledged_at', 'completed_at', 'completion_note']


@api_view(['GET'])
def requests(request):
    if role(request.user) != 'officer': raise PermissionDenied('This inbox is for designated Bureau officers.')
    qs = CoordinationParticipant.objects.filter(officer=request.user, bureau_id__in=Membership.objects.filter(user=request.user, role='officer').values('bureau_id')).select_related('record').order_by('-record__created_at', '-id')
    return page(request, qs, RequestSerializer)
