"""Isolated synthetic read/search scale test; not a full bulk-import claim."""
import concurrent.futures
import json
import platform
import resource
import statistics
import time
from types import SimpleNamespace
from pathlib import Path
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand,CommandError
from django.db import connection,close_old_connections
from django.http import QueryDict
from django.utils import timezone
from pgvector.django import CosineDistance
from cases.models import Institution,Bureau,Membership,Complaint,Escalation,OverlapCandidate
from cases.api import dashboard_data
from django.core.cache import caches
cache = caches['dashboard']
from cases.access import filtered_cases

class Command(BaseCommand):
 help='Measure 10k/100k records only inside a disposable coordination_scale_* database.'
 def add_arguments(self,parser):
  parser.add_argument('--sizes',nargs='+',type=int,choices=[1000,10000,100000],default=[1000,10000,100000])
 def handle(self,*args,**options):
  if not connection.settings_dict['NAME'].startswith('coordination_scale_'):raise CommandError('Requires an isolated coordination_scale_* database.')
  user=User.objects.create(username='scale-coordinator');Membership.objects.create(user=user,role='coordinator')
  bureau=Bureau.objects.create(code='SCALE',name='Synthetic scale bureau')
  Institution.objects.bulk_create([Institution(name=f'Scale Institution {i}',permanent_id=f'SCALE-{i}',region='Synthetic',district='Synthetic') for i in range(100)])
  institutions=list(Institution.objects.order_by('permanent_id').values_list('pk',flat=True));vector=[1.0]+[0.0]*383
  output={'platform':platform.platform(),'database':connection.settings_dict['NAME'],'concurrent_clients':10,'transport':'In-process Django calls with separate thread-local PostgreSQL connections; HTTP measured separately by benchmark_import.py','limits':'Synthetic metadata and identical unit vectors; registration histories, a small escalation queue and bounded relationship-review traffic; no attachments. Measures in-process endpoint scaling, not 100k upload or production matching accuracy.','results':[]}

  other_bureaus=[bureau]+[Bureau.objects.create(code=x,name=x+' synthetic Bureau') for x in ['PGRC','OTHER']]
  previous=0
  for size in sorted(set(options['sizes'])):
   started=time.perf_counter()
   with connection.cursor() as cursor:
    # Synthetic setup is deliberately server-side; the application import path is benchmarked separately.
    cursor.execute('''INSERT INTO cases_complaint
     (id, reference,submission_id,submission_fingerprint,institution_id,source_system,source_reference,category,classification,next_action,summary,description,incident_date,bureau_id,assigned_to_id,created_by_id,received_at,created_at,due_at,disposed_at,status,version,embedding,model_revision,matching_state,matching_error)
     SELECT gen_random_uuid(),'SCALE-'||i,gen_random_uuid(),'',(%s::uuid[])[1+(i %% 100)],'scale','SCALE-'||i,
     (ARRAY['refunds','admissions','documents','facilities','scholarships','administration'])[1+(i %% 6)],'unclassified','',
     'Synthetic fee refund allegation for load measurement.','Synthetic scale record; no real allegations.',NULL,(%s::bigint[])[1+(i %% 3)],NULL,%s,
     CURRENT_TIMESTAMP - make_interval(days => (i %% 120)::int),CURRENT_TIMESTAMP,
     CURRENT_TIMESTAMP + make_interval(days => (30-i %% 120)::int),
     CASE WHEN i %% 4=3 THEN CURRENT_TIMESTAMP-make_interval(days => ((i %% 120)::int-1)) ELSE NULL END,
     (ARRAY['registered','under_review','awaiting_response','disposed'])[1+(i %% 4)],1,%s::vector,'scale','complete',''
     FROM generate_series(%s,%s) AS i''',[institutions,[b.pk for b in other_bureaus],user.pk,str(vector),previous+1,size])
    cursor.execute("INSERT INTO cases_caseaction (case_id,actor_id,kind,reason,changes,created_at) SELECT id,%s,'registered','Synthetic scale registration','{}'::jsonb,received_at FROM cases_complaint WHERE substring(source_reference from 7)::int BETWEEN %s AND %s",[user.pk,previous+1,size])
    cursor.execute('ANALYZE cases_complaint')
   setup_seconds=time.perf_counter()-started;previous=size
   for distribution in ['distributed','concentrated']:
    with connection.cursor() as cursor:
     if distribution=='concentrated':cursor.execute('UPDATE cases_complaint SET institution_id=%s',[institutions[0]])
     else:cursor.execute("UPDATE cases_complaint SET institution_id=(%s::uuid[])[1+((substring(source_reference from 7))::int %% 100)]",[institutions])
     cursor.execute('ANALYZE cases_complaint')
    cache.clear()

    if not OverlapCandidate.objects.exists():
     for institution_id in institutions[:20]:
      pair=list(Complaint.objects.filter(institution_id=institution_id).order_by('pk')[:2])
      OverlapCandidate.objects.create(left=pair[0],right=pair[1],origin='manual',score=None,decision='unrelated',reason='Synthetic scale relationship',reviewer=user,reviewed_at=timezone.now())
    review_pairs=list(OverlapCandidate.objects.order_by('pk')[:20])
    if not Escalation.objects.exists():
     import uuid
     Escalation.objects.bulk_create([Escalation(case=c,created_by=user,submission_id=uuid.uuid4(),reason='Synthetic scale supervision') for c in Complaint.objects.exclude(status='disposed')[:20]])
    cold_start=time.perf_counter();cold_data=dashboard_data(SimpleNamespace(user=user,query_params=QueryDict('')));cold_ms=(time.perf_counter()-cold_start)*1000
    def simulate(index):
     close_old_connections();request=SimpleNamespace(user=User.objects.get(pk=user.pk),query_params=QueryDict(''));latencies=[]
     try:
      from rest_framework.test import APIClient
      client=APIClient();client.force_authenticate(user)
      for iteration in range(2):
       start=time.perf_counter();data=dashboard_data(request);assert data['total']==size;latencies.append(('dashboard',(time.perf_counter()-start)*1000))
       start=time.perf_counter();rows=list(filtered_cases(request)[:20]);assert len(rows)==20;latencies.append(('read',(time.perf_counter()-start)*1000))
       start=time.perf_counter();neighbors=list(Complaint.objects.filter(institution_id=institutions[0]).annotate(distance=CosineDistance('embedding',vector)).order_by('distance')[:5]);assert len(neighbors)==5;latencies.append(('exact_search',(time.perf_counter()-start)*1000))
       for label,path in [('registry','/api/institution-registry'),('profile',f'/api/institutions/{institutions[0]}'),('cases',f'/api/institutions/{institutions[0]}/cases'),('history',f'/api/institutions/{institutions[0]}/history'),('notices','/api/coordination-notices'),('escalations','/api/escalations'),('relationships','/api/overlaps?decision=all')]:
        start=time.perf_counter();response=client.get(path);assert response.status_code==200,(path,response.data);latencies.append((label,(time.perf_counter()-start)*1000))
       pair=review_pairs[iteration*10+index]
       start=time.perf_counter();response=client.post(f'/api/overlaps/{pair.pk}/review',{'expected_version':pair.version,'decision':'related_issue' if pair.decision=='unrelated' else 'unrelated','reason':f'Synthetic measured review {size} {distribution} {index} {iteration}'},format='json');assert response.status_code==200,response.data;latencies.append(('review',(time.perf_counter()-start)*1000))
      return latencies
     finally:close_old_connections()
    from unittest.mock import patch
    from rest_framework.throttling import UserRateThrottle
    with patch.object(UserRateThrottle,'THROTTLE_RATES',{'user':'100000/min'}), concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:measurements=[item for batch in pool.map(simulate,range(10)) for item in batch]
    result={'cold_dashboard_ms':cold_ms,'records':size,'distribution':distribution,'setup_seconds':setup_seconds,'peak_process_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'metrics':{}}
    for name in ['dashboard','read','exact_search','registry','profile','cases','history','notices','escalations','relationships','review']:
     values=sorted(v for k,v in measurements if k==name);result['metrics'][name]={'requests':len(values),'p50_ms':statistics.median(values),'p95_ms':values[int(.95*len(values))]}
    output['results'].append(result);self.stdout.write(json.dumps(result))
    suffix='-'+str(options['sizes'][0]) if len(options['sizes'])==1 else ''
    Path('/reports/completion-scale'+suffix+'.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
