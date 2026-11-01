"""Read-only experimental discovery. Production matching never calls this module."""
import re
from django.conf import settings
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from pgvector.django import CosineDistance
from rest_framework.exceptions import PermissionDenied
from .access import coordination, scoped_cases
from .matching import runtime


def discover(user, case, budget=20, reference_ids=None):
    if not getattr(settings, 'SHADOW_RETRIEVAL_ENABLED', False) or not coordination(user):
        raise PermissionDenied('Shadow discovery is disabled or unauthorized.')
    if not 1 <= budget <= 20:
        raise ValueError('Each experimental channel is bounded to 1–20 candidates.')
    _, revision, cutoff = runtime()
    base = scoped_cases(user).filter(institution_id=case.institution_id).exclude(pk=case.pk)
    # A query supplied by an unauthorized caller must not reveal even candidate counts.
    if not scoped_cases(user).filter(pk=case.pk).exists():
        raise PermissionDenied('Case access required.')
    if reference_ids is not None:
        base = base.filter(pk__in=reference_ids)
    vector = list(case.embedding) if case.embedding is not None and case.model_revision == revision else None
    semantic = base.filter(embedding__isnull=False, model_revision=revision).annotate(distance=CosineDistance('embedding', vector)).order_by('distance') if vector else base.none()
    terms = list(dict.fromkeys(re.findall(r'[a-zA-Z0-9]{3,}', case.summary)))[:12]
    query = SearchQuery(' OR '.join(terms), search_type='websearch', config='english')
    search = SearchVector('summary', config='english')
    lexical = base.annotate(search=search, lexical_rank=SearchRank(search, query)).filter(search=query).order_by('-lexical_rank', 'reference', 'pk') if terms else base.none()
    reference = base.filter(source_reference=case.source_reference).order_by('pk') if case.source_reference and case.source_reference.strip() else base.none()
    channels = {'semantic': semantic, 'lexical': lexical, 'reference': reference}
    retrieved, candidates, volumes = {}, {}, {}
    for method, qs in channels.items():
        rows = list(qs[:budget]); retrieved[method] = []
        count = qs.count(); volumes[method] = {'eligible': count, 'retrieved': len(rows), 'truncated': count > budget}
        for rank, row in enumerate(rows, 1):
            key = str(row.pk); retrieved[method].append(key)
            result = candidates.setdefault(key, {'case_id': key, 'methods': [], 'cosine': None, 'lexical_rank': None, 'experimental_priority': 0.0})
            result['methods'].append(method); result['experimental_priority'] += 1/(60+rank)
            if method == 'lexical': result['lexical_rank'] = float(row.lexical_rank)
    if vector and candidates:
        scores = base.filter(pk__in=candidates, embedding__isnull=False, model_revision=revision).annotate(distance=CosineDistance('embedding', vector))
        for row in scores: candidates[str(row.pk)]['cosine'] = 1-float(row.distance)
    for result in candidates.values():
        result['passes_semantic_cutoff'] = result['cosine'] is not None and result['cosine'] >= cutoff
        result['score_state'] = 'model_scored' if result['cosine'] is not None else 'embedding_unavailable'
    baseline = [key for key in retrieved['semantic'][:5] if candidates[key]['passes_semantic_cutoff']]
    union = sorted(candidates, key=lambda key: (-candidates[key]['experimental_priority'], key))[:5]
    return {'policy': 'shadow-rrf-v1; RRF priority is not confidence', 'production_policy_changed': False,
        'model_revision': revision, 'threshold': cutoff, 'budget_per_channel': budget,
        'baseline': baseline, 'lexical': retrieved['lexical'][:5], 'reference': retrieved['reference'][:5], 'union': union,
        'candidates': list(candidates.values()), 'volumes': volumes,
        'candidate_ids_by_channel': retrieved, 'bounded_union': list(candidates),
        'lexical_query_terms': terms, 'plans': {'lexical': lexical[:budget].explain(format='json', analyze=True, buffers=True) if terms else None,
                                              'semantic': semantic[:budget].explain(format='json', analyze=True, buffers=True) if vector else None}}
