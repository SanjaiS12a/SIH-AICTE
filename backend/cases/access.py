from django.db.models import Q, Exists, OuterRef
from rest_framework.exceptions import PermissionDenied
from .models import Complaint, Membership, Escalation

def role(user):
    return Membership.objects.filter(user_id=user.pk, user__is_active=True).values_list('role', flat=True).first() or ''

def current_bureau_id(user):
    return Membership.objects.filter(user_id=user.pk, user__is_active=True).values_list('bureau_id', flat=True).first()

def authorized_actions(user, qs):
    return qs if coordination(user) else qs.exclude(kind__startswith='coordination_group')

def coordination(user):
    return role(user) in ('coordinator', 'auditor')

def writable(user):
    if role(user) not in ('officer', 'coordinator'):
        raise PermissionDenied('Your account has read-only access.')

def scoped_cases(user):
    qs = Complaint.objects.select_related('institution', 'bureau', 'source_bureau', 'assigned_to', 'created_by').annotate(
        has_unresolved_escalation=Exists(Escalation.objects.filter(case_id=OuterRef('pk'), status='pending')))
    if coordination(user):
        return qs
    if role(user) == 'officer':
        return qs.filter(bureau_id__in=Membership.objects.filter(user_id=user.pk, role='officer', bureau__isnull=False).values('bureau_id'))
    return qs.none()

def filtered_cases(request):
    from .serializers import FilterSerializer
    form = FilterSerializer(data=request.query_params)
    form.is_valid(raise_exception=True)
    p = form.validated_data
    qs = scoped_cases(request.user)
    if p.get('import_id'):
        from .imports import get_job
        job = get_job(request.user, p['import_id'])
        qs = qs.filter(importrow__job=job, importrow__state__in=['imported', 'duplicate'])
    if p.get('q'):
        q = p['q']
        qs = qs.filter(Q(reference__icontains=q) | Q(source_reference__icontains=q) | Q(institution__name__icontains=q) | Q(institution__permanent_id__icontains=q) | Q(summary__icontains=q))
    for key in ('institution', 'bureau', 'region', 'district', 'category', 'classification', 'status'):
        if p.get(key):
            field = {'institution': 'institution_id', 'bureau': 'bureau__code', 'region': 'institution__region', 'district': 'institution__district__icontains'}.get(key, key)
            if key == 'district' and p.get('district_exact'): field = 'institution__district'
            qs = qs.filter(**{field: p[key]})
    if p.get('from'):
        qs = qs.filter(received_at__date__gte=p['from'])
    if p.get('to'):
        qs = qs.filter(received_at__date__lte=p['to'])
    if p.get('disposed_from'):
        qs = qs.filter(disposed_at__date__gte=p['disposed_from'])
    if p.get('disposed_to'):
        qs = qs.filter(disposed_at__date__lte=p['disposed_to'])
    if p.get('overdue'):
        from django.utils import timezone
        qs = qs.filter(due_at__lt=timezone.now()).exclude(status='disposed')
    if p.get('pending'):
        qs = qs.exclude(status='disposed')
    if p.get('under_process'):
        qs = qs.filter(status__in=['under_review', 'awaiting_response'])
    if p.get('closed'):
        qs = qs.filter(status='disposed')
    if p.get('escalated'):
        qs = qs.filter(has_unresolved_escalation=True)
    if p.get('approaching'):
        from datetime import timedelta
        from django.utils import timezone
        now = timezone.now()
        qs = qs.exclude(status='disposed').filter(due_at__gte=now, due_at__lte=now + timedelta(days=7))
    if p.get('age'):
        from datetime import timedelta
        from django.utils import timezone
        # Non-overlapping ageing bands based on received_at; pending cases only.
        # '30+' is equivalent to the original '31+' bucket.
        lo, hi = {'0-7': (0, 7), '8-15': (8, 15), '16-30': (16, 30), '30+': (31, None),
                  # Legacy aliases kept for backward compatibility with existing filter links.
                  '8-30': (8, 30), '31-60': (31, 60), '61+': (61, None)}[p['age']]
        now = timezone.now()
        qs = qs.exclude(status='disposed').filter(received_at__lte=now - timedelta(days=lo))
        if hi is not None:
            qs = qs.filter(received_at__gt=now - timedelta(days=hi + 1))
    return qs
