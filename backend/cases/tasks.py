from datetime import timedelta
from django.contrib.auth.models import User
from django.db import transaction, connection
from django.utils import timezone
from .models import Notification, Escalation


@transaction.atomic
def notify_escalation(escalation_id):
    escalation = Escalation.objects.get(pk=escalation_id)
    recipients = User.objects.filter(is_active=True, membership__role='coordinator')
    count = 0
    for user in recipients:
        _, created = Notification.objects.get_or_create(user=user, escalation=escalation,
            defaults={'case_id': escalation.case_id, 'kind': 'escalation'})
        count += created
    return count

def send_reminders(now=None):
    now = now or timezone.now()
    # One statement avoids per-case queries; the unique constraint also handles concurrent runs.
    with connection.cursor() as cursor:
        cursor.execute('''
            INSERT INTO cases_notification (user_id,case_id,kind,deadline,escalation_id,read,created_at)
            SELECT u.id,c.id,
                CASE WHEN c.due_at < %s THEN 'overdue'
                     WHEN c.due_at <= %s THEN 'due_1_day' ELSE 'due_7_days' END,
                c.due_at,NULL,FALSE,%s
            FROM cases_complaint c
            JOIN cases_membership m ON m.role='coordinator' OR (m.role='officer' AND m.bureau_id=c.bureau_id)
            JOIN auth_user u ON u.id=m.user_id AND u.is_active
            WHERE c.status <> 'disposed' AND c.due_at <= %s
            ORDER BY c.id,u.id
            ON CONFLICT (user_id,case_id,kind,deadline) DO NOTHING
        ''', [now, now+timedelta(days=1), timezone.now(), now+timedelta(days=7)])
        return cursor.rowcount
