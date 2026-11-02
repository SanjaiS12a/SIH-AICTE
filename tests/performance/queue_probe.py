"""Measure idle broker dispatch separately from complaint age and matching work."""
import json
import os
import statistics
import sys
import time
from pathlib import Path
sys.path.insert(0,'/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection
from django_q.models import Task
from django_q.tasks import async_task


def main():
    assert connection.settings_dict['NAME']=='coordination_audit'
    values=[]
    for _ in range(12):
        start=time.time();key=async_task('time.time',task_name='core-readiness-idle-probe')
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            task=Task.objects.filter(pk=key).first()
            if task:
                assert task.success,task.result
                values.append((float(task.result)-start)*1000);break
            time.sleep(.05)
        else:raise TimeoutError('Idle audit worker did not dispatch.')
    result={'requests':len(values),'poll_seconds':settings.Q_CLUSTER['poll'],'workers':settings.Q_CLUSTER['workers'],
        'dispatch_ms':values,'p50_ms':statistics.median(values),'p95_ms':sorted(values)[-1],
        'scope':'Sequential idle audit broker time.time tasks, not full import or sustained throughput.'}
    with Path(os.environ['QUEUE_OUTPUT']).open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result))


if __name__=='__main__':main()
