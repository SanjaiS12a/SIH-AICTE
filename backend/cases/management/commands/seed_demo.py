import json
import os
import uuid
from datetime import timedelta, date
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django_q.models import Schedule
from cases.models import Institution, Bureau, Membership, Complaint, CaseAction
from cases.demo_data import seed_records, evaluation_dataset

class Command(BaseCommand):
    help = 'Add 500 fictional complaints and demo users. Safe to repeat; does not reset case decisions.'

    def handle(self, *args, **options):
        password = os.getenv('DEMO_PASSWORD', 'Demo-only-26264!')
        now = timezone.now()
        with transaction.atomic():
            bureaus = [Bureau.objects.get_or_create(code=code, defaults={'name': name})[0] for code, name in [
                ('RB','Regulation Bureau · demo'), ('PGRC','Public Grievance Redressal Cell · demo'), ('DEMO','Additional demonstration cell')]]
            users = {}
            for username, name, role, bureau in [
                ('coordinator','Aditi Sharma','coordinator',None), ('auditor','Ravi Menon','auditor',None),
                ('officer_rb','Meera Nair','officer',bureaus[0]), ('officer_pgrc','Arjun Rao','officer',bureaus[1]),
                ('officer_demo','Kiran Shah','officer',bureaus[2]), ('admin','Demo Administrator','',None)]:
                first, last = name.split(' ', 1)
                user, created = User.objects.get_or_create(username=username, defaults={'first_name':first,'last_name':last,'is_staff':username=='admin','is_superuser':username=='admin'})
                if created:
                    user.set_password(password)
                    user.save()
                if role:
                    Membership.objects.get_or_create(user=user, defaults={'role':role,'bureau':bureau})
                    group, _ = Group.objects.get_or_create(name=role)
                    user.groups.add(group)
                users[username] = user
            names = ['Aster','Cedar','Maple','Willow','Juniper','Birch','Saffron','Fern','Linden','Olive',
                     'Silverleaf','Meadow','Riverbend','Hillcrest','Brookfield','Pinecrest','Woodland','Elmwood','Lakeside','Orchard',
                     'Clearwater','Westwood','Evergreen','Rosewood','Springfield','Oakridge','Bluebell','Northfield','Greenvale','Stonebridge']
            institutions = [Institution.objects.get_or_create(permanent_id=f'DEMO-{i+1:04d}', defaults={
                'name': f'{name} Institute of Technology', 'region':['Southern','Western','Northern','Eastern','Central'][i%5],
                'district':f'Fictional district {i+1}'})[0] for i,name in enumerate(names)]
            for row in seed_records():
                n = row['index']
                received = now - timedelta(days=row['age'], hours=n%20)
                case, created = Complaint.objects.get_or_create(source_system='synthetic', source_reference=f'SYN-{n+1:05d}', defaults={
                    'reference': f'C-DEMO-{n+1:04d}', 'submission_id':uuid.uuid5(uuid.NAMESPACE_URL,f'aicte-demo-{n}'),
                    'institution':institutions[row['institution_index']], 'category':row['category'],
                    'summary':row['summary'], 'description':row['description'], 'incident_date':date(row['year'],6,15),
                    'bureau':bureaus[n%3], 'created_by':users['coordinator'], 'received_at':received,
                    'due_at':received+timedelta(days=settings.DEMO_DEADLINE_DAYS), 'status':row['status'],
                    'disposed_at':min(received+timedelta(days=10),now) if row['status']=='disposed' else None,
                    'assigned_to':users[['officer_rb','officer_pgrc','officer_demo'][n%3]]})
                if created:
                    initial = CaseAction.objects.create(case=case, actor=users['coordinator'], kind='registered', reason='Synthetic complaint imported for demonstration.', changes={'bureau':case.bureau.code})
                    CaseAction.objects.filter(pk=initial.pk).update(created_at=received)
                    if n % 11 == 0:
                        CaseAction.objects.create(case=case, actor=users['coordinator'], kind='note', reason='Demo scrutiny note: request supporting evidence before determining the allegation.')
                    if n % 17 == 0:
                        previous_bureau = bureaus[(n+1)%3]
                        CaseAction.objects.create(case=case, actor=users['coordinator'], kind='transfer',
                            reason='Synthetic historical transfer for cross-bureau coordination.',
                            changes={'bureau':{'before':previous_bureau.code,'after':case.bureau.code}})
                    if row['status']=='disposed':
                        action = CaseAction.objects.create(case=case, actor=users['coordinator'], kind='status', reason='Synthetic resolution: written response recorded for demonstration.', changes={'status':{'before':'under_review','after':'disposed'}})
                        CaseAction.objects.filter(pk=action.pk).update(created_at=case.disposed_at)
            Schedule.objects.get_or_create(name='deadline-reminders', defaults={'func':'cases.tasks.send_reminders','schedule_type':Schedule.MINUTES,'minutes':5,'repeats':-1})
        out = Path('/data') if Path('/data').exists() else settings.BASE_DIR.parent/'data'
        out.mkdir(exist_ok=True)
        (out/'evaluation.json').write_text(json.dumps(evaluation_dataset(),indent=2),encoding='utf-8')
        self.stdout.write(self.style.SUCCESS('Demo ready: 30 fictional institutions, 500 complaints, 6 users. Existing records preserved.'))
