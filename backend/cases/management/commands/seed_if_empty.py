from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from cases.models import Institution, Complaint


class Command(BaseCommand):
    help = 'Seed only a fresh, designated demo database; never augment existing data.'

    def handle(self, *args, **options):
        name = connection.settings_dict['NAME']
        if name not in ('coordination','coordination_audit') and not name.startswith(('coordination_demo_','test_coordination')):
            raise CommandError('Seeding is restricted to designated demo databases.')
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_advisory_xact_lock(26264, 100)')
            if Institution.objects.exists() or Complaint.objects.exists():
                self.stdout.write('Existing data detected: no fixtures or matching were added.')
                return
            call_command('seed_demo')
            call_command('seed_sih_demo')
        call_command('match_pending')
