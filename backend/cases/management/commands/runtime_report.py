import json
import platform
import statistics
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from cases.models import Complaint, OverlapCandidate

class Command(BaseCommand):
    help = 'Record measured matching durations separately from queue wait.'
    def handle(self,*args,**options):
        qs=Complaint.objects.filter(matching_duration_ms__isnull=False).order_by('matched_at')
        durations=list(qs.values_list('matching_duration_ms',flat=True))
        queue=list(qs.values_list('matching_queue_ms',flat=True))
        def stats(values):
            values=sorted(values)
            return {'samples':len(values),'p50_ms':statistics.median(values),'p95_ms':values[min(len(values)-1,int(len(values)*.95))]} if values else None
        result={'platform':platform.platform(),'matching_including_first_cold_load':stats(durations),
                'matching_after_first_case':stats(durations[1:]),'queue_wait':stats([x for x in queue if x is not None]),
                'states':{s:Complaint.objects.filter(matching_state=s).count() for s in ['pending','complete','failed']},
                'overlap_pairs':OverlapCandidate.objects.count(),
                'note':'Stored durations include native and container verification runs and worker cold starts. Seed batch waits are not online submission latency; queue wait is time since case creation, including downtime.'}
        dest=settings.RESULTS_DIR
        dest.mkdir(exist_ok=True);(dest/'matching-runtime.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        self.stdout.write(json.dumps(result,indent=2))
