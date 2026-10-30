"""HTTP benchmark: 10 simulated sessions; retains clearly marked synthetic submissions."""
import concurrent.futures
import http.cookiejar
import json
import os
import platform
import statistics
import time
import urllib.request
import urllib.parse
import uuid
from pathlib import Path

BASE = os.getenv('BENCHMARK_URL', 'http://127.0.0.1:8000')

def browser():
    jar=http.cookiejar.CookieJar()
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    client.open(BASE+'/accounts/login/').read()
    csrf=next(c.value for c in jar if c.name=='csrftoken')
    body=urllib.parse.urlencode({'username':'coordinator','password':os.getenv('DEMO_PASSWORD','Demo-only-26264!'),'csrfmiddlewaretoken':csrf,'next':'/api/session'}).encode()
    client.open(BASE+'/accounts/login/',data=body).read()
    return client,jar

def simulate(index):
    client,jar=browser()
    rows=[]
    for kind,path in [('read','/api/cases?bureau=RB'),('dashboard','/api/dashboard')]*5:
        start=time.perf_counter()
        result=json.loads(client.open(BASE+path).read())
        assert ('count' in result if kind=='read' else 'total' in result)
        rows.append((kind,(time.perf_counter()-start)*1000))
    institutions=json.loads(client.open(BASE+'/api/institutions').read())
    body={'submission_id':str(uuid.uuid4()),'institution':institutions[0]['id'],'bureau':'RB',
          'source_system':'benchmark','source_reference':f'BENCH-{uuid.uuid4()}', 'category':'refunds',
          'summary':'The college withheld a tuition refund after an admission cancellation.',
          'description':'Fictional load-test complaint. No real institution or person is involved.'}
    csrf=next(c.value for c in jar if c.name=='csrftoken')
    request=urllib.request.Request(BASE+'/api/cases',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-CSRFToken':csrf})
    start=time.perf_counter();result=client.open(request)
    assert result.status==201
    rows.append(('create',(time.perf_counter()-start)*1000))
    return rows

def main():
    started=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        rows=[row for batch in pool.map(simulate,range(10)) for row in batch]
    output={'concurrent_sessions':10,'platform':platform.platform(),'seconds':time.perf_counter()-started,
            'transport':'HTTP localhost; 10 separate authenticated sessions', 'results':{}}
    for kind in ['read','dashboard','create']:
        values=sorted(value for name,value in rows if name==kind)
        output['results'][kind]={'requests':len(values),'p50_ms':statistics.median(values),'p95_ms':values[min(len(values)-1,int(.95*len(values)))],
                                 'target_p95_ms':1000 if kind=='dashboard' else 500}
    dest=Path(__file__).resolve().parent.parent/'tests/results'/'latency.json';dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
