"""Run through manage.py shell in the audit container, after HTTP regressions."""
import json
import math
import time
from pathlib import Path
from django.conf import settings
from django.db import connection
from cases.matching import encoder, runtime, tokenizer

assert connection.settings_dict['NAME'] == 'coordination_audit', 'Audit database required'
frozen = json.loads((settings.BASE_DIR / 'model-manifest.json').read_text())
assert runtime()[1] == frozen['revision']
started = time.perf_counter()
model = encoder()
cold = time.perf_counter() - started
summaries = [f'Tuition fees have not been refunded following cancellation of admission for programme cohort {n}. '
    'The student requests repayment and a written response from the institution. '
    'This is a fictional performance record without personal information.' for n in range(1000)]
tokens = tokenizer()
maximum = max(len(tokens.encode(text).ids) for text in summaries)
assert maximum <= 256
model.encode(summaries[:2], normalize_embeddings=True)
started = time.perf_counter()
vectors = model.encode(summaries, normalize_embeddings=True, batch_size=32)
seconds = time.perf_counter() - started
assert vectors.shape == (1000, 384)
assert abs(math.sqrt(sum(float(x)**2 for x in vectors[0])) - 1) < 1e-5
result = {'device':'cpu', 'threads':2, 'revision':frozen['revision'], 'summaries':1000,
    'max_wordpieces':maximum, 'cold_model_load_seconds':cold, 'warm_encode_seconds':seconds,
    'summaries_per_second':1000/seconds, 'scope':'Encoder only; excludes queue, database matching and HTTP.'}
target = settings.RESULTS_DIR / 'encoder-performance.json'
assert not target.exists(), 'Keep earlier measurement evidence'
target.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
