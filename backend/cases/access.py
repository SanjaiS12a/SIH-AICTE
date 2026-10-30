from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from .models import Complaint

def role(user):
    return user.membership.role if hasattr(user, 'membership') else ''

def coordination(user):
    return role(user) in ('coordinator', 'auditor')

def writable(user):
    if role(user) not in ('officer', 'coordinator'):
        raise PermissionDenied('Your account has read-only access.')

def scoped_cases(user):
    qs = Complaint.objects.select_related('institution', 'bureau', 'assigned_to', 'created_by')
    if coordination(user):
        return qs
    if role(user) == 'officer' and user.membership.bureau_id:
        return qs.filter(bureau_id=user.membership.bureau_id)
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
        qs = qs.filter(importrow__job=job)
    if p.get('q'):
        q = p['q']
        qs = qs.filter(Q(reference__icontains=q) | Q(source_reference__icontains=q) | Q(institution__name__icontains=q) | Q(institution__permanent_id__icontains=q) | Q(summary__icontains=q))
    for key in ('institution', 'bureau', 'region', 'category', 'status'):
        if p.get(key):
            field = {'institution': 'institution_id', 'bureau': 'bureau__code', 'region': 'institution__region'}.get(key, key)
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
    if p.get('age'):
        from datetime import timedelta
        from django.utils import timezone
        lo, hi = {'0-7': (0, 7), '8-30': (8, 30), '31-60': (31, 60), '61+': (61, None)}[p['age']]
        now = timezone.now()
        qs = qs.exclude(status='disposed').filter(received_at__lte=now - timedelta(days=lo))
        if hi is not None:
            qs = qs.filter(received_at__gt=now - timedelta(days=hi + 1))
    return qs
