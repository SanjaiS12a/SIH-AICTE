"""Read-only evaluation of the frozen production policy on an explicit corpus."""
import hashlib
import json
import platform
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from cases.evidence import MATCHING_POLICY_REVISION
from cases.matching import encoder, runtime


def metrics(scores, labels, threshold):
    predicted = scores >= threshold
    positive = labels.astype(bool)
    tp = int(np.sum(predicted & positive)); fp = int(np.sum(predicted & ~positive)); fn = int(np.sum(~predicted & positive))
    return {'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / (tp + fn) if tp + fn else None,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': int(np.sum(~predicted & ~positive)), 'samples': len(scores)}


def calibrate(scores, labels):
    # Existing offline callers retain this helper; the command never selects a threshold.
    candidates = [(float(t), metrics(scores, labels, float(t))) for t in np.unique(scores)]
    valid = [x for x in candidates if x[1]['precision'] is not None and x[1]['precision'] >= .85]
    return max(valid, key=lambda x: (x[1]['f1'], x[1]['recall'], x[0])) if valid else None


def eligible_corpus(corpus):
    if not isinstance(corpus, dict) or not all(isinstance(corpus.get(k), list) for k in ['records', 'pairs', 'retrieval']):
        raise CommandError('Expected records, pairs and retrieval arrays.')
    records, rejected, seen = {}, [], set()
    for number, row in enumerate(corpus['records'], 1):
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
            rejected.append({'row': number, 'reason': 'Missing record ID'}); continue
        if row['id'] in seen:
            raise CommandError('Duplicate record IDs make evaluation ambiguous.')
        seen.add(row['id'])
        if (row.get('split') not in ['calibration', 'test'] or row.get('family') is None
                or not isinstance(row.get('institution'), str) or not row['institution'].strip()
                or not isinstance(row.get('text'), str) or not row['text'].strip()):
            rejected.append({'id': row['id'], 'reason': 'Missing text, institution, family or valid split'}); continue
        records[row['id']] = row
    families = {split: {str(r['family']) for r in records.values() if r['split'] == split} for split in ['calibration', 'test']}
    if families['calibration'] & families['test']:
        raise CommandError('Incident families overlap calibration and test partitions.')
    texts = defaultdict(set)
    for row in records.values():
        texts[' '.join(row['text'].casefold().split())].add(row['split'])
    repeats = {text for text, splits in texts.items() if len(splits) > 1}
    excluded = [r['id'] for r in records.values() if r['split'] == 'test' and ' '.join(r['text'].casefold().split()) in repeats]
    for key in excluded:
        del records[key]
    if not records:
        raise CommandError('No eligible records.')
    pairs, invalid_pairs, labels = [], [], {}
    for number, pair in enumerate(corpus['pairs'], 1):
        if not isinstance(pair, dict) or pair.get('label') not in ['same_incident', 'related_issue', 'unrelated']:
            invalid_pairs.append({'row': number, 'reason': 'Missing or invalid label'}); continue
        left = records.get(pair['left']) if isinstance(pair.get('left'), str) else None
        right = records.get(pair['right']) if isinstance(pair.get('right'), str) else None
        if not left or not right or left['id'] == right['id'] or left['split'] != right['split'] or pair.get('split') != left['split']:
            invalid_pairs.append({'row': number, 'reason': 'Unavailable, self or cross-partition endpoints'}); continue
        key = tuple(sorted([left['id'], right['id']]))
        if key in labels:
            if labels[key] != pair['label']:
                raise CommandError('Conflicting labels for one complaint pair.')
            invalid_pairs.append({'row': number, 'reason': 'Repeated labelled pair'}); continue
        labels[key] = pair['label']; pairs.append(pair)
    return records, pairs, labels, {
        'raw_records': len(corpus['records']), 'eligible_records': len(records),
        'raw_partition_counts': dict(Counter(r.get('split', 'missing') for r in corpus['records'] if isinstance(r, dict))),
        'eligible_partition_counts': dict(Counter(r['split'] for r in records.values())),
        'invalid_records': rejected, 'cross_partition_exact_text_groups': len(repeats),
        'excluded_repeated_test_ids': excluded, 'raw_pairs': len(corpus['pairs']), 'eligible_pairs': len(pairs),
        'invalid_or_excluded_pairs': invalid_pairs,
        'label_counts': dict(Counter(p['label'] for p in pairs)),
        'test_label_counts': dict(Counter(p['label'] for p in pairs if p['split'] == 'test')),
    }


def evaluate(corpus, model, cutoff):
    records, pairs, labels, eligibility = eligible_corpus(corpus)
    ids = sorted(records)
    started = time.perf_counter()
    dense = np.asarray(model.encode([records[key]['text'] for key in ids], normalize_embeddings=True, batch_size=32), dtype=np.float32)
    embedding_seconds = time.perf_counter() - started
    if dense.shape != (len(ids), 384):
        raise CommandError('Encoder did not return one 384-dimensional vector per eligible record.')
    vectors = {key: dense[i] for i, key in enumerate(ids) if np.isfinite(dense[i]).all() and np.linalg.norm(dense[i]) > 0}
    unavailable = sorted(set(ids) - vectors.keys())
    vectors = {key: value / np.linalg.norm(value) for key, value in vectors.items()}
    def score(a, b):
        return float(np.clip(vectors[a] @ vectors[b], -1, 1))
    pair_metrics = {}
    for split in ['calibration', 'test']:
        selected = [p for p in pairs if p['split'] == split and p['left'] in vectors and p['right'] in vectors]
        scores = np.array([score(p['left'], p['right']) if records[p['left']]['institution'] == records[p['right']]['institution'] else -2 for p in selected])
        truth = np.array([p['label'] != 'unrelated' for p in selected], dtype=bool)
        result = metrics(scores, truth, cutoff)
        result['false_positives'] = [{'left': p['left'], 'right': p['right'], 'score': float(s)} for p, s in zip(selected, scores) if p['label'] == 'unrelated' and s >= cutoff]
        result['missed_review_worthy_pairs'] = [{'left': p['left'], 'right': p['right'], 'label': p['label'], 'score': float(s)} for p, s in zip(selected, scores) if p['label'] != 'unrelated' and s < cutoff]
        result['unavailable_pairs'] = sum(p['split'] == split and (p['left'] not in vectors or p['right'] not in vectors) for p in pairs)
        pair_metrics[split] = result
    query_ids = {q['query'] for q in corpus['retrieval'] if isinstance(q, dict) and isinstance(q.get('query'), str)}
    queries, invalid_queries, seen = [], [], set()
    suggested = judged = worthy = relevant_count = retrieved_relevant = candidate_relevant = 0
    with_suggestions = abstentions = with_candidates = 0
    timings = []
    for number, query in enumerate(corpus['retrieval'], 1):
        if not isinstance(query, dict) or query.get('split') != 'test':
            continue
        row = records.get(query['query']) if isinstance(query.get('query'), str) else None
        if (not row or row['split'] != 'test' or row['id'] in seen or not isinstance(query.get('relevant'), list)
                or not query['relevant'] or not all(isinstance(key, str) for key in query['relevant'])):
            invalid_queries.append({'row': number, 'reason': 'Missing, repeated or invalid test query/relevance'}); continue
        seen.add(row['id'])
        references = [r for r in records.values() if r['split'] == 'test' and r['institution'] == row['institution'] and r['id'] not in query_ids]
        relevant = set(query['relevant'])
        if not relevant <= {r['id'] for r in references} or any(labels.get(tuple(sorted([row['id'], r]))) != 'same_incident' for r in relevant):
            invalid_queries.append({'row': number, 'reason': 'Relevant references unavailable or not explicitly labelled same incident'}); continue
        with_candidates += bool(references); relevant_count += len(relevant)
        started = time.perf_counter()
        top = sorted(((r['id'], score(row['id'], r['id'])) for r in references if row['id'] in vectors and r['id'] in vectors), key=lambda item: (-item[1], item[0]))[:5]
        accepted = [(key, value) for key, value in top if value >= cutoff]
        timings.append((time.perf_counter() - started) * 1000)
        abstentions += row['id'] not in vectors; with_suggestions += bool(accepted); suggested += len(accepted)
        for key, value in accepted:
            label = labels.get(tuple(sorted([row['id'], key])))
            judged += label is not None; worthy += label in ['same_incident', 'related_issue']
        hits = relevant & {key for key, _ in accepted}
        retrieved_relevant += len(hits); candidate_relevant += len(relevant & {key for key, _ in top})
        queries.append({'query': row['id'], 'eligible_candidates': len(references), 'relevant': sorted(relevant),
            'top5_before_threshold': [{'id': key, 'score': value} for key, value in top],
            'suggestions': [{'id': key, 'score': value, 'label': labels.get(tuple(sorted([row['id'], key])))} for key, value in accepted],
            'missed_same_incident': sorted(relevant - hits)})
    count = len(queries)
    return {'eligibility': eligibility, 'pairwise_threshold_rule': pair_metrics, 'embedding_seconds': embedding_seconds, 'retrieval': {
        'eligible_queries': count, 'invalid_or_excluded_queries': invalid_queries,
        'query_candidate_coverage': with_candidates / count if count else None,
        'queries_with_suggestions': with_suggestions, 'query_suggestion_coverage': with_suggestions / count if count else None,
        'suggestions': suggested, 'judged_suggestions': judged, 'unjudged_suggestions': suggested - judged,
        'judgment_coverage': judged / suggested if suggested else None,
        'review_worthy_judged_suggestions': worthy, 'review_worthy_precision_on_judged_suggestions': worthy / judged if judged else None,
        'overall_suggestion_precision': worthy / suggested if suggested and judged == suggested else None,
        'eligible_relevant_pairs': relevant_count, 'retrieved_relevant_pairs': retrieved_relevant,
        'same_incident_recall_at_5': retrieved_relevant / relevant_count if relevant_count else None,
        'query_hit_rate_at_5': sum(not q['missed_same_incident'] for q in queries) / count if count else None,
        'same_incident_candidate_recall_before_threshold': candidate_relevant / relevant_count if relevant_count else None,
        'embedding_abstentions': abstentions, 'unavailable_embedding_ids': unavailable,
        'in_memory_exact_retrieval_ms': {'total': sum(timings), 'p95': float(np.percentile(timings, 95)) if timings else None},
        'pgvector_database_latency_ms': None, 'queries': queries,
    }}


class Command(BaseCommand):
    help = 'Evaluate frozen MiniLM retrieval; never writes calibration or promotes a model.'

    def add_arguments(self, parser):
        parser.add_argument('--data', default=str(settings.BASE_DIR.parent / 'data' / 'evaluation.json'))
        destination = parser.add_mutually_exclusive_group()
        destination.add_argument('--run-dir', help='Report directory inside RESULTS_DIR/runs (ignored).')
        destination.add_argument('--output', help='New report file inside RESULTS_DIR/runs; existing files are protected.')

    def handle(self, *args, **options):
        root = (settings.RESULTS_DIR / 'runs').resolve()
        default = root / ('matching-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
        dest = Path(options['output']).resolve() if options.get('output') else (Path(options['run_dir']).resolve() if options.get('run_dir') else default) / 'matching.json'
        if not dest.is_relative_to(root) or dest.exists():
            raise CommandError('Reports must be new files inside RESULTS_DIR/runs; production and existing outputs are protected.')
        try:
            raw = Path(options['data']).read_bytes(); corpus = json.loads(raw)
        except (OSError, ValueError) as exc:
            raise CommandError('Unable to read evaluation JSON.') from exc
        eligible_corpus(corpus)
        pinned_runtime = runtime()
        _, model_revision, cutoff = pinned_runtime
        started = time.perf_counter(); model = encoder(); cold = time.perf_counter() - started
        if runtime() != pinned_runtime:
            raise CommandError('Active model changed during evaluation; no report was written.')
        output = evaluate(corpus, model, cutoff)
        if runtime() != pinned_runtime:
            raise CommandError('Active model changed during evaluation; no report was written.')
        output.update({
            'model_revision': model_revision, 'matching_policy_revision': MATCHING_POLICY_REVISION,
            'threshold': cutoff, 'policy': 'same institution, exact cosine, nearest five, then frozen threshold; closed cases included',
            'dataset_sha256': hashlib.sha256(raw).hexdigest(), 'label_provenance': corpus.get('label_provenance', 'Not provided'),
            'cold_model_load_seconds': cold, 'hardware': {'platform': platform.platform(), 'processor': platform.processor(), 'inference_device': 'cpu'},
            'metric_definitions': {
                'pairwise_threshold_rule': 'Review-worthy (same_incident OR related_issue) versus unrelated on labelled eligible pairs; not three-class classification or retrieval precision.',
                'same_incident_recall_at_5': 'Returned explicitly relevant same-incident pairs after nearest-five and threshold / all eligible relevant pairs; unavailable vectors count as misses.',
                'candidate_recall': 'Relevant pairs in nearest five before threshold / eligible relevant pairs.',
                'precision': 'Review-worthy / judged returned suggestions. Overall precision unavailable if any suggestion is unjudged; missing labels never become negatives.',
                'coverage': 'Queries with reference candidates or returned suggestions / eligible queries. Judgment coverage = judged / all returned suggestions.',
            },
            'eligibility_rules': ['Family-disjoint calibration/test; duplicate IDs and conflicting labels rejected.',
                'Repeated normalized exact text across partitions excluded from test; near-duplicate leakage not independently audited.',
                'All declared query IDs excluded from reference pools; no reliance on ID suffixes.',
                'References share query institution and test partition; explicit same-incident labels define relevance.',
                'No threshold selection or model activation; calibration metrics also use the frozen production threshold.'],
            'limitations': ['Synthetic regression only; not independently reviewed AICTE accuracy.',
                'Sparse judgments cannot establish overall suggestion precision.',
                'In-memory exact cosine timing is not PostgreSQL latency or end-to-end queue performance.',
                'Evaluation breaks equal-score ties by ID; live SQL does not guarantee a tie order.'],
        })
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('x', encoding='utf-8') as target:
            json.dump(output, target, indent=2, allow_nan=False)
        self.stdout.write(f'Non-mutating evaluation report: {dest}')
        self.stdout.write(json.dumps({key: output[key] for key in ['model_revision', 'matching_policy_revision', 'threshold', 'cold_model_load_seconds', 'embedding_seconds']}))
