"""GPU PAWS candidate experiment. Never activates/replaces the portal's baseline."""
import gc
import hashlib
import json
import math
import random
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.losses import ContrastiveLoss

from train_matching import calibrate, evaluate, metrics, vectors

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/research/public_pairs'
RESULTS = ROOT / 'tests/results'
SEED = 26264


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def seed():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)


def load(name):
    return [json.loads(line) for line in (DATA / f'{name}.jsonl').read_text(encoding='utf-8').splitlines()]


def pair_scores(model, pairs):
    model.eval()
    texts = list(dict.fromkeys(row[key] for row in pairs for key in ['sentence1', 'sentence2']))
    matrix = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    lookup = {text: i for i, text in enumerate(texts)}
    return np.array([float(matrix[lookup[row['sentence1']]] @ matrix[lookup[row['sentence2']]]) for row in pairs])


def measured(scores, pairs, threshold=None):
    labels = np.array([row['label'] for row in pairs], dtype=bool)
    calibration = calibrate(scores, labels) if threshold is None else None
    if threshold is None:
        if calibration is None:
            return {'precision_target_met': False, 'f1': 0, 'precision': 0, 'recall': 0, 'threshold': None}
        threshold = float(calibration[0])
    return {'threshold': threshold, **metrics(scores, labels, threshold), 'precision_target_met': calibration is not None if calibration is not None else None}


def epoch(model, rows, batch_size, output, pilot=False):
    model.train()
    loss_function = ContrastiveLoss(model)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5, weight_decay=.01)
    scaler = torch.amp.GradScaler('cuda')
    values = list(rows)
    random.shuffle(values)
    if pilot:
        values = values[:batch_size * 8]
    batches = math.ceil(len(values) / batch_size)
    accumulation_steps = max(1, 32 // batch_size)
    updates = math.ceil(batches / accumulation_steps)
    warmup = max(1, int(updates * .1))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: min((step + 1) / warmup, max(0., (updates - step) / max(1, updates - warmup))))
    optimizer.zero_grad(set_to_none=True)
    started = time.perf_counter()
    losses = []
    for step, start in enumerate(range(0, len(values), batch_size)):
        batch = values[start:start + batch_size]
        features = [{key: tensor.to('cuda') if isinstance(tensor, torch.Tensor) else tensor for key, tensor in model.tokenize([row[field] for row in batch]).items()} for field in ['sentence1', 'sentence2']]
        labels = torch.tensor([row['label'] for row in batch], dtype=torch.float32, device='cuda')
        # Scale the last accumulation group by its actual size, not always four.
        accumulation = min(accumulation_steps, batches - (step // accumulation_steps) * accumulation_steps)
        with torch.autocast(device_type='cuda', dtype=torch.float16):
            loss = loss_function(features, labels)
        if not torch.isfinite(loss):
            raise RuntimeError('Non-finite training loss; no candidate is approved')
        scaler.scale(loss / accumulation).backward()
        losses.append(float(loss.detach()))
        if (step + 1) % accumulation_steps == 0 or step + 1 == batches:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            previous_scale = scaler.get_scale()
            scaler.step(optimizer)
            scaler.update()
            if scaler.get_scale() >= previous_scale:
                scheduler.step()
            optimizer.zero_grad(set_to_none=True)
        if not pilot and ((step + 1) % 200 == 0 or step + 1 == batches):
            elapsed = time.perf_counter() - started
            progress = {'state': 'training', 'batch': step + 1, 'batches': batches, 'pairs_seen': min(start + batch_size, len(values)), 'seconds': elapsed, 'estimated_remaining_seconds': elapsed / (step + 1) * (batches - step - 1), 'mean_loss': float(np.mean(losses)), 'peak_allocated_bytes': torch.cuda.max_memory_allocated()}
            save(RESULTS / 'public-paraphrase-progress.json', progress)
            print(json.dumps(progress), flush=True)
    torch.cuda.synchronize()
    return {'seconds': time.perf_counter() - started, 'batches': batches, 'pairs': len(values), 'mean_loss': float(np.mean(losses))}


def export(candidate, report):
    destination = ROOT / 'artifacts'
    destination.mkdir(exist_ok=True)
    package = destination / 'minilm-public-paraphrase-candidate.zip'
    instructions = '''# Public paraphrase MiniLM candidate

EXPERIMENTAL: this is not a validated AICTE incident/duplicate detector. The deployed portal baseline was not replaced. Read experiment.json before use.

Base model: sentence-transformers/all-MiniLM-L6-v2 (https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), Apache-2.0. Training data: Google Research PAWS (https://github.com/google-research-datasets/paws), with publisher licence/attribution included. Public pair labels mean paraphrase/different meaning, not same complaint incident.

Unzip this archive. Install sentence-transformers==5.7.0 (and a supported CPU/CUDA PyTorch build), then:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("model", device="cpu", local_files_only=True)
vectors = model.encode(["First complaint summary", "Second complaint summary"], normalize_embeddings=True)
print(float(vectors[0] @ vectors[1]))
```

The complete model directory is required, not only model.safetensors. Output dimension: 384. Maximum input: 256 wordpieces; validate before encoding to avoid truncation. Retain the PAWS attribution/licence. Public paraphrase thresholds must not be treated as validated complaint thresholds. Re-embedding and application model-release gates are required before any portal deployment. Never merge or close cases automatically.
'''
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in candidate.rglob('*'):
            if path.is_file():
                archive.write(path, 'model/' + path.relative_to(candidate).as_posix())
        archive.writestr('README.md', instructions)
        archive.writestr('experiment.json', json.dumps(report, indent=2))
        archive.write(DATA / 'PAWS-LICENSE.txt', 'PAWS-LICENSE.txt')
        archive.write(DATA / 'MODEL-APACHE2-LICENSE.txt', 'MODEL-APACHE2-LICENSE.txt')
        archive.writestr('requirements.txt', 'sentence-transformers==5.7.0\n')
    checksum = hashlib.sha256(package.read_bytes()).hexdigest()
    package.with_suffix('.sha256').write_text(checksum + '  ' + package.name + '\n', encoding='utf-8')
    return {'path': str(package), 'sha256': checksum, 'bytes': package.stat().st_size}


def main():
    if not torch.cuda.is_available():
        raise RuntimeError('This experiment requires a working CUDA training environment; CPU fallback is not hidden.')
    seed()
    torch.set_num_threads(2)
    started = time.perf_counter()
    train, validation, calibration, test = [load(name) for name in ['train', 'validation', 'calibration', 'test']]
    audit = json.loads((RESULTS / 'public-pairs-audit.json').read_text(encoding='utf-8'))
    for name in ['train', 'validation', 'calibration', 'test']:
        assert hashlib.sha256((DATA / f'{name}.jsonl').read_bytes()).hexdigest() == audit['splits'][name]['sha256']
    run = ROOT / 'models/experiments' / ('public-paws-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    run.mkdir(parents=True)
    report = {'purpose': 'Public PAWS paraphrase candidate; not trained on AICTE incident labels', 'run': str(run), 'data_audit': audit, 'torch': torch.__version__, 'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0), 'gpu_total_bytes': torch.cuda.get_device_properties(0).total_memory, 'seed': SEED, 'epochs': 1, 'learning_rate': 1e-5, 'gradient_accumulation': 4, 'precision': 'CUDA AMP float16 with FP32 model weights', 'loss': 'ContrastiveLoss, cosine distance, margin 0.5', 'active_model': 'unchanged baseline', 'approval': 'Experimental candidate only; no automatic portal promotion'}
    batch_size = 32
    while True:
        model = SentenceTransformer(str(ROOT / 'models/minilm'), device='cuda', local_files_only=True)
        try:
            report['pilot'] = epoch(model, train, batch_size, run, pilot=True)
            break
        except torch.cuda.OutOfMemoryError:
            if batch_size == 1:
                raise
            batch_size //= 2
        finally:
            del model
            gc.collect()
            torch.cuda.empty_cache()
    report['batch_size'] = batch_size
    report['gradient_accumulation'] = max(1, 32 // batch_size)
    report['effective_batch_size'] = batch_size * report['gradient_accumulation']
    report['estimated_epoch_seconds'] = report['pilot']['seconds'] / report['pilot']['batches'] * math.ceil(len(train) / batch_size)
    save(RESULTS / 'public-paraphrase-training.json', report)
    print(json.dumps({'pilot': report['pilot'], 'batch_size': batch_size, 'estimated_epoch_seconds': report['estimated_epoch_seconds']}), flush=True)
    seed()
    model = SentenceTransformer(str(ROOT / 'models/minilm'), device='cuda', local_files_only=True)
    report['baseline_validation'] = measured(pair_scores(model, validation), validation)
    torch.cuda.reset_peak_memory_stats()
    report['training'] = epoch(model, train, batch_size, run)
    candidate = run / 'candidate'
    model.eval()
    model.save(str(candidate))
    report['candidate_validation'] = measured(pair_scores(model, validation), validation)
    report['checkpoint_selected_on'] = 'Validation only; one predeclared epoch, no test-driven hyperparameter or checkpoint changes'
    report['peak_cuda_bytes'] = torch.cuda.max_memory_allocated()
    del model
    gc.collect()
    torch.cuda.empty_cache()
    # Freeze both models/cutoffs on calibration before measuring the official test once.
    for name, path in [('baseline', ROOT / 'models/minilm'), ('candidate', candidate)]:
        model = SentenceTransformer(str(path), device='cuda', local_files_only=True)
        calibrated = measured(pair_scores(model, calibration), calibration)
        scores = pair_scores(model, test)
        report[name] = {'calibration': calibrated, 'test': measured(scores, test, calibrated['threshold']) if calibrated['threshold'] is not None else {'not_evaluated_at_operating_threshold': 'Precision floor could not be calibrated'}}
        domain = json.loads((ROOT / 'data/research/education_pairs.json').read_text(encoding='utf-8'))
        matrix = vectors(model, domain['records'])
        domain_calibration = evaluate(matrix, domain['records'], domain['pairs'], 'calibration')
        report[name]['synthetic_domain_regression'] = {'calibration': domain_calibration, 'test': evaluate(matrix, domain['records'], domain['pairs'], 'test', domain_calibration['threshold']) if domain_calibration['calibration_passed'] else None, 'limitation': 'Previously used authored synthetic regression, not new real-world evidence'}
        del model
        gc.collect()
        torch.cuda.empty_cache()
    report['checkpoint_sha256'] = hashlib.sha256((candidate / 'model.safetensors').read_bytes()).hexdigest()
    save(candidate / 'revision.json', {'revision': 'public-paws-' + report['checkpoint_sha256'][:16], 'base': 'all-MiniLM-L6-v2'})
    save(candidate / 'evaluation.json', report)
    report['seconds_before_packaging'] = time.perf_counter() - started
    save(run / 'experiment.json', report)
    report['package'] = export(candidate, report)
    report['total_seconds'] = time.perf_counter() - started
    save(run / 'experiment.json', report)
    save(RESULTS / 'public-paraphrase-training.json', report)
    save(RESULTS / 'public-paraphrase-progress.json', {'state': 'complete', 'run': str(run), 'package': report['package']})
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
