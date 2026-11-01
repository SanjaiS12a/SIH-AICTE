import csv
import hashlib
import io
import json
import uuid
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.db.models import Count, Q, Prefetch, F
from django.db.models.functions import TruncMonth
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_q.tasks import async_task
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError, APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from .access import role, coordination, writable, scoped_cases, filtered_cases, current_bureau_id
from .models import Institution, Bureau, Complaint, CaseAction, OverlapCandidate, Attachment, Notification, AuditEvent, Escalation
from .serializers import (InstitutionSerializer, CaseSerializer, CreateCaseSerializer, ActionSerializer,
                          ActionReadSerializer, AttachmentSerializer, ReviewSerializer)

class Conflict(APIException):
    status_code = 409
    default_detail = 'This record changed. Refresh it before saving again.'

def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        response.data = {'error': response.data}
    return response

def page(request, qs, serializer, context=None):
    paginator = PageNumberPagination()
    rows = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(serializer(rows, many=True, context=context or {}).data)

@api_view(['GET'])
@permission_classes([AllowAny])
def session(request):
    get_token(request)
    if not request.user.is_authenticated:
        return Response({'user': None})
    bureau = Bureau.objects.filter(pk=current_bureau_id(request.user)).values_list('code', flat=True).first()
    return Response({'user': {'id': request.user.id, 'name': request.user.get_full_name() or request.user.username,
                             'username': request.user.username, 'role': role(request.user),
                             'bureau': bureau},
                     'policy': {'deadline_days': settings.DEMO_DEADLINE_DAYS, 'label': 'Demonstration policy, not an AICTE rule'}})

@api_view(['GET'])
def institutions(request):
    qs = Institution.objects.order_by('name')
    if request.query_params.get('q'):
        qs = qs.filter(Q(name__icontains=request.query_params['q']) | Q(permanent_id__icontains=request.query_params['q']))
    return Response(InstitutionSerializer(qs[:100], many=True).data)

@api_view(['GET'])
def options(request):
    bureaus = Bureau.objects.order_by('code')
    users = User.objects.filter(is_active=True, membership__role='officer')
    if not coordination(request.user):
        bureaus = bureaus.filter(id=current_bureau_id(request.user)) if role(request.user) == 'officer' else bureaus.none()
        users = users.filter(membership__bureau_id=current_bureau_id(request.user)) if role(request.user) == 'officer' else users.none()
    return Response({'bureaus': list(bureaus.values('code', 'name')),
                     'officers': [{'id': u.id, 'name': u.get_full_name(), 'bureau': u.membership.bureau.code} for u in users.select_related('membership__bureau')],
                     'regions': list(Institution.objects.order_by('region').values_list('region', flat=True).distinct())})

@api_view(['GET', 'POST'])
def cases(request):
    if request.method == 'GET':
        return page(request, filtered_cases(request), CaseSerializer)
    writable(request.user)
    data = CreateCaseSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    d = data.validated_data
    original = {key: str(value.pk if hasattr(value, 'pk') else value) for key, value in d.items()}
    if d['classification'] == 'unclassified':
        original.pop('classification', None)  # Preserve pre-classification submission fingerprints.
    if 'received_at' not in request.data:
        original.pop('received_at', None)
    fingerprint = hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()
    if role(request.user) == 'officer' and d['bureau'].id != current_bureau_id(request.user):
        raise PermissionDenied('Officers can register cases only in their own bureau.')

    def replay(existing):
        if existing.created_by_id != request.user.id or not scoped_cases(request.user).filter(pk=existing.pk).exists():
            raise PermissionDenied('This submission identifier is already in use.')
        if existing.submission_fingerprint != fingerprint:
            raise Conflict('Submission ID was reused with different complaint content.')
        return Response(CaseSerializer(existing).data)

    with transaction.atomic():
        existing = Complaint.objects.filter(submission_id=d['submission_id']).first()
        if existing:
            return replay(existing)
        try:
            with transaction.atomic():
                case = Complaint.objects.create(**d, created_by=request.user, submission_fingerprint=fingerprint,
                    reference=f'C-{timezone.now():%y%m}-{uuid.uuid4().hex[:8].upper()}',
                    due_at=d['received_at'] + timedelta(days=settings.DEMO_DEADLINE_DAYS))
        except IntegrityError:
            existing = Complaint.objects.filter(submission_id=d['submission_id']).first()
            if existing:
                return replay(existing)
            raise Conflict('The source reference or submission ID already exists.')
        CaseAction.objects.create(case=case, actor=request.user, kind='registered', reason='Complaint registered', changes={'bureau': case.bureau.code, 'classification': case.classification})
        async_task('cases.matching.match_case', str(case.id))
    return Response(CaseSerializer(case).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def case_detail(request, case_id):
    case = get_object_or_404(scoped_cases(request.user), pk=case_id)
    data = CaseSerializer(case).data
    data['actions'] = ActionReadSerializer(case.actions.select_related('actor', 'bureau_at_action'), many=True,
                                         context={'restricted': not coordination(request.user)}).data
    data['attachments'] = AttachmentSerializer(case.attachments.all(), many=True).data
    history = scoped_cases(request.user).filter(institution=case.institution).exclude(pk=case.id)[:20]
    data['institution_history'] = CaseSerializer(history, many=True).data
    return Response(data)

@api_view(['POST'])
def actions(request, case_id):
    writable(request.user)
    serializer = ActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data
    with transaction.atomic():
        case = get_object_or_404(scoped_cases(request.user).select_for_update(of=('self',)), pk=case_id)
        if case.version != d['expected_version']:
            raise Conflict()
        kind, changes = d['kind'], {}
        if kind in ('transfer', 'assign', 'deadline', 'retry_matching', 'classification') and role(request.user) != 'coordinator':
            raise PermissionDenied('This action requires a coordinator.')
        if kind == 'status':
            if case.status == d['status']:
                raise ValidationError('Choose a different status.')
            if case.status == 'disposed' and role(request.user) != 'coordinator':
                raise PermissionDenied('Reopening requires a coordinator.')
            changes = {'status': {'before': case.status, 'after': d['status']}}
            case.status = d['status']
            case.disposed_at = timezone.now() if case.status == 'disposed' else None
            if case.status == 'disposed':
                changes.update(next_action={'before': case.next_action, 'after': ''},
                               next_action_date={'before': case.next_action_date.isoformat() if case.next_action_date else None, 'after': None})
                case.next_action, case.next_action_date = '', None
        elif kind == 'classification':
            if case.classification == d['classification']:
                raise ValidationError('Choose a different classification.')
            changes = {'classification': {'before': case.classification, 'after': d['classification']}}
            case.classification = d['classification']
        elif kind == 'next_action':
            if case.status == 'disposed':
                raise ValidationError('Reopen the case before setting its next action.')
            expected_date = d.get('next_action_date')
            changes = {'next_action': {'before': case.next_action, 'after': d['next_action']},
                       'next_action_date': {'before': case.next_action_date.isoformat() if case.next_action_date else None,
                                            'after': expected_date.isoformat() if expected_date else None}}
            case.next_action, case.next_action_date = d['next_action'], expected_date
        elif kind == 'transfer':
            if case.bureau_id == d['bureau'].id:
                raise ValidationError('Choose a different bureau.')
            changes = {'bureau': {'before': case.bureau.code, 'after': d['bureau'].code}, 'assigned_to': {'before': case.assigned_to_id, 'after': None}}
            case.bureau, case.assigned_to = d['bureau'], None
        elif kind == 'assign':
            officer = d['assigned_to']
            if officer and (role(officer) != 'officer' or current_bureau_id(officer) != case.bureau_id):
                raise ValidationError('Select an active officer from the case bureau.')
            changes = {'assigned_to': {'before': case.assigned_to_id, 'after': officer.id if officer else None}}
            case.assigned_to = officer
        elif kind == 'deadline':
            if d['due_at'] < case.received_at:
                raise ValidationError('Deadline cannot precede receipt.')
            changes = {'due_at': {'before': case.due_at.isoformat(), 'after': d['due_at'].isoformat()}}
            case.due_at = d['due_at']
        elif kind == 'retry_matching':
            case.matching_state, case.matching_error = 'pending', ''
            async_task('cases.matching.match_case', str(case.id))
        case.version += 1
        case.save()
        CaseAction.objects.create(case=case, actor=request.user, kind=kind, reason=d['reason'], changes=changes)
    return Response(CaseSerializer(case).data)

def overlap_data(obj):
    return {'id': obj.id, 'left': CaseSerializer(obj.left).data, 'right': CaseSerializer(obj.right).data,
            'score': obj.score, 'origin': obj.origin, 'evidence': obj.evidence, 'decision': obj.decision,
            'reason': obj.reason, 'model_revision': obj.model_revision, 'version': obj.version,
            'reviewed_at': obj.reviewed_at, 'reviewer': obj.reviewer.get_full_name() if obj.reviewer else None}

@api_view(['GET'])
def overlaps(request):
    qs = overlap_queryset(request)
    paginator = PageNumberPagination()
    rows = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response([overlap_data(o) for o in rows])


def overlap_queryset(request):
    if not coordination(request.user):
        raise PermissionDenied('Cross-bureau review requires coordination access.')
    qs = OverlapCandidate.objects.select_related('left__institution', 'right__institution', 'left__bureau', 'right__bureau', 'left__assigned_to', 'right__assigned_to', 'left__source_bureau', 'right__source_bureau', 'reviewer')
    qs = qs.prefetch_related(*[Prefetch(f'{side}__escalations',queryset=Escalation.objects.filter(status='pending'),to_attr='pending_escalations') for side in ['left','right']])
    decision = request.query_params.get('decision', 'pending')
    if decision != 'all':
        if decision not in ('pending', 'same_incident', 'related_issue', 'unrelated'):
            raise ValidationError('Invalid review filter.')
        qs = qs.filter(decision=decision)
    ids = filtered_cases(request).values('pk')
    qs = qs.filter(Q(left_id__in=ids) | Q(right_id__in=ids))
    if request.query_params.get('pair'):
        from rest_framework import serializers
        qs = qs.filter(pk=serializers.IntegerField(min_value=1).run_validation(request.query_params['pair']))
    return qs

@api_view(['POST'])
def review(request, overlap_id):
    if role(request.user) != 'coordinator':
        raise PermissionDenied('Only coordinators can record a review.')
    form = ReviewSerializer(data=request.data)
    form.is_valid(raise_exception=True)
    d = form.validated_data
    record = get_object_or_404(OverlapCandidate.objects.select_related('left'), pk=overlap_id)
    with transaction.atomic():
        Institution.objects.select_for_update().get(pk=record.left.institution_id)
        obj = get_object_or_404(OverlapCandidate.objects.select_for_update(), pk=overlap_id)
        from .relationships import decide
        decide(obj, request.user, d['decision'], d['reason'], d['expected_version'])
    return Response({'id': obj.id, 'decision': obj.decision, 'version': obj.version})

@api_view(['GET'])
def dashboard(request):
    return Response(dashboard_data(request))

def dashboard_data(request):
    # Officers always query their current bureau; no cached restricted rows or counts.
    if not coordination(request.user):
        return compute_dashboard(request)
    from django.core.cache import caches
    cache = caches['dashboard']
    filtered_cases(request)  # Validate filters and import access before consulting the cache.
    key = 'dashboard:' + hashlib.sha256(json.dumps(sorted(request.query_params.items()), default=str).encode()).hexdigest()
    data = cache.get(key)
    if data is not None:
        return data
    from django.db import connection
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [int(key[-15:], 16)])
        data = cache.get(key)
        if data is None:
            data = compute_dashboard(request)
            cache.set(key, data, timeout=5)
    return data


def compute_dashboard(request):
    qs, now = filtered_cases(request), timezone.now()
    pending = qs.exclude(status='disposed')
    months = qs.annotate(month=TruncMonth('received_at')).values('month').annotate(count=Count('id')).order_by('month')
    disposed_months = qs.filter(disposed_at__isnull=False).annotate(month=TruncMonth('disposed_at')).values('month').annotate(count=Count('id'))
    disposal_map = {x['month'].strftime('%Y-%m'): x['count'] for x in disposed_months}
    month_map = {x['month'].strftime('%Y-%m'): {'month': x['month'].strftime('%Y-%m'), 'received': x['count'], 'disposed': 0} for x in months}
    for month, count in disposal_map.items():
        month_map.setdefault(month, {'month': month, 'received': 0, 'disposed': 0})['disposed'] = count
    aggregate = {'total': Count('id'), 'pending': Count('id', filter=~Q(status='disposed')),
                 'institutions': Count('institution',distinct=True),
                 'approaching': Count('id',filter=~Q(status='disposed') & Q(due_at__gte=now,due_at__lte=now+timedelta(days=7))),
                 'unresolved_escalations': Count('id',filter=Q(has_unresolved_escalation=True)),
                 'overdue': Count('id', filter=~Q(status='disposed') & Q(due_at__lt=now)),
                 'under_process': Count('id', filter=Q(status__in=['under_review','awaiting_response']))}
    for status in dict(Complaint.STATUSES):
        aggregate[status] = Count('id', filter=Q(status=status))
    # Ageing bands for pending cases — based on actual received_at timestamps.
    # Bands are: 0-7, 8-15, 16-30, 30+ days. Non-overlapping, non-disposed only.
    age_ranges = [('0-7 days', 0, 7), ('8-15 days', 8, 15), ('16-30 days', 16, 30), ('More than 30 days', 31, None)]
    for index, (label, lo, hi) in enumerate(age_ranges):
        condition = ~Q(status='disposed') & Q(received_at__lte=now-timedelta(days=lo))
        if hi is not None:
            condition &= Q(received_at__gt=now-timedelta(days=hi+1))
        aggregate[f'age_{index}'] = Count('id', filter=condition)
    totals = qs.aggregate(**aggregate)
    workload = list(pending.values('bureau__code','bureau__name').annotate(
        count=Count('id'),
        overdue=Count('id',filter=Q(due_at__lt=now)),
        approaching=Count('id',filter=Q(due_at__gte=now,due_at__lte=now+timedelta(days=7))),
        institutions=Count('institution',distinct=True),
    ).order_by('bureau__code'))
    data = {k: totals[k] for k in ['total', 'pending', 'overdue', 'disposed','institutions','approaching','unresolved_escalations','under_process']}
    data['closed_share']=totals['disposed']/totals['total'] if totals['total'] else 0
    data.update({'workload': workload, 'statuses': [{'status': status, 'count': totals[status]} for status in dict(Complaint.STATUSES)],
                 'ageing': [{'name': row[0], 'count': totals[f'age_{i}']} for i, row in enumerate(age_ranges)],
                 'trend': [month_map[k] for k in sorted(month_map)], 'generated_at': now,
                 'recent': CaseSerializer(qs[:5], many=True).data,
                 'attention': CaseSerializer(pending.order_by('due_at','id')[:8], many=True).data,
                 'active_categories': list(pending.values('category').annotate(count=Count('id')).order_by('-count'))})
    if coordination(request.user):
        ids = qs.values('pk')
        data['overlap_reviews'] = OverlapCandidate.objects.filter(decision='pending').filter(Q(left_id__in=ids) | Q(right_id__in=ids)).count()
        from .coordination import groups
        multi = groups(request)
        data['coordination_institutions'] = multi.count()
        data['coordination_notices'] = list(multi[:10])
        from .analytics import analytics
        data['management']=analytics(request,qs,pending,now)
    data['categories'] = list(qs.values('category').annotate(count=Count('id')).order_by('-count'))
    data['overdue_bureaus'] = sorted([{'bureau__code': b['bureau__code'], 'bureau__name': b.get('bureau__name',''), 'count': b['overdue']} for b in workload if b['overdue']], key=lambda b: -b['count'])
    data['matching'] = dict(qs.order_by().values_list('matching_state').annotate(n=Count('id')).values_list('matching_state','n'))
    data['filters'] = dict(request.query_params)
    return data

@api_view(['GET'])
def report(request):
    qs = filtered_cases(request)
    AuditEvent.objects.create(actor=request.user, kind='export', detail={'count': qs.count(), 'filters': dict(request.query_params)})
    from .exports import CASE_COLUMNS, case_values
    def chunks():
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(CASE_COLUMNS)
        yield stream.getvalue()
        for c in qs.select_related('source_bureau').iterator(chunk_size=1000):
            stream.seek(0); stream.truncate(0)
            writer.writerow(case_values(c))
            yield stream.getvalue()
    return StreamingHttpResponse(chunks(), content_type='text/csv', headers={'Content-Disposition': 'attachment; filename="case-report.csv"'})

@api_view(['POST'])
def upload(request, case_id):
    writable(request.user)
    case = get_object_or_404(scoped_cases(request.user), pk=case_id)
    f = request.FILES.get('file')
    if not f or f.size > 5 * 1024 * 1024 or f.size == 0:
        raise ValidationError('Select a non-empty PDF, PNG or JPEG up to 5 MB.')
    suffix = Path(f.name).suffix.lower()
    if suffix not in ('.pdf', '.png', '.jpg', '.jpeg'):
        raise ValidationError('Only PDF, PNG and JPEG are supported.')
    try:
        if suffix == '.pdf':
            from pypdf import PdfReader
            if not f.read(5) == b'%PDF-':
                raise ValueError('Invalid PDF signature')
            f.seek(0)
            reader = PdfReader(f, strict=True)
            if reader.is_encrypted or not len(reader.pages):
                raise ValueError('Encrypted or empty PDF')
            content_type = 'application/pdf'
        else:
            from PIL import Image
            image = Image.open(f)
            expected = 'PNG' if suffix == '.png' else 'JPEG'
            if image.format != expected:
                raise ValueError('Image type mismatch')
            image.verify()
            content_type = 'image/png' if expected == 'PNG' else 'image/jpeg'
        f.seek(0)
    except Exception:
        raise ValidationError('The file content is invalid or unsupported.')
    attachment = Attachment(case=case, original_name=Path(f.name).name[:180], content_type=content_type, size=f.size, uploaded_by=request.user)
    try:
        with transaction.atomic():
            # Recheck ownership under lock so a transfer cannot race the upload.
            case = get_object_or_404(scoped_cases(request.user).select_for_update(of=('self',)), pk=case_id)
            attachment.file.save(f'{uuid.uuid4().hex}{suffix}', f, save=False)
            attachment.save()
            CaseAction.objects.create(case=case, actor=request.user, kind='attachment', reason='Supporting document uploaded', changes={'attachment_id': str(attachment.id)})
    except Exception:
        if attachment.file.name:
            attachment.file.delete(save=False)
        raise
    return Response(AttachmentSerializer(attachment).data, status=201)

@api_view(['GET'])
def download(request, attachment_id):
    attachment = get_object_or_404(Attachment.objects.filter(case__in=scoped_cases(request.user)), pk=attachment_id)
    AuditEvent.objects.create(actor=request.user, kind='attachment_download', detail={'attachment_id': str(attachment.id)})
    return FileResponse(attachment.file.open('rb'), as_attachment=True, filename=attachment.original_name,
                        content_type='application/octet-stream', headers={'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'no-store'})

@api_view(['GET', 'POST'])
def notifications(request):
    qs = Notification.objects.filter(user=request.user, case__in=scoped_cases(request.user)).select_related('case', 'escalation')
    now = timezone.now()
    actionable = ~Q(case__status='disposed') & Q(deadline=F('case__due_at')) & (
        Q(kind='overdue', deadline__lt=now) |
        Q(kind='due_1_day', deadline__gte=now, deadline__lte=now+timedelta(days=1)) |
        Q(kind='due_7_days', deadline__gt=now+timedelta(days=1), deadline__lte=now+timedelta(days=7)))
    qs = qs.filter(Q(escalation__isnull=False) | actionable)
    if not request.user.is_active:
        qs = qs.none()
    elif role(request.user) != 'coordinator':
        qs = qs.filter(escalation__isnull=True)
    if request.method == 'POST':
        qs.filter(read=False).update(read=True)
        return Response({'ok': True})
    return Response({'unread': qs.filter(read=False).count(), 'results': [
        {'id': n.id, 'case_id': n.case_id, 'reference': n.case.reference, 'kind': n.kind,
         'deadline': n.deadline, 'read': n.read, 'created_at': n.created_at,
         'escalation_id': n.escalation_id, 'escalation_status': n.escalation.status if n.escalation_id else None} for n in qs[:30]]})
