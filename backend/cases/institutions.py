from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .access import coordination, filtered_cases, role, scoped_cases
from .api import Conflict, page
from .models import AuditEvent, CaseAction, Institution, Complaint
from .serializers import ActionReadSerializer, CaseSerializer, InstitutionSerializer, FilterSerializer


PROFILE_FIELDS = ['name', 'permanent_id', 'region', 'district', 'address', 'official_email', 'official_phone']


class InstitutionProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', *PROFILE_FIELDS, 'version']
        read_only_fields = ['id', 'version']


class InstitutionHistorySerializer(ActionReadSerializer):
    case_id = serializers.UUIDField()
    reference = serializers.CharField(source='case.reference')

    class Meta(ActionReadSerializer.Meta):
        fields = [*ActionReadSerializer.Meta.fields, 'case_id', 'reference']


class InstitutionWriteSerializer(serializers.ModelSerializer):
    expected_version = serializers.IntegerField(min_value=1, required=False, write_only=True)
    reason = serializers.CharField(max_length=4000, write_only=True)
    official_phone = serializers.RegexField(r'^[0-9+().\s-]+$', max_length=30, required=False, allow_blank=True)

    class Meta:
        model = Institution
        fields = [*PROFILE_FIELDS, 'expected_version', 'reason']

    def validate(self, data):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise ValidationError({key: 'Unknown field.' for key in sorted(unknown)})
        if self.instance:
            if data.get('permanent_id', self.instance.permanent_id) != self.instance.permanent_id:
                raise ValidationError({'permanent_id': 'Permanent ID cannot be changed.'})
            if 'expected_version' not in data:
                raise ValidationError({'expected_version': 'This field is required.'})
        return data


def save_profile(actor, values, institution_id=None, expected_version=None, reason=''):
    with transaction.atomic():
        institution = get_object_or_404(Institution.objects.select_for_update(), pk=institution_id) if institution_id else None
        if institution and institution.version != expected_version:
            raise Conflict()
        if institution and values.get('permanent_id', institution.permanent_id) != institution.permanent_id:
            raise ValidationError({'permanent_id': 'Permanent ID cannot be changed.'})
        before = {key: getattr(institution, key) for key in PROFILE_FIELDS} if institution else {}
        if institution:
            for key, value in values.items():
                setattr(institution, key, value)
            institution.version += 1
            institution.save()
        else:
            institution = Institution.objects.create(**values)
        changes = {key: {'before': before.get(key), 'after': getattr(institution, key)}
                   for key in PROFILE_FIELDS if key not in before or before[key] != getattr(institution, key)}
        AuditEvent.objects.create(actor=actor, kind='institution_updated' if before else 'institution_created',
                                  detail={'institution_id': str(institution.pk), 'reason': reason,
                                          'version': institution.version, 'changes': changes})
        return institution


def require_reader(user):
    if role(user) not in ('officer', 'coordinator', 'auditor'):
        raise PermissionDenied('Institution access requires a bureau role.')


@api_view(['GET', 'POST'])
def registry(request):
    require_reader(request.user)
    if request.method == 'POST':
        if role(request.user) != 'coordinator':
            raise PermissionDenied('Only coordinators can register institutions.')
        form = InstitutionWriteSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        values = dict(form.validated_data)
        reason = values.pop('reason')
        values.pop('expected_version', None)
        try:
            institution = save_profile(request.user, values, reason=reason)
        except IntegrityError:
            raise Conflict('This permanent ID already exists.')
        return Response(InstitutionProfileSerializer(institution).data, status=201)
    # Registry searches identity; case filters select institutions through scoped cases.
    qs = Institution.objects.order_by('name', 'id')
    params = request.query_params
    cases = filtered_cases(request)
    if params.get('q'):
        qs = qs.filter(Q(name__icontains=params['q']) | Q(permanent_id__icontains=params['q']))
    if params.get('region'):
        qs = qs.filter(region=params['region'])
    if params.get('institution'):
        qs = qs.filter(pk=params['institution'])
    filters = FilterSerializer(data=params)
    filters.is_valid(raise_exception=True)
    if filters.validated_data.get('district'):
        qs = qs.filter(district__icontains=filters.validated_data['district'])
    case_filters = set(filters.fields) - {'q', 'region', 'district', 'institution'}
    if any(filters.validated_data.get(key) for key in case_filters):
        qs = qs.filter(pk__in=cases.values('institution_id'))
    return page(request, qs, InstitutionSerializer)


@api_view(['GET', 'PATCH'])
def detail(request, institution_id):
    require_reader(request.user)
    institution = get_object_or_404(Institution, pk=institution_id)
    if request.method == 'PATCH':
        if role(request.user) != 'coordinator':
            raise PermissionDenied('Only coordinators can edit institutions.')
        form = InstitutionWriteSerializer(institution, data=request.data, partial=True)
        form.is_valid(raise_exception=True)
        values = dict(form.validated_data)
        if 'reason' not in values:
            raise ValidationError({'reason': 'This field is required.'})
        institution = save_profile(request.user, values={key: value for key, value in values.items() if key in PROFILE_FIELDS},
                                   institution_id=institution_id, expected_version=values['expected_version'], reason=values['reason'])
        return Response(InstitutionProfileSerializer(institution).data)
    cases = scoped_cases(request.user).filter(institution=institution)
    now = timezone.now()
    overview = cases.aggregate(total=Count('id'), open=Count('id', filter=~Q(status='disposed')),
                               closed=Count('id', filter=Q(status='disposed')),
                               overdue=Count('id', filter=~Q(status='disposed') & Q(due_at__lt=now)),
                               unresolved_escalations=Count('id', filter=Q(has_unresolved_escalation=True)))
    data = InstitutionProfileSerializer(institution).data
    data.update(overview=overview, scope='all_bureaus' if coordination(request.user) else 'current_bureau',
                classifications=[{'classification': value, 'count': cases.filter(classification=value).count()} for value, _ in Complaint.CLASSIFICATIONS],
                history_period='all_time', bureaus=list(cases.order_by('bureau__code').values('bureau__code', 'bureau__name').annotate(count=Count('id'))),
                cases_url=f'/api/institutions/{institution_id}/cases', history_url=f'/api/institutions/{institution_id}/history')
    return Response(data)


@api_view(['GET'])
def institution_cases(request, institution_id):
    require_reader(request.user)
    get_object_or_404(Institution, pk=institution_id)
    return page(request, filtered_cases(request).filter(institution_id=institution_id), CaseSerializer)


@api_view(['GET'])
def history(request, institution_id):
    require_reader(request.user)
    get_object_or_404(Institution, pk=institution_id)
    cases = scoped_cases(request.user).filter(institution_id=institution_id)
    actions = CaseAction.objects.filter(case__in=cases).select_related('actor', 'case').order_by('-created_at', '-id')
    return page(request, actions, InstitutionHistorySerializer, context={'restricted': not coordination(request.user)})
