import time
from django.core.management.base import BaseCommand
from django_q.tasks import async_task
from cases.models import Complaint
from cases.matching import match_case

class Command(BaseCommand):
    help = 'Embed pending/failed cases. --queue schedules durable tasks instead of processing immediately.'
    def add_arguments(self, parser):
        parser.add_argument('--queue', action='store_true')
    def handle(self, *args, **options):
        started = time.perf_counter()
        ids = list(Complaint.objects.exclude(matching_state='complete').order_by('created_at').values_list('id',flat=True))
        for i, pk in enumerate(ids):
            if options['queue']:
                async_task('cases.matching.match_case',str(pk))
            else:
                match_case(str(pk))
            if (i+1)%50==0:
                self.stdout.write(f'{i+1}/{len(ids)} cases processed')
        self.stdout.write(f'{len(ids)} cases; {time.perf_counter()-started:.2f}s')
