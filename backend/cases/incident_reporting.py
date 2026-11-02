"""Distinct complaint, relationship and reviewed-group measures share one scope."""
import csv
import io
from django.db.models import Count, Exists, OuterRef, Q
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .access import filtered_cases
from .models import Complaint, IncidentGroup, IncidentMembership, OverlapCandidate, AuditEvent


CASE_METRICS = ('complaints','suggested_cases','grouped_cases','ungrouped_cases','matching_complete',
                'matching_pending','matching_failed','matching_not_processed')
PAIR_METRICS = {'pending_pairs':'pending','same_incident_pairs':'same_incident','related_issue_pairs':'related_issue'}


def confirmed_groups():
    return IncidentGroup.objects.filter(state='active',needs_review=False).filter(
        Q(supporting_relationship__isnull=True) | Q(supporting_relationship__decision='same_incident')).annotate(
        member_count=Count('memberships',filter=Q(memberships__active=True),distinct=True)).filter(member_count__gte=2)


def scope(request):
    from .intelligence import manager, feature
    manager(request.user); feature('ENABLE_INCIDENT_GROUPS')
    cases = filtered_cases(request).order_by().distinct()
    ids = cases.values('pk')
    pairs = OverlapCandidate.objects.filter(left_id__in=ids,right_id__in=ids).select_related('left','right','left__institution').order_by('-created_at','-id')
    memberships = IncidentMembership.objects.filter(active=True,group_id__in=confirmed_groups().values('pk'))
    groups = confirmed_groups().filter(Exists(memberships.filter(group_id=OuterRef('pk'),case_id__in=ids)))
    pending = pairs.filter(decision='pending')
    suggested = cases.filter(Q(pk__in=pending.values('left_id')) | Q(pk__in=pending.values('right_id')))
    grouped = cases.filter(pk__in=memberships.values('case_id'))
    from .matching import revision
    model = revision()
    complete = Q(matching_state='complete',embedding__isnull=False,model_revision=model)
    queries = {'complaints':cases,'pending_pairs':pending,'suggested_cases':suggested,
        'same_incident_pairs':pairs.filter(decision='same_incident'),'related_issue_pairs':pairs.filter(decision='related_issue'),
        'confirmed_groups':groups,'grouped_cases':grouped,'ungrouped_cases':cases.exclude(pk__in=memberships.values('case_id')),
        'matching_complete':cases.filter(complete),'matching_pending':cases.filter(matching_state='pending'),
        'matching_failed':cases.filter(matching_state='failed'),
        'matching_not_processed':cases.exclude(complete | Q(matching_state__in=['pending','failed']))}
    return queries, model


@api_view(['GET'])
def summary(request):
    queries, model = scope(request)
    # One aggregate for each kind; never join pairs and memberships into complaint totals.
    cases = queries['complaints'].aggregate(total=Count('pk',distinct=True),
        complete=Count('pk',filter=Q(pk__in=queries['matching_complete'].values('pk')),distinct=True),
        pending=Count('pk',filter=Q(matching_state='pending'),distinct=True),
        failed=Count('pk',filter=Q(matching_state='failed'),distinct=True))
    counts = {key:qs.count() for key,qs in queries.items() if not key.startswith('matching_') and key!='complaints'}
    counts['complaints'] = cases['total']
    counts.update(matching_complete=cases['complete'],matching_pending=cases['pending'],matching_failed=cases['failed'],
        matching_not_processed=cases['total']-cases['complete']-cases['pending']-cases['failed'])
    return Response({'counts':counts,'model_revision':model,'generated_at':timezone.now(),
        'scope':'selected_authorized_complaints','filters':dict(request.query_params),
        'definitions':{'pairs':'Both endpoints must be in the selected complaint scope; stored pairs are not exhaustive similarity counts.',
            'groups':'Active, reviewed, valid groups touching this scope; distinct member case counts use only cases in scope.',
            'coverage':'Complete requires a stored embedding from the current model. Pending, failed and not-processed are not confirmed zero matches.',
            'group_members':'Groups can overlap; counts of members across different groups must not be added.'}})


def selected(request):
    queries, _ = scope(request)
    metric = request.query_params.get('metric','complaints')
    if metric not in queries: raise ValidationError('Unknown incident metric.')
    return metric, queries[metric], queries['complaints'].values('pk')


@api_view(['GET'])
def records(request):
    from .api import page
    from .serializers import CaseSerializer
    metric, qs, ids = selected(request)
    if metric in CASE_METRICS:
        return page(request,qs.order_by('-received_at','-pk'),CaseSerializer)
    if metric in PAIR_METRICS:
        from rest_framework import serializers
        class PairSerializer(serializers.ModelSerializer):
            left_reference = serializers.CharField(source='left.reference')
            right_reference = serializers.CharField(source='right.reference')
            class Meta:
                model = OverlapCandidate
                fields = ['id','left_id','right_id','left_reference','right_reference','decision','score','origin','reason']
        return page(request,qs,PairSerializer)
    from .intelligence import GroupSerializer, group_query
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    rows = paginator.paginate_queryset(group_query().filter(pk__in=qs.values('pk')),request)
    payload = GroupSerializer(rows,many=True).data
    selected_members = IncidentMembership.objects.filter(group_id__in=[g.pk for g in rows],active=True,case_id__in=ids).values('group_id').annotate(count=Count('case_id',distinct=True))
    counts = {str(row['group_id']):row['count'] for row in selected_members}
    for row in payload:
        row['scope_case_count'] = counts.get(row['id'],0)
        row['all_time_case_count'] = len(row['cases'])
    return paginator.get_paginated_response(payload)


@api_view(['GET'])
def export(request):
    from .exports import safe
    metric, qs, ids = selected(request)
    AuditEvent.objects.create(actor=request.user,kind='incident_export',detail={'metric':metric,'filters':dict(request.query_params),'count':qs.count()})
    def chunks():
        out = io.StringIO(); writer = csv.writer(out)
        def line(values):
            writer.writerow([safe(v) for v in values]); result=out.getvalue(); out.seek(0);out.truncate(0);return result
        if metric in CASE_METRICS:
            yield line(['Row type','Case ID','Reference','Institution','Bureau','Status','Matching state'])
            for c in qs.order_by('-received_at','-pk').iterator(chunk_size=1000):
                yield line(['complaint',c.pk,c.reference,c.institution.name,c.bureau.code,c.status,c.matching_state])
        elif metric in PAIR_METRICS:
            yield line(['Row type','Pair ID','Left case','Right case','Decision','Origin','Cosine similarity','Reason'])
            for pair in qs.iterator(chunk_size=1000):
                yield line(['relationship',pair.pk,pair.left.reference,pair.right.reference,pair.decision,pair.origin,pair.score if pair.score is not None else 'Not model-scored',pair.reason])
        else:
            qs_groups = qs.annotate(scope_case_count=Count('memberships',filter=Q(memberships__active=True,memberships__case_id__in=ids),distinct=True))
            yield line(['Row type','Group ID','Institution ID','Title','Members in selected scope','All-time active members','Version','Reason'])
            for group in qs_groups.iterator(chunk_size=1000):
                yield line(['incident_group',group.pk,group.institution_id,group.title,group.scope_case_count,group.member_count,group.version,group.reason])
    return StreamingHttpResponse(chunks(),content_type='text/csv',headers={'Content-Disposition':f'attachment; filename="incident-{metric}.csv"'})
