"""Bounded SQL profile on a fresh isolated database; never the demo/audit corpus."""
import json
import os
import sys
import time
import uuid
from unittest.mock import patch
from collections import Counter
from pathlib import Path

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from cases.models import Bureau, Complaint, Institution, Membership
from cases.matching import match_batch, revision
from cases.incident_reporting import summary


def main():
    assert connection.settings_dict['NAME'].startswith('coordination_core_profile_')
    assert not Complaint.objects.exists(), 'A new profile database is required.'
    user=User.objects.create_user('profile');Membership.objects.create(user=user,role='coordinator')
    bureau=Bureau.objects.create(code='RB',name='Synthetic profile Bureau')
    institution=Institution.objects.create(permanent_id='PROFILE-ONLY',name='Fictional profile institution',region='Synthetic',district='Synthetic')
    now=timezone.now();model=revision();vector=[1.0]+[0.0]*383
    size=int(os.environ.get('PROFILE_ROWS','1000'));assert size in (1000,10000)
    cases=[Complaint(submission_id=uuid.uuid4(),reference=f'PROFILE-{i}',source_reference=str(i),source_system='profile',
        institution=institution,bureau=bureau,created_by=user,summary='Fictional fee refund remains pending after admission cancellation.',
        description='Synthetic profiling only.',category='refunds',received_at=now,due_at=now,
        embedding=vector,model_revision=model,matching_state='complete' if i>=32 else 'pending') for i in range(size)]
    Complaint.objects.bulk_create(cases,batch_size=100)
    started=time.perf_counter()
    with CaptureQueriesContext(connection) as captured:match_batch([str(c.pk) for c in cases[:32]])
    elapsed=time.perf_counter()-started
    Complaint.objects.filter(pk__in=[c.pk for c in cases[:32]]).update(embedding=None,matching_state='pending')
    from cases.matching import encoder
    started=time.perf_counter();model_encoder=encoder();cold_load=time.perf_counter()-started
    encode_times=[]
    def encode(*args,**kwargs):
        started=time.perf_counter();result=model_encoder.encode(*args,**kwargs);encode_times.append(time.perf_counter()-started);return result
    started=time.perf_counter()
    with patch('cases.matching.encoder') as factory:
        factory.return_value.encode.side_effect=encode
        match_batch([str(c.pk) for c in cases[:32]])
    with_encoding=time.perf_counter()-started
    requests=APIRequestFactory();request=requests.get('/api/incident-summary');force_authenticate(request,user)
    with CaptureQueriesContext(connection) as aggregates:response=summary(request)
    assert response.status_code==200 and response.data['counts']['complaints']==size
    plans=[]
    with connection.cursor() as cursor:
        for sql in [q['sql'] for q in captured.captured_queries if 'ORDER BY' in q['sql'] and '<=>' in q['sql']][:1]+[q['sql'] for q in aggregates.captured_queries if 'COUNT(' in q['sql']]:
            cursor.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+sql);plans.append(cursor.fetchone()[0])
    result={'database':connection.settings_dict['NAME'],'cases':size,'batch_cases':32,'matching_seconds':elapsed,
        'matching_queries':len(captured),'matching_database_seconds':sum(float(q['time']) for q in captured.captured_queries),
        'query_types':dict(Counter(q['sql'].split()[0] for q in captured.captured_queries)),
        'slowest_matching_queries':sorted(captured.captured_queries,key=lambda q:float(q['time']),reverse=True)[:5],
        'summary_queries':len(aggregates),'summary_sql':aggregates.captured_queries,'plans':plans,
        'cold_encoder_seconds':cold_load,'warm_batch_with_encoding_seconds':with_encoding,'encode_seconds':sum(encode_times),
        'limit':'Synthetic SQL profile with pre-existing vectors; excludes encoding and is not matching accuracy.'}
    Path(os.environ['PROFILE_OUTPUT']).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('plans','summary_sql','slowest_matching_queries')}))


if __name__=='__main__':main()
