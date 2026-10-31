"""All-time activity notices derive from current ownership, never model scores."""
from django.db.models import Count, Window, F
from django.db.models.functions import RowNumber
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .access import scoped_cases, coordination
from .models import OverlapCandidate
from .serializers import FilterSerializer, CaseSerializer


def active_cases(request):
    form=FilterSerializer(data=request.query_params);form.is_valid(raise_exception=True)
    p=form.validated_data
    qs=scoped_cases(request.user).exclude(status='disposed')
    # Select institutions geographically; always count every active bureau/category/date within them.
    for key,field in [('institution','institution_id'),('region','institution__region'),('district','institution__district__icontains')]:
        if p.get(key):qs=qs.filter(**{field:p[key]})
    return qs


def groups(request):
    return active_cases(request).order_by().values('institution_id','institution__name','institution__permanent_id',
        'institution__region','institution__district').annotate(bureaus=Count('bureau',distinct=True),count=Count('id')).filter(bureaus__gte=2).order_by('-count','institution_id')


def enrich(request, rows):
    rows=list(rows)
    if not rows:return rows
    ids=[r['institution_id'] for r in rows]
    active=active_cases(request).filter(institution_id__in=ids)
    bureaus=list(active.order_by().values('institution_id','bureau__code','bureau__name').annotate(count=Count('id')))
    officers=list(active.order_by().values('institution_id','assigned_to_id','assigned_to__first_name','assigned_to__last_name','assigned_to__username').annotate(count=Count('id')))
    previews=active.annotate(position=Window(RowNumber(),partition_by=[F('institution_id')],order_by=[F('due_at').asc(),F('id').asc()])).filter(position__lte=5).order_by('institution_id','due_at','id')
    cases=CaseSerializer(previews,many=True).data
    reviewed={r['left__institution_id']:r['count'] for r in OverlapCandidate.objects.filter(left__institution_id__in=ids).exclude(decision='pending').order_by().values('left__institution_id').annotate(count=Count('id'))}
    for row in rows:
        inst=row['institution_id']
        row['bureau_details']=[{'code':b['bureau__code'],'name':b['bureau__name'],'count':b['count']} for b in bureaus if b['institution_id']==inst]
        row['officers']=[{'name':(' '.join([o['assigned_to__first_name'] or '',o['assigned_to__last_name'] or '']).strip() or o['assigned_to__username']) if o['assigned_to_id'] else 'Unassigned','count':o['count']} for o in officers if o['institution_id']==inst]
        row['cases']=[c for c in cases if c['institution']['id']==str(inst)]
        row['reviewed_relationships']=reviewed.get(inst,0)
        row['scope']='All-time active cases; all current bureaus and categories'
    return rows


@api_view(['GET'])
def notices(request):
    if not coordination(request.user):raise PermissionDenied('Cross-bureau activity requires coordination access.')
    paginator=PageNumberPagination()
    rows=paginator.paginate_queryset(groups(request),request)
    return paginator.get_paginated_response(enrich(request,rows))
