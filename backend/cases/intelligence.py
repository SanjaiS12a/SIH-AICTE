"""Source-grounded briefs, reviewed spans and explicit incident membership."""
import hashlib
import re
from datetime import date
from django.conf import settings
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .access import role, coordination, scoped_cases, authorized_actions, current_bureau_id
from .api import Conflict, page
from .models import (Complaint, Institution, CaseAction, Escalation, OverlapCandidate,
                     CoordinationParticipant, ReviewedFact, IncidentGroup, IncidentMembership)
from .serializers import CaseSerializer, ActionReadSerializer


def feature(name):
    if not getattr(settings, name, False):
        raise Http404('Feature is disabled.')


def manager(user, write=False):
    allowed = role(user) == 'coordinator' if write else coordination(user)
    if not allowed:
        raise PermissionDenied('Coordinator access required.' if write else 'Management access required.')


def actions_for(user, case):
    return authorized_actions(user, CaseAction.objects.filter(case=case)).select_related('actor', 'bureau_at_action').order_by('-created_at', '-id')


@api_view(['GET'])
def brief(request, case_id):
    case = get_object_or_404(scoped_cases(request.user), pk=case_id)
    latest = actions_for(request.user, case).first()
    data = {'case': CaseSerializer(case).data, 'generated_at': timezone.now(),
            'allegation_label': 'Original allegation — not a verified finding',
            'latest_action': ActionReadSerializer(latest, context={'restricted': not coordination(request.user)}).data if latest else None,
            'pending_escalation': Escalation.objects.filter(case=case, status='pending').exists()}
    participants = CoordinationParticipant.objects.filter(record__cases=case, record__state='in_coordination').select_related('record', 'bureau', 'officer')
    if not coordination(request.user):
        participants = participants.filter(officer=request.user, bureau_id=current_bureau_id(request.user))
    data['responsibilities'] = [{'instruction': p.instruction, 'bureau': p.bureau.code, 'officer': p.officer.get_full_name() or p.officer.username,
        'action_date': p.action_date, 'acknowledged_at': p.acknowledged_at, 'completed_at': p.completed_at} for p in participants]
    if coordination(request.user):
        pairs = OverlapCandidate.objects.filter(Q(left=case) | Q(right=case))
        data['relationship_status'] = {'awaiting_review': pairs.filter(decision='pending').count(),
            'same_incident': pairs.filter(decision='same_incident').count(), 'related_issue': pairs.filter(decision='related_issue').count()}
    return Response(data)


@api_view(['GET'])
def history(request, case_id):
    case = get_object_or_404(scoped_cases(request.user), pk=case_id)
    return page(request, actions_for(request.user, case), ActionReadSerializer, context={'restricted': not coordination(request.user)})


class FactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewedFact
        fields = ['id','submission_id','case_id','kind','source_field','span_start','span_end','quote','source_digest',
                  'value','method','state','proposed_by_id','created_at','reviewer_id','reviewed_at','reason','version']


class FactInput(serializers.Serializer):
    submission_id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=['incident_date','reference','remedy'])
    source_field = serializers.ChoiceField(choices=['summary','description','source_reference'])
    span_start = serializers.IntegerField(min_value=0)
    span_end = serializers.IntegerField(min_value=1)
    quote = serializers.CharField(max_length=2000, trim_whitespace=False)
    source_digest = serializers.RegexField(r'^[a-f0-9]{64}$')
    value = serializers.CharField(max_length=2000)


class ReviewInput(serializers.Serializer):
    expected_version = serializers.IntegerField(min_value=1)
    state = serializers.ChoiceField(choices=['accepted','rejected'])
    reason = serializers.CharField(max_length=4000)


def validate_span(case, data):
    source = getattr(case, data['source_field'])
    if hashlib.sha256(source.encode('utf-8')).hexdigest() != data['source_digest']:
        raise Conflict('The source text changed. Reload and select the supporting span again.')
    if data['span_end'] > len(source) or data['span_start'] >= data['span_end'] or source[data['span_start']:data['span_end']] != data['quote']:
        raise ValidationError('The quoted span must match the source exactly.')
    if data['kind'] == 'incident_date':
        try:
            if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', data['quote'].strip()):
                raise ValueError()
            value = date.fromisoformat(data['quote'].strip()).isoformat()
        except ValueError:
            raise ValidationError('Date evidence must be an unambiguous ISO date (YYYY-MM-DD).')
    else:
        value = data['quote'].strip()
    if data['value'] != value:
        raise ValidationError('The proposed value must be the selected evidence, with only whitespace or ISO-date normalization.')


@api_view(['GET','POST'])
def facts(request, case_id):
    feature('ENABLE_REVIEWED_FACTS')
    case = get_object_or_404(scoped_cases(request.user), pk=case_id)
    if request.method == 'GET':
        return page(request, ReviewedFact.objects.filter(case=case), FactSerializer)
    if role(request.user) not in ('officer','coordinator'):
        raise PermissionDenied('Read-only account.')
    form = FactInput(data=request.data); form.is_valid(raise_exception=True)
    d = form.validated_data
    with transaction.atomic():
        Institution.objects.select_for_update().get(pk=case.institution_id)
        case = get_object_or_404(scoped_cases(request.user).select_for_update(of=('self',)), pk=case_id)
        validate_span(case, d)
        existing = ReviewedFact.objects.filter(submission_id=d['submission_id']).first()
        if existing:
            if existing.case_id != case.pk or existing.proposed_by_id != request.user.pk or any(getattr(existing,k) != v for k,v in d.items()):
                raise Conflict('Submission ID already used for different evidence.')
            return Response(FactSerializer(existing).data)
        try:
            with transaction.atomic():
                obj = ReviewedFact.objects.create(case=case, proposed_by=request.user, **d)
        except IntegrityError:
            raise Conflict('Submission ID was used concurrently. Reload before retrying.')
        CaseAction.objects.create(case=case, actor=request.user, kind='fact_proposed', reason='Source-grounded fact proposed for review.',
            changes={'fact_id':str(obj.pk),'kind':obj.kind,'source_field':obj.source_field,'quote':obj.quote,'source_digest':obj.source_digest,'state':'pending'})
    return Response(FactSerializer(obj).data, status=201)


@api_view(['POST'])
def review_fact(request, case_id, fact_id):
    feature('ENABLE_REVIEWED_FACTS'); manager(request.user, write=True)
    case = get_object_or_404(scoped_cases(request.user), pk=case_id)
    form = ReviewInput(data=request.data); form.is_valid(raise_exception=True); d = form.validated_data
    with transaction.atomic():
        Institution.objects.select_for_update().get(pk=case.institution_id)
        case = Complaint.objects.select_for_update().get(pk=case.pk)
        obj = get_object_or_404(ReviewedFact.objects.select_for_update(), pk=fact_id, case=case)
        if obj.version != d['expected_version']: raise Conflict()
        if d['state'] == 'accepted':
            validate_span(case, {key:getattr(obj,key) for key in ['kind','source_field','span_start','span_end','quote','source_digest','value']})
        previous = obj.state
        obj.state, obj.reason, obj.reviewer, obj.reviewed_at = d['state'], d['reason'], request.user, timezone.now()
        obj.version += 1; obj.save()
        CaseAction.objects.create(case=case, actor=request.user, kind='fact_reviewed', reason=d['reason'],
            changes={'fact_id':str(obj.pk),'state':{'before':previous,'after':obj.state},'version':obj.version})
    return Response(FactSerializer(obj).data)


class GroupInput(serializers.Serializer):
    submission_id = serializers.UUIDField(required=False)
    expected_version = serializers.IntegerField(min_value=1, required=False)
    institution = serializers.UUIDField()
    title = serializers.CharField(max_length=180)
    reason = serializers.CharField(max_length=4000)
    cases = serializers.ListField(child=serializers.UUIDField(), min_length=2, max_length=20)
    supporting_relationship = serializers.IntegerField(min_value=1, allow_null=True, default=None)

    def validate_cases(self, values):
        if len(set(values)) != len(values): raise ValidationError('Select each case once.')
        return values


class GroupSerializer(serializers.ModelSerializer):
    cases = serializers.SerializerMethodField()
    def get_cases(self, obj):
        return [{'id':str(m.case_id),'reference':m.case.reference} for m in obj.memberships.all() if m.active]
    class Meta:
        model = IncidentGroup
        fields = ['id','submission_id','institution_id','title','reason','reviewer_id','supporting_relationship_id','needs_review','version','created_at','cases']


def group_query():
    from django.db.models import Prefetch
    return IncidentGroup.objects.prefetch_related(Prefetch('memberships',queryset=IncidentMembership.objects.select_related('case')))


def group_audit(group, actor, reason, before, after, kind='coordination_group_changed', profile_before=None):
    for case_id in sorted(set(before) | set(after)):
        CaseAction.objects.create(case_id=case_id, actor=actor, kind=kind, reason=reason,
            changes={'group_id':str(group.pk),'version':group.version,'before':[str(v) for v in before],
                     'after':[str(v) for v in after],'needs_review':group.needs_review,'supporting_relationship_id':group.supporting_relationship_id,
                     'profile':{'before':profile_before or {},'after':group_profile(group)}})


def group_profile(group):
    return {'title':group.title,'reason':group.reason,'reviewer_id':group.reviewer_id,
            'supporting_relationship_id':group.supporting_relationship_id,'needs_review':group.needs_review,'version':group.version}


def flag_supporting_groups(pair, actor, reason):
    for group in IncidentGroup.objects.select_for_update().filter(supporting_relationship=pair).order_by('id'):
        previous = group_profile(group)
        group.needs_review = True; group.version += 1; group.save(update_fields=['needs_review','version'])
        ids = list(group.memberships.filter(active=True).values_list('case_id',flat=True))
        group_audit(group, actor, reason, ids, ids, 'coordination_group_review', previous)


@api_view(['GET','POST'])
def groups(request):
    feature('ENABLE_INCIDENT_GROUPS'); manager(request.user, write=request.method=='POST')
    if request.method == 'GET':
        form = serializers.UUIDField()
        institution = form.run_validation(request.query_params.get('institution'))
        return page(request, group_query().filter(institution_id=institution), GroupSerializer)
    return save_group(request)


@api_view(['PATCH'])
def edit_group(request, group_id):
    feature('ENABLE_INCIDENT_GROUPS'); manager(request.user, write=True)
    return save_group(request, group_id)


def save_group(request, group_id=None):
    form = GroupInput(data=request.data); form.is_valid(raise_exception=True); d = form.validated_data
    if group_id and 'expected_version' not in d: raise ValidationError('Expected version required.')
    if not group_id and 'submission_id' not in d: raise ValidationError('Submission ID required.')
    with transaction.atomic():
        institution = get_object_or_404(Institution.objects.select_for_update(), pk=d['institution'])
        pair = None
        if d['supporting_relationship']:
            pair = get_object_or_404(OverlapCandidate.objects.select_for_update(), pk=d['supporting_relationship'])
            if pair.decision != 'same_incident' or pair.left_id not in d['cases'] or pair.right_id not in d['cases']:
                raise ValidationError('Supporting relationship must be a reviewed same-incident pair within the selected cases.')
        group = get_object_or_404(IncidentGroup.objects.select_for_update(), pk=group_id, institution=institution) if group_id else None
        cases = list(scoped_cases(request.user).select_for_update(of=('self',)).filter(pk__in=d['cases'], institution=institution).order_by('id'))
        if len(cases) != len(d['cases']): raise ValidationError('Select authorized cases from one institution.')
        before = list(group.memberships.filter(active=True).values_list('case_id',flat=True)) if group else []
        previous = group_profile(group) if group else {}
        if group:
            if group.version != d['expected_version']: raise Conflict()
            group.version += 1
        else:
            existing = IncidentGroup.objects.filter(submission_id=d['submission_id']).first()
            if existing:
                member_ids = set(existing.memberships.filter(active=True).values_list('case_id',flat=True))
                if existing.institution_id != institution.pk or existing.reviewer_id != request.user.pk or existing.title != d['title'] or existing.reason != d['reason'] or member_ids != set(d['cases']) or existing.supporting_relationship_id != d['supporting_relationship']:
                    raise Conflict('Submission ID already used for a different group.')
                return Response(GroupSerializer(group_query().get(pk=existing.pk)).data)
            group = IncidentGroup(submission_id=d['submission_id'],institution=institution)
        group.title, group.reason, group.reviewer = d['title'], d['reason'], request.user
        group.supporting_relationship, group.needs_review = pair, False
        try:
            with transaction.atomic():
                group.save()
        except IntegrityError:
            raise Conflict('Submission ID was used concurrently. Reload before retrying.')
        for case_id in set(before) | set(d['cases']):
            IncidentMembership.objects.update_or_create(group=group, case_id=case_id,
                defaults={'active':case_id in d['cases'],'reason':d['reason'],'actor':request.user,'updated_at':timezone.now()})
        group_audit(group, request.user, d['reason'], before, d['cases'], profile_before=previous)
    return Response(GroupSerializer(group_query().get(pk=group.pk)).data, status=200 if group_id else 201)
