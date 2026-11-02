"""Scoped incident reporting with ten independent synthetic audit users."""
import concurrent.futures
import csv
import io
import json
import statistics
import time
import uuid
from benchmark import browser, BASE, RESULTS
from benchmark_import import request


def main():
    client,jar=browser()
    institution=request(client,jar,'/api/institutions')[0]['id']
    cases=request(client,jar,'/api/cases?institution='+institution)['results'][:6]
    if len(cases)!=6:raise ValueError('Six existing same-institution synthetic records required.')
    group=request(client,jar,'/api/incident-groups',{'submission_id':str(uuid.uuid4()),'institution':institution,
        'title':'Synthetic six-member performance fixture','reason':'Authored load-test fixture only; not a real-world incident finding.',
        'cases':[c['id'] for c in cases]})
    started=time.perf_counter()
    while True:
        expected=request(client,jar,'/api/incident-summary')['counts']
        if not expected['matching_pending']:break
        if time.perf_counter()-started>120:raise TimeoutError('Matching queue did not settle before the counts benchmark.')
        time.sleep(.5)
    assert expected['matching_failed']==0 and expected['matching_not_processed']==0
    assert expected['grouped_cases']==6 and expected['confirmed_groups']==1
    def simulate(index):
        own,_=browser(f'readiness-user-{index}');values=[]
        for _ in range(3):
            for name,path in [('summary','/api/incident-summary'),('cases','/api/incident-summary/records?metric=grouped_cases'),
                              ('groups','/api/incident-summary/records?metric=confirmed_groups'),('csv','/api/incident-summary.csv?metric=confirmed_groups')]:
                start=time.perf_counter()
                with own.open(BASE+path,timeout=120) as response:content=response.read().decode('utf-8')
                values.append((name,(time.perf_counter()-start)*1000))
                if name=='summary':assert json.loads(content)['counts']==expected
                elif name=='csv':assert len(list(csv.DictReader(io.StringIO(content))))==1
                else:assert json.loads(content)['count']==(6 if name=='cases' else 1)
        return values
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:values=[v for row in pool.map(simulate,range(10)) for v in row]
    lifecycle=lambda row:{key:row[key] for key in ['status','bureau','due_at','version']}
    before={row['id']:lifecycle(row) for row in cases}
    after={row['id']:lifecycle(request(client,jar,'/api/cases/'+row['id'])) for row in cases}
    assert before==after,'Grouping/reporting changed independent complaint lifecycles.'
    output={'transport':'HTTP localhost; ten different coordinator users and sessions','expected_counts':expected,
        'group_id':group['id'],'case_lifecycle_changed':False,'provenance':'Synthetic aggregation load, not matching accuracy','measurements':{}}
    for name in ['summary','cases','groups','csv']:
        timings=sorted(value for key,value in values if key==name)
        output['measurements'][name]={'requests':len(timings),'p50_ms':statistics.median(timings),'p95_ms':timings[min(len(timings)-1,int(.95*len(timings)))]}
    with (RESULTS/'incident-http.json').open('x',encoding='utf-8') as stream:json.dump(output,stream,indent=2)
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
