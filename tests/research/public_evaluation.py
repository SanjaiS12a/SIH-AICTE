"""Offline transfer/workflow probes with blind annotation; no Django or database access."""
import argparse
import csv
import json
import os
import random
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from .public_corpus import LABELS, digest, validate_manifest, write_new

REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
THRESHOLD = 0.603080153465271
WEIGHTS = '53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db'


def validate_records(records, manifest):
    validate_manifest(manifest)
    if not isinstance(records,list): raise ValueError('Corpus must be a record array.')
    permitted = {s['dataset'] for s in manifest['sources'] if s['status'] == 'collected' and s['evaluation_permitted'] is True}
    seen, source_ids = set(), set()
    for row in records:
        if not isinstance(row,dict): raise ValueError('Each record must have structured provenance.')
        if row.get('dataset') not in permitted or not row.get('source_id') or not row.get('source_url') or not row.get('text_type'):
            raise ValueError('Record lacks permitted source provenance.')
        if not isinstance(row.get('id'), str) or row['id'] in seen:
            raise ValueError('Missing or duplicate local record ID.')
        seen.add(row['id'])
        source_key = (row['dataset'], str(row['source_id']))
        if source_key in source_ids: raise ValueError('Repeated source record is not an independent complaint.')
        source_ids.add(source_key)
        if row.get('institution_id') is not None or row.get('incident_group') is not None:
            raise ValueError('Public transfer adapter cannot invent canonical institutions or incident labels; authorized institution evaluation is a separate track.')
        if not isinstance(row.get('model_text'), str):
            raise ValueError('Missing model representation.')


def split_records(records, query_limit=100):
    # Exact duplicate representations stay on one side. This does not establish incident groups.
    groups = defaultdict(list)
    for row in records:
        normalized = ' '.join(row['model_text'].casefold().split())
        groups[digest(normalized.encode())].append(row)
    queries, references = [], []
    for index, (_, group) in enumerate(sorted(groups.items())):
        if index % 5 == 0 and len(queries) < query_limit:
            queries.append(sorted(group, key=lambda row: row['id'])[0])
        else:
            references.extend(group)
    return queries, references, len(groups)


def final_labels(rows, allowed_pairs):
    result, seen = {}, set()
    for row in rows:
        key = row.get('pair_id')
        if key not in allowed_pairs or key in seen:
            raise ValueError('Unknown or repeated annotation pair.')
        seen.add(key)
        if not row.get('final_label'):
            continue
        if any(row.get(k) not in LABELS for k in ['label_1', 'label_2', 'final_label']):
            raise ValueError('Invalid annotation label; uncertainty must remain insufficient_evidence.')
        a, b, adjudicator = row.get('reviewer_1'), row.get('reviewer_2'), row.get('adjudicator')
        if not a or not b or a == b or not row.get('reason', '').strip() or not row.get('evidence_references', '').strip():
            raise ValueError('Two independent reviewer IDs, rationale and evidence references are required.')
        if row['label_1'] == row['label_2']:
            if row.get('status') != 'agreed' or row['final_label'] != row['label_1']:
                raise ValueError('Agreed labels cannot silently change at adjudication.')
        elif row.get('status') != 'adjudicated' or not adjudicator or adjudicator in [a, b]:
            raise ValueError('Disagreement requires an independent third reviewer.')
        result[key] = row['final_label']
    return result


def cluster_precision_interval(suggestions, labels):
    groups = defaultdict(list)
    for suggestion in suggestions:
        groups[suggestion['query_id']].append(labels[suggestion['pair_id']] in ['same_incident', 'related_issue'])
    if len(groups) < 2:
        return None
    clusters = list(groups.values()); randomizer = random.Random(26264)
    values = []
    for _ in range(1000):
        sample = [value for group in randomizer.choices(clusters, k=len(clusters)) for value in group]
        values.append(sum(sample) / len(sample))
    values.sort()
    return {'lower': values[24], 'upper': values[974], 'method': '95% query-cluster percentile bootstrap, 1000 resamples; convenience-sample uncertainty only'}


def summarize(suggestions, labels, query_count):
    usable = {key: value for key, value in labels.items() if value != 'insufficient_evidence'}
    n = len(suggestions); known = sum(s['pair_id'] in usable for s in suggestions)
    worthy = sum(usable.get(s['pair_id']) in ['same_incident', 'related_issue'] for s in suggestions)
    complete = n > 0 and known == n
    return {'returned_suggestions': n, 'adjudicated_labels': sum(s['pair_id'] in labels for s in suggestions),
            'usable_judgments': known, 'insufficient_evidence': sum(labels.get(s['pair_id']) == 'insufficient_evidence' for s in suggestions),
            'usable_label_coverage': known / n if n else None,
            'review_worthy_precision_at_5': worthy / n if complete else None,
            'precision_unavailable_reason': None if complete else 'Requires a nonempty suggestion set with 100% usable independent adjudication.',
            'precision_interval': cluster_precision_interval(suggestions, usable) if complete else None,
            'same_incident_recall_at_5': None, 'recall_unavailable_reason': 'No independently established eligible same-incident reference corpus; returned-pair annotation alone cannot measure recall.',
            'false_positive_rate': None, 'fpr_unavailable_reason': 'No independently sampled and completely labelled negative candidate population.',
            'known_unrelated_suggestions': sum(labels.get(s['pair_id']) == 'unrelated' for s in suggestions),
            'queries_with_suggestions': len({s['query_id'] for s in suggestions}),
            'no_suggestion_rate': 1-len({s['query_id'] for s in suggestions}) / query_count if query_count else None,
            'unjudged': n-sum(s['pair_id'] in labels for s in suggestions)}


def blind_files(directory, dataset, suggestions, records):
    pairs = {s['pair_id']: s for s in suggestions}
    rows = []
    for pair_id, pair in pairs.items():
        a, b = records[pair['query_id']], records[pair['reference_id']]
        rows.append({'pair_id': pair_id, 'text_a': a['model_text'], 'text_b': b['model_text'],
            'source_id_a': a['source_id'], 'source_id_b': b['source_id'],
            'source_a': a['source_url'], 'source_b': b['source_url'], 'category_a': a['category'], 'category_b': b['category'],
            'reviewer_id': '', 'label': '', 'reason': '', 'evidence_references': '', 'status': 'pending'})
    for number in [1, 2]:
        shuffled = rows.copy(); random.Random(26264+number).shuffle(shuffled)
        filename = directory / f'{dataset}-reviewer-{number}.csv'
        with filename.open('x', encoding='utf-8', newline='') as target:
            fields = list(rows[0]) if rows else ['pair_id', 'reviewer_id', 'label', 'reason', 'evidence_references', 'status']
            writer = csv.DictWriter(target, fieldnames=fields); writer.writeheader()
            writer.writerows({key: "'"+value if isinstance(value,str) and value.lstrip().startswith(('=', '+', '-', '@')) else value for key,value in row.items()} for row in shuffled)
    with (directory / f'{dataset}-adjudication.csv').open('x', encoding='utf-8', newline='') as target:
        fields = ['pair_id', 'reviewer_1', 'label_1', 'reviewer_2', 'label_2', 'adjudicator', 'final_label', 'reason', 'evidence_references', 'status']
        writer = csv.DictWriter(target, fieldnames=fields); writer.writeheader()
        writer.writerows({'pair_id': key, 'status': 'pending'} for key in sorted(pairs))


def workflow_counts(records):
    rows = [row['original_fields'] for row in records if row.get('original_fields')]
    intervals, invalid, backwards = [], 0, 0
    for row in rows:
        try:
            start = datetime.fromisoformat(row['created_date'])
            if row.get('closed_date'):
                elapsed = (datetime.fromisoformat(row['closed_date'])-start).total_seconds()
                backwards += elapsed < 0
                if elapsed >= 0: intervals.append(elapsed / 86400)
        except (ValueError, TypeError, KeyError): invalid += 1
    return {'records': len(rows), 'unique_source_keys': len({r['unique_key'] for r in rows}),
        'status_counts': dict(Counter(r['status'] or 'Not recorded' for r in rows)),
        'agency_counts': dict(Counter(r['agency'] or 'Not recorded' for r in rows)),
        'category_counts': dict(Counter(r['complaint_type'] or 'Not recorded' for r in rows)),
        'invalid_date_rows': invalid, 'closure_before_creation': backwards,
        'closed_status_missing_closed_date': sum(r['status']=='Closed' and not r.get('closed_date') for r in rows),
        'nonclosed_status_with_closed_date': sum(r['status']!='Closed' and bool(r.get('closed_date')) for r in rows),
        'valid_closed_intervals': len(intervals), 'mean_recorded_closure_days': sum(intervals)/len(intervals) if intervals else None,
        'limits': 'Source timestamps retained as published, without inventing an AICTE deadline, Bureau ownership, overdue state or original narrative.'}


def evaluate_workspace(workspace, model, tokenizer, output_name='evaluation'):
    import numpy as np
    root = Path(workspace)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    raw = (root / 'corpus.json').read_bytes()
    if manifest.get('corpus_sha256') != digest(raw): raise ValueError('Corpus checksum does not match source manifest.')
    records = json.loads(raw)
    validate_records(records, manifest)
    output = root / output_name; output.mkdir(mode=0o700, exist_ok=False)
    reports = {}
    for source in manifest['sources']:
        dataset = source['dataset']; rows = [r for r in records if r['dataset'] == dataset and r.get('eligible')]
        if source['status'] != 'collected' or not rows:
            reports[dataset] = {'status': source['status'], 'records': 0, 'performance': None, 'reason': source.get('access_error') or source['usage_conditions']}; continue
        token_counts = {r['id']: len(tokenizer.encode(r['model_text']).ids) for r in rows}
        eligible = [r for r in rows if 0 < token_counts[r['id']] <= 256]
        queries, references, text_groups = split_records(eligible)
        ordered = queries + references; embedding_time = 0
        if ordered:
            started = time.perf_counter(); vectors = np.asarray(model.encode([r['model_text'] for r in ordered], normalize_embeddings=True, batch_size=32)); embedding_time = time.perf_counter()-started
            if vectors.shape != (len(ordered), 384) or not np.isfinite(vectors).all() or np.any(np.linalg.norm(vectors,axis=1) == 0): raise ValueError('Invalid local embeddings.')
            vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        else: vectors = np.empty((0,384))
        suggestions, retrieval_ms = [], []
        no_references = threshold_abstentions = 0
        for i, query in enumerate(queries):
            eligible_indexes = [len(queries)+j for j, r in enumerate(references) if dataset == 'oia' or (query.get('entity') and r.get('entity') == query['entity'])]
            no_references += not eligible_indexes
            before = len(suggestions)
            started = time.perf_counter()
            scores = [(j, float(vectors[i] @ vectors[j])) for j in eligible_indexes]
            scores.sort(key=lambda item: (-item[1], ordered[item[0]]['id']))
            for j, score in scores[:5]:
                if score >= THRESHOLD:
                    ref = ordered[j]; pair_id = digest((dataset+'|'+query['id']+'|'+ref['id']).encode())[:24]
                    suggestions.append({'pair_id': pair_id, 'query_id': query['id'], 'reference_id': ref['id'], 'cosine': score, 'category': query['category']})
            threshold_abstentions += bool(eligible_indexes) and len(suggestions) == before
            retrieval_ms.append((time.perf_counter()-started)*1000)
        by_id = {r['id']: r for r in ordered}
        blind_files(output, dataset, suggestions, by_id)
        write_new(output / f'{dataset}-suggestions.json', suggestions)
        reports[dataset] = {'status': 'unlabelled_probe', 'records': len(rows), 'eligible_records': len(eligible),
            'token_limit_exclusions': len(rows)-len(eligible), 'token_limit': 256, 'silent_truncation': False,
            'queries': len(queries), 'references': len(references), 'exact_representation_groups': text_groups,
            'encoded_records': len(ordered), 'duplicate_query_representations_held_out': len(eligible)-len(ordered),
            'scope': 'global education-summary transfer probe; institution identity unavailable' if dataset == 'oia' else 'same published company; not institution identity' if dataset == 'cfpb' else 'same published agency; structured workflow probe, not citizen narrative',
            'metrics': summarize(suggestions, {}, len(queries)),
            'category_breakdown': {key: {'queries': sum(r['category'] == key for r in queries), 'suggestions': sum(s['category'] == key for s in suggestions), 'error_rate': None} for key in sorted({r['category'] for r in queries})},
            'embedding_seconds': embedding_time, 'in_memory_retrieval_ms': {'total': sum(retrieval_ms), 'p95': float(np.percentile(retrieval_ms,95)) if retrieval_ms else None},
            'queries_without_eligible_references': no_references, 'threshold_abstentions': threshold_abstentions,
            'threshold_abstention_rate_among_eligible_queries': threshold_abstentions/(len(queries)-no_references) if len(queries)>no_references else None,
            'unavailable_embeddings': 0,
            'database_latency_ms': None, 'workflow': workflow_counts(rows) if dataset == 'nyc311' else None,
            'privacy_review': 'Automatic/minimal-field preparation; independent re-identification review pending.',
            'leakage': 'Frozen threshold, no training/calibration; exact normalized text groups kept on one side. Incident groups and near-duplicate independence unverified; no recall claim.'}
    report = {'schema_version': 1, 'model_revision': REVISION, 'threshold': THRESHOLD, 'production_policy_changed': False,
        'database_access': False, 'corpus_sha256': digest((root/'corpus.json').read_bytes()), 'tracks': reports,
        'institution_track': {'status': 'unavailable', 'reason': 'No authorized institution corpus or independently known incident matches supplied.'},
        'limitations': ['No dataset scores pooled.', 'No relationship labels invented.', 'No source outcomes interpreted as incident labels.',
            'Private annotations/text must not be committed.', 'Public identifiers may permit re-identification; no raw examples cleared for redistribution.']}
    write_new(output/'report.json', report)
    return report


def adjudicate(workspace, dataset, annotations, evaluation_name='evaluation'):
    if dataset not in ['oia','cfpb','nyc311']:
        raise ValueError('Unknown dataset.')
    root = Path(workspace); report = json.loads((root/evaluation_name/'report.json').read_text())
    if report['corpus_sha256'] != digest((root/'corpus.json').read_bytes()):
        raise ValueError('Corpus changed after retrieval; judgments cannot be reused silently.')
    suggestions = json.loads((root/evaluation_name/f'{dataset}-suggestions.json').read_text())
    with Path(annotations).open(encoding='utf-8-sig', newline='') as source:
        labels = final_labels(list(csv.DictReader(source)), {s['pair_id'] for s in suggestions})
    result = summarize(suggestions, labels, report['tracks'][dataset]['queries'])
    # A new result preserves the initial unlabelled report and the reviewer files.
    import uuid
    dest = root/evaluation_name/f'{dataset}-adjudicated-{uuid.uuid4().hex[:8]}.json'
    write_new(dest, {'dataset':dataset,'annotation_sha256':digest(Path(annotations).read_bytes()),'metrics':result,
        'category_breakdown': {key: summarize([s for s in suggestions if s['category']==key],labels,
            report['tracks'][dataset]['category_breakdown'][key]['queries']) for key in report['tracks'][dataset]['category_breakdown']}})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--model', default=os.environ.get('MODEL_PATH', '/models/minilm'))
    parser.add_argument('--calibration', default='/app/calibration.json')
    parser.add_argument('--output-name', default='evaluation')
    parser.add_argument('--adjudications', help='Completed private adjudication CSV; scores never determine labels.')
    parser.add_argument('--dataset', choices=['oia','cfpb','nyc311'])
    args = parser.parse_args()
    if Path(args.output_name).name != args.output_name or args.output_name in ['.', '..']: raise ValueError('Output must be a new child directory name.')
    if args.adjudications:
        if not args.dataset: parser.error('--dataset is required with --adjudications')
        print(json.dumps(adjudicate(args.workspace,args.dataset,args.adjudications,args.output_name))); return
    path = Path(args.model); calibration = json.loads(Path(args.calibration).read_text())
    if calibration['model_revision'] != REVISION or calibration['threshold'] != THRESHOLD or json.loads((path/'revision.json').read_text())['revision'] != REVISION:
        raise ValueError('Frozen B1 baseline does not match; no experiment performed.')
    if digest((path/'model.safetensors').read_bytes()) != WEIGHTS: raise ValueError('Model weights checksum mismatch.')
    os.environ['HF_HUB_OFFLINE'] = '1'; os.environ['TRANSFORMERS_OFFLINE'] = '1'
    started = time.perf_counter()
    from tokenizers import Tokenizer
    from sentence_transformers import SentenceTransformer
    import torch
    torch.set_num_threads(2)
    tokenizer = Tokenizer.from_file(str(path/'tokenizer.json')); tokenizer.no_truncation(); tokenizer.no_padding()
    model = SentenceTransformer(str(path), device='cpu', local_files_only=True); cold = time.perf_counter()-started
    warmup_started = time.perf_counter()
    model.encode(['Local encoder warm-up.'],normalize_embeddings=True)
    warmup = time.perf_counter()-warmup_started
    report = evaluate_workspace(args.workspace, model, tokenizer, args.output_name)
    write_new(Path(args.workspace)/args.output_name/'runtime.json', {'cold_model_load_seconds': cold, 'cold_timing_scope':'dependency imports plus first local model construction; excludes preflight checksums and interpreter startup',
        'warmup_seconds':warmup,'warmup_input':'one synthetic non-corpus sentence', 'device': 'cpu', 'model_revision': REVISION, 'threshold': THRESHOLD})
    print(json.dumps({key: {'status': value['status'], 'records': value['records']} for key,value in report['tracks'].items()}))


if __name__ == '__main__': main()
