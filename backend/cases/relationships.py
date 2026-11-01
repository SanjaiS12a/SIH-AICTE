"""Manual decisions reuse the canonical pair and append-only case histories."""
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from .access import role, scoped_cases
from .api import Conflict, overlap_data, review_snapshots
from .models import Institution, OverlapCandidate, CaseAction
from .evidence import build_evidence, decision_snapshot


@api_view(['GET'])
def export(request):
    import csv, io
    from django.http import StreamingHttpResponse
    from .api import overlap_queryset
    from .exports import safe
    from .models import AuditEvent
    qs=overlap_queryset(request)
    AuditEvent.objects.create(actor=request.user,kind='relationship_export',detail={'filters':dict(request.query_params),'count':qs.count()})
    def chunks():
        out=io.StringIO();writer=csv.writer(out);writer.writerow(['Left case','Right case','Institution','Origin','Cosine similarity','Decision','Reason','Model revision'])
        yield out.getvalue();out.seek(0);out.truncate(0)
        for row in qs.iterator(chunk_size=1000):
            writer.writerow([safe(v) for v in [row.left.reference,row.right.reference,row.left.institution.name,row.origin,row.score if row.score is not None else 'Not model-scored',row.decision,row.reason,row.model_revision]])
            yield out.getvalue();out.seek(0);out.truncate(0)
    return StreamingHttpResponse(chunks(),content_type='text/csv',headers={'Content-Disposition':'attachment; filename="case-relationships.csv"'})


class ManualRelationshipSerializer(serializers.Serializer):
    left = serializers.UUIDField()
    right = serializers.UUIDField()
    decision = serializers.ChoiceField(choices=['same_incident', 'related_issue', 'unrelated'])
    reason = serializers.CharField(max_length=4000)
    expected_version = serializers.IntegerField(min_value=1, required=False)


def decide(obj, user, decision, reason, expected_version):
    same = obj.decision == decision and obj.reason == reason and obj.reviewer_id == user.pk
    if same and obj.version in (expected_version, expected_version + 1):
        return
    if obj.version != expected_version:
        raise Conflict()
    previous = obj.decision
    obj.decision, obj.reason, obj.reviewer, obj.reviewed_at = decision, reason, user, timezone.now()
    obj.version += 1
    obj.save()
    snapshot = decision_snapshot(obj, user)
    for case_id in [obj.left_id, obj.right_id]:
        CaseAction.objects.create(case_id=case_id, actor=user, kind='overlap_review', reason=reason,
            changes={'overlap_id': obj.pk, 'origin': obj.origin, 'decision': {'before': previous, 'after': decision},
                     'review_snapshot': snapshot})
    from .intelligence import flag_supporting_groups
    flag_supporting_groups(obj, user, reason)


@api_view(['POST'])
def manual(request):
    if role(request.user) != 'coordinator':
        raise PermissionDenied('Only coordinators can record relationships.')
    form = ManualRelationshipSerializer(data=request.data)
    form.is_valid(raise_exception=True)
    d = form.validated_data
    if d['left'] == d['right']:
        raise ValidationError('Select two different cases.')
    left, right = [get_object_or_404(scoped_cases(request.user), pk=pk) for pk in sorted([d['left'], d['right']])]
    if left.institution_id != right.institution_id:
        raise ValidationError('Both cases must belong to the same canonical institution.')
    with transaction.atomic():
        Institution.objects.select_for_update().get(pk=left.institution_id)
        obj = OverlapCandidate.objects.select_for_update().filter(left=left, right=right).first()
        created = obj is None
        if created:
            obj = OverlapCandidate.objects.create(left=left, right=right, origin='manual', score=None,
                decision=d['decision'], reason=d['reason'], reviewer=request.user, reviewed_at=timezone.now(),
                evidence=build_evidence(left, right))
            snapshot = decision_snapshot(obj, request.user)
            for case in [left, right]:
                CaseAction.objects.create(case=case, actor=request.user, kind='overlap_review', reason=d['reason'],
                    changes={'overlap_id': obj.pk, 'origin': 'manual', 'decision': {'before': None, 'after': d['decision']},
                             'review_snapshot': snapshot})
        elif not (obj.decision == d['decision'] and obj.reason == d['reason'] and obj.reviewer_id == request.user.pk):
            if 'expected_version' not in d:
                raise Conflict('This pair already exists. Review it with its current version before changing the decision.')
            decide(obj, request.user, d['decision'], d['reason'], d['expected_version'])
    return Response(overlap_data(obj, review_snapshots([obj]).get(obj.pk)), status=201 if created else 200)
