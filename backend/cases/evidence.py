"""Recorded comparison evidence, separate from incident findings and ranking."""
from copy import deepcopy

MATCHING_POLICY_REVISION = 'institution-exact-top5-v1'


def recorded(value):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value.isoformat() if hasattr(value, 'isoformat') else value


def compare(left, right):
    left, right = recorded(left), recorded(right)
    return {'left': left, 'right': right,
            'state': 'unknown' if left is None or right is None else 'agrees' if left == right else 'differs'}


def build_evidence(left, right, *, score=None, model_revision=''):
    references = compare(left.source_reference, right.source_reference)
    systems = compare(left.source_system, right.source_system)
    identities = compare(
        [systems['left'], references['left']] if systems['left'] and references['left'] else None,
        [systems['right'], references['right']] if systems['right'] and references['right'] else None)
    semantic = score is not None
    return {
        # Legacy keys remain available to existing readers.
        'institution': left.institution.name,
        'shared_reference': references['state'] == 'agrees',
        'categories': [left.category, right.category],
        'incident_dates': [str(left.incident_date or 'Not recorded'), str(right.incident_date or 'Not recorded')],
        'scope': 'Original allegation summaries; human review required' if semantic else 'Manual coordination decision; not model-scored',
        'schema_version': 1,
        'discovery_method': 'same_institution_minilm_top5' if semantic else 'manual_selection',
        'matching_policy_revision': MATCHING_POLICY_REVISION if semantic else 'manual-pair-v1',
        'cosine_score': score,
        'encoder_revision': model_revision if semantic else None,
        'canonical_institution': {
            'left': {'id': str(left.institution_id), 'permanent_id': left.institution.permanent_id, 'name': left.institution.name},
            'right': {'id': str(right.institution_id), 'permanent_id': right.institution.permanent_id, 'name': right.institution.name},
            'state': 'agrees' if left.institution_id == right.institution_id else 'differs',
            'source': 'Canonical Institution registry; not inferred from names',
        },
        'comparisons': {
            'source_system': systems, 'source_reference': references, 'source_identity': identities,
            'category': compare(left.category, right.category),
            'classification': compare(None if left.classification == 'unclassified' else left.classification,
                                      None if right.classification == 'unclassified' else right.classification),
            'incident_date': compare(left.incident_date, right.incident_date),
        },
        'provenance': {'source': 'Recorded Complaint fields at evidence capture',
                       'left_case_id': str(left.pk), 'right_case_id': str(right.pk),
                       'left_case_version': left.version, 'right_case_version': right.version},
        'incident_finding': {'state': 'unverified', 'source': 'Human relationship review is required'},
        'limitations': [
            'Cosine measures allegation-summary wording, not duplicate probability.',
            'Shared reference text across sources is not source identity or proof of a common incident.',
            'Matching institution or category is not proof of a common incident.',
            'Different recorded dates are review cues, not automatic rejection.',
            'Recorded allegations and metadata have not been independently verified.',
        ],
    }


def decision_snapshot(obj, user):
    return {'evidence': deepcopy(obj.evidence),
            'matching_policy_revision': obj.evidence.get('matching_policy_revision'),
            'score': obj.score, 'model_revision': obj.model_revision, 'origin': obj.origin,
            'relationship_version': obj.version, 'decision': obj.decision, 'reason': obj.reason,
            'reviewer': {'id': user.pk, 'name': user.get_full_name() or user.username},
            'reviewed_at': obj.reviewed_at.isoformat()}
