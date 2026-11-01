"""Measure actual reminder generation and an idempotent rerun on the audit corpus."""
import json
import time
from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from cases.models import Complaint
from cases.tasks import send_reminders

assert connection.settings_dict['NAME'] == 'coordination_audit'
target = settings.RESULTS_DIR / 'reminder-performance.json'
assert not target.exists(), 'Preserve earlier measurements'
samples = []
for _ in range(2):
    started = time.perf_counter()
    with CaptureQueriesContext(connection) as queries:
        created = send_reminders()
    samples.append({'seconds':time.perf_counter()-started, 'created':created, 'queries':len(queries)})
    assert len(queries) == 1
assert samples[1]['created'] == 0
report = {'cases':Complaint.objects.count(), 'samples':samples,
    'scope':'Current dates and memberships; existing reminders preserved. Includes conflict checks on existing rows.'}
target.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
