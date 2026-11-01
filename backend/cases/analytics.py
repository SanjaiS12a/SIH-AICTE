"""Receipt cohorts, all-time coordination and action periods remain distinct."""
import csv
import io
import json
from types import SimpleNamespace
from django.db.models import Count, Q, Min
from django.db.models.functions import TruncQuarter
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from .access import filtered_cases, coordination
from .models import CaseAction, AuditEvent
from .serializers import ActionReadSerializer, FilterSerializer

EVENTS = {'registered': Q(kind__in=['registered','imported']), 'transfer': Q(kind='transfer'),
    'escalation_created': Q(kind='escalation_created'), 'escalation_resolved': Q(kind='escalation_resolved'),
    'classification': Q(kind='classification'), 'overlap_review': Q(kind='overlap_review'),
    'coordination': Q(kind__startswith='coordination_'),
    'closed': Q(kind='status', changes__status__after='disposed'),
    'reopened': Q(kind='status', changes__status__before='disposed') & ~Q(changes__status__after='disposed')}


def action_query(request):
    form=FilterSerializer(data=request.query_params);form.is_valid(raise_exception=True)
    params=request.query_params.copy()
    for key in ['from','to','page','event']:params.pop(key,None)
    qs=CaseAction.objects.filter(case__in=filtered_cases(SimpleNamespace(user=request.user,query_params=params))).select_related('actor','case__institution').order_by('-created_at','-id')
    for key,lookup in [('from','created_at__date__gte'),('to','created_at__date__lte')]:
        if form.validated_data.get(key):qs=qs.filter(**{lookup:form.validated_data[key]})
    event=request.query_params.get('event')
    if event:
        if event not in EVENTS:raise ValidationError('Unknown movement event.')
        qs=qs.filter(EVENTS[event])
    return qs


class MovementSerializer(ActionReadSerializer):
    case_id=serializers.UUIDField()
    reference=serializers.CharField(source='case.reference')
    institution=serializers.CharField(source='case.institution.name')
    event=serializers.SerializerMethodField()
    def get_event(self,obj):
        if obj.kind=='status':
            change=obj.changes.get('status',{})
            if change.get('after')=='disposed':return 'closed'
            if change.get('before')=='disposed':return 'reopened'
        return 'registered' if obj.kind=='imported' else obj.kind
    class Meta(ActionReadSerializer.Meta):
        fields=[*ActionReadSerializer.Meta.fields,'case_id','reference','institution','event']


@api_view(['GET'])
def movements(request):
    from .api import page
    return page(request,action_query(request),MovementSerializer,context={'restricted':not coordination(request.user)})


@api_view(['GET'])
def movements_csv(request):
    from .exports import safe
    qs=action_query(request)
    AuditEvent.objects.create(actor=request.user,kind='movement_export',detail={'filters':dict(request.query_params),'count':qs.count()})
    def chunks():
        out=io.StringIO();writer=csv.writer(out);writer.writerow(['Case','Institution','Event','Action time','Actor','Reason','Changes'])
        yield out.getvalue();out.seek(0);out.truncate(0)
        for action in qs.iterator(chunk_size=1000):
            row=MovementSerializer(action,context={'restricted':not coordination(request.user)}).data
            writer.writerow([safe(row[k]) for k in ['reference','institution','event','created_at','actor','reason']]+[safe(json.dumps(row['changes']))])
            yield out.getvalue();out.seek(0);out.truncate(0)
    return StreamingHttpResponse(chunks(),content_type='text/csv',headers={'Content-Disposition':'attachment; filename="case-movements.csv"'})


def analytics(request,qs,pending,now):
    from .coordination import groups
    regions=list(qs.order_by().values('institution__region','institution__district').annotate(count=Count('id'),institutions=Count('institution',distinct=True)).order_by('institution__region','institution__district'))
    classifications=list(qs.order_by().values('classification').annotate(count=Count('id')).order_by('classification'))
    # Top-10 institutions by pending workload in the selected cohort.
    # Overdue and approaching use real due_at timestamps, not estimated.
    from datetime import timedelta
    institutions=list(pending.order_by().values('institution_id','institution__name','institution__permanent_id','institution__region','institution__district').annotate(
        count=Count('id'),
        bureaus=Count('bureau',distinct=True),
        overdue=Count('id',filter=Q(due_at__lt=now)),
        approaching=Count('id',filter=Q(due_at__gte=now,due_at__lte=now+timedelta(days=7))),
        unresolved_escalations=Count('id',filter=Q(has_unresolved_escalation=True)),
    ).order_by('-count','institution_id')[:10])
    priority=list(pending.order_by().values('institution_id','institution__name','institution__permanent_id').annotate(
        count=Count('id'), overdue=Count('id',filter=Q(due_at__lt=now)),
        unresolved_escalations=Count('id',filter=Q(has_unresolved_escalation=True)), earliest_deadline=Min('due_at'),
    ).order_by('-overdue','-unresolved_escalations','earliest_deadline','institution_id')[:5])
    from .coordination_workflow import filtered_records
    awaiting=filtered_records(request).filter(state='in_coordination', participants__acknowledged_at__isnull=True).distinct().count()
    ids=[i['institution_id'] for i in institutions]
    bureau_rows=list(pending.filter(institution_id__in=ids).order_by().values('institution_id','bureau__code','bureau__name').annotate(count=Count('id')))
    notices=set(groups(request).filter(institution_id__in=ids).values_list('institution_id',flat=True))
    for row in institutions:
        row['bureau_names']=[b['bureau__code'] for b in bureau_rows if b['institution_id']==row['institution_id']]
        row['bureau_details']=[{'code':b['bureau__code'],'name':b['bureau__name'],'count':b['count']} for b in bureau_rows if b['institution_id']==row['institution_id']]
        row['coordination']=row['institution_id'] in notices
    quarters={}
    for field,key in [('received_at','received'),('disposed_at','disposed')]:
        for row in qs.filter(**{field+'__isnull':False}).annotate(period=TruncQuarter(field)).values('period').annotate(count=Count('id')).order_by('period'):
            start=row['period'].strftime('%Y-%m-%d')
            quarters.setdefault(start,{'start':start,'label':f"{row['period'].year} Q{(row['period'].month-1)//3+1}",'received':0,'disposed':0})[key]=row['count']
    actions=action_query(request)
    counts=[{'event':event,'count':actions.filter(condition).count()} for event,condition in EVENTS.items()]
    return {'regions':regions,'classifications':classifications,'institutions':institutions,'priority_institutions':priority,
            'pending_acknowledgment_records':awaiting,'quarters':[quarters[k] for k in sorted(quarters)],
            'movement_counts':counts,'recent_movements':MovementSerializer(actions[:10],many=True).data,
            'movement_scope':'Action timestamps; current authorized case attributes, independent of receipt cohort',
            'coordination_scope':'All-time active cases; institution/region/district only; no receipt-date, bureau or category restriction'}
