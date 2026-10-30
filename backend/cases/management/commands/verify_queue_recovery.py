import json
import time
import uuid
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django_q.cluster import Cluster
from django_q.models import OrmQ
from rest_framework.test import APIClient
from cases.models import Complaint, Institution

class Command(BaseCommand):
    help = 'Verify two real durable jobs across a controlled worker stop/restart. Run without another worker.'

    def handle(self,*args,**options):
        client=APIClient();client.force_authenticate(User.objects.get(username='coordinator'))
        institution=Institution.objects.first()
        cases=[]
        for cycle in range(2):
            result=client.post('/api/cases',{'submission_id':str(uuid.uuid4()),'institution':str(institution.pk),
                'bureau':'RB','source_system':'queue-recovery-check','source_reference':str(uuid.uuid4()),
                'category':'refunds','summary':'A tuition fee refund remains unpaid after withdrawal.',
                'description':'Synthetic worker recovery acceptance check.'},format='json')
            assert result.status_code==201,result.data
            case_id=result.data['id']
            assert Complaint.objects.get(pk=case_id).matching_state=='pending'
            assert OrmQ.objects.exists()
            cluster=Cluster()
            try:
                cluster.start()
                deadline=time.monotonic()+90
                while time.monotonic()<deadline:
                    case=Complaint.objects.get(pk=case_id)
                    if case.matching_state=='complete':break
                    if case.matching_state=='failed':raise AssertionError(case.matching_error)
                    time.sleep(.2)
                else:raise AssertionError('Durable task did not finish before the test deadline.')
                cases.append(str(case_id))
            finally:
                cluster.stop()
        dest=Path('/reports') if Path('/reports').exists() else settings.BASE_DIR.parent/'reports'
        dest.mkdir(exist_ok=True)
        report={'worker_cycles':2,'queued_while_stopped':True,'processed_after_restart':True,'cases':cases}
        (dest/'queue-recovery.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        self.stdout.write(self.style.SUCCESS('Durable jobs survived worker stop/restart; both completed.'))
