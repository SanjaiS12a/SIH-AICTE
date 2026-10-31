"""Read-only comparison on new project test data; never fits or activates a model."""
import csv
import gc
import hashlib
import io
import json
import platform
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics import average_precision_score, roc_auc_score

from prepare_public_pairs import download, normalized
from train_public_paraphrase import pair_scores
from train_matching import metrics

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'tests/results'
MRPC_SHA = 'a623ed1cbdf445b11f8e249acbf649d7d3a5ee58c918554c40cbd8307e488693'
MRPC_URL = 'https://huggingface.co/datasets/nyu-mll/glue/resolve/bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c/mrpc/test-00000-of-00001.parquet'


def education_pairs(fixture):
    families = fixture['families']
    rows = []
    for i, family in enumerate(families):
        for kind, text, label in [('same_incident', family['paraphrase'], 1),
                                  ('distinct_incident', family['distinct'], 0),
                                  ('different_issue', families[(i + 1) % len(families)]['anchor'], 0)]:
            rows.append({'id': f"{family['id']}-{kind}", 'kind': kind,
                         'sentence1': family['anchor'], 'sentence2': text, 'label': label})
    return rows


def unseen(rows, previous):
    retained = [r for r in rows if all(normalized(r[k]) not in previous for k in ['sentence1', 'sentence2'])]
    return retained, len(rows) - len(retained)


def summarize(scores, rows, cutoff):
    labels = np.array([r['label'] for r in rows], dtype=bool)
    result = metrics(scores, labels, cutoff)
    result.update(threshold=cutoff, pairs=len(rows), positives=int(labels.sum()),
                  accuracy=float(np.mean((scores >= cutoff) == labels)),
                  tn=int(np.sum((scores < cutoff) & ~labels)),
                  roc_auc=float(roc_auc_score(labels, scores)),
                  average_precision=float(average_precision_score(labels, scores)))
    return result


def main():
    torch.set_num_threads(2)
    report_path = RESULTS / 'fresh-model-comparison.json'
    if report_path.exists():
        raise FileExistsError('Fresh test results already exist. Keep the first run; do not tune on this test.')
    experiment = json.loads((RESULTS / 'public-paraphrase-training.json').read_text(encoding='utf-8'))
    data = ROOT / 'data/research/fresh_comparison'
    data.mkdir(parents=True, exist_ok=True)
    raw = download(MRPC_URL, data / 'mrpc-test.parquet', MRPC_SHA)
    original = pq.read_table(io.BytesIO(raw)).to_pylist()
    assert len(original) == 1725 and {r['label'] for r in original} == {0, 1}
    mrpc = [dict(r, id=str(r['idx']), kind='news_paraphrase') for r in original]
    fixture_path = ROOT / 'tests/research/fresh_education_incidents.json'
    fixture = json.loads(fixture_path.read_text(encoding='utf-8'))
    previous = set()
    for name in ['train', 'validation', 'calibration', 'test']:
        for line in (ROOT / f'data/research/public_pairs/{name}.jsonl').read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            previous.update(normalized(row[k]) for k in ['sentence1', 'sentence2'])
    old_domain = json.loads((ROOT / 'data/research/education_pairs.json').read_text(encoding='utf-8'))
    previous.update(normalized(r['text']) for r in old_domain['records'])
    datasets = {}
    exclusions = {}
    for name, rows in [('mrpc', mrpc), ('education', education_pairs(fixture))]:
        datasets[name], exclusions[name] = unseen(rows, previous)
        assert len(datasets[name]) > 0 and len({r['label'] for r in datasets[name]}) == 2
    report = {'date': '2026-10-31', 'protocol': 'No training, new calibration, threshold search or checkpoint selection. Previously frozen PAWS thresholds for MRPC; previously frozen synthetic-domain thresholds for education.',
              'mrpc': {'source': MRPC_URL, 'sha256': MRPC_SHA, 'downloaded_pairs': len(mrpc), 'labels': 'Human paraphrase labels from news; not complaint incident labels', 'licence': 'GLUE card: other; original MRPC terms apply. Raw source text is not redistributed in Git.'},
              'education': {'sha256': hashlib.sha256(fixture_path.read_bytes()).hexdigest(), **fixture},
              'overlap_exclusions': exclusions, 'overlap_rule': 'Exclude any pair sharing an NFKC/casefold/whitespace-normalized sentence with any prior PAWS split or education regression record. Does not establish absence from upstream pretraining or detect all near-duplicates.',
              'hardware': {'platform': platform.platform(), 'torch': torch.__version__, 'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
              'models': {}, 'active_model': 'unchanged baseline'}
    paths = {'baseline': ROOT / 'models/minilm', 'candidate': Path(experiment['run']) / 'candidate'}
    hashes = {n: hashlib.sha256((p / 'model.safetensors').read_bytes()).hexdigest() for n, p in paths.items()}
    assert hashes['candidate'] == experiment['checkpoint_sha256'] and hashes['baseline'] != hashes['candidate']
    detail = []
    for name, path in paths.items():
        started = time.perf_counter()
        model = SentenceTransformer(str(path), device=report['hardware']['device'], local_files_only=True)
        result = {'sha256': hashes[name], 'load_seconds': time.perf_counter() - started, 'datasets': {}}
        for dataset, rows in datasets.items():
            texts = list({r[k] for r in rows for k in ['sentence1', 'sentence2']})
            lengths = model.tokenizer(texts, truncation=False)['input_ids']
            assert max(map(len, lengths)) <= model.max_seq_length, 'Input would silently truncate'
            model.encode(['Warm inference'], normalize_embeddings=True, show_progress_bar=False)
            started = time.perf_counter()
            scores = pair_scores(model, rows)
            elapsed = time.perf_counter() - started
            assert np.isfinite(scores).all()
            cutoff = experiment[name]['calibration']['threshold'] if dataset == 'mrpc' else experiment[name]['synthetic_domain_regression']['calibration']['threshold']
            result['datasets'][dataset] = {**summarize(scores, rows, cutoff), 'embedding_and_scoring_seconds': elapsed, 'unique_texts': len(texts), 'max_wordpieces': max(map(len, lengths))}
            if dataset == 'education':
                result['datasets'][dataset]['by_kind'] = {kind: {'pairs': sum(r['kind'] == kind for r in rows), 'correct': sum(int((s >= cutoff) == bool(r['label'])) for r, s in zip(rows, scores) if r['kind'] == kind)} for kind in sorted({r['kind'] for r in rows})}
            detail.extend({'model': name, 'dataset': dataset, 'id': r['id'], 'kind': r['kind'], 'label': r['label'], 'cosine': float(s), 'threshold': cutoff, 'predicted': int(s >= cutoff)} for r, s in zip(rows, scores))
        report['models'][name] = result
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    assert all(hashlib.sha256((p / 'model.safetensors').read_bytes()).hexdigest() == hashes[n] for n, p in paths.items())
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (RESULTS / 'fresh-model-predictions.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(detail[0]))
        writer.writeheader()
        writer.writerows(detail)
    print(json.dumps(report['models'], indent=2))


if __name__ == '__main__':
    main()
