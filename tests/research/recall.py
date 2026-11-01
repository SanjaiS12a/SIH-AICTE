"""Independent known-positive evaluation, without application database access."""
from .public_evaluation import final_labels


def known_positive_metrics(records, judgments, suggestions, candidates):
    by_id = {r['id']: r for r in records}
    if len(by_id) != len(records): raise ValueError('Duplicate corpus IDs.')
    pairs = {}
    for row in judgments:
        a, b = row.get('query_id'), row.get('reference_id')
        if a == b or a not in by_id or b not in by_id or not row.get('incident_family'):
            raise ValueError('Known-positive endpoints and independently established family required.')
        entity_a, entity_b = by_id[a].get('entity'), by_id[b].get('entity')
        if not entity_a or entity_a != entity_b:
            raise ValueError('Known positives need a shared genuine source entity.')
        if row.get('established_before_retrieval') is not True or not row.get('permission_reference'):
            raise ValueError('Independent pre-retrieval ground truth and permission evidence required.')
        if row['pair_id'] in pairs: raise ValueError('Repeated known-positive pair.')
        pairs[row['pair_id']] = (a,b)
    labels = final_labels(judgments,pairs)
    positives = [pairs[key] for key,label in labels.items() if label == 'same_incident']
    return {'known_same_incident_pairs':len(positives),'adjudicated_pairs':len(labels),
        'recall_at5':sum(b in suggestions.get(a,[])[:5] for a,b in positives)/len(positives) if positives else None,
        'candidate_recall':sum(b in candidates.get(a,[]) for a,b in positives)/len(positives) if positives else None,
        'limit':'Metrics apply only to this independently supplied reference set; absent judgments stay unknown.'}
