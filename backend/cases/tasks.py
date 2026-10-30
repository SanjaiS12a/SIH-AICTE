from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from .models import Complaint, Notification

def send_reminders(now=None):
    now = now or timezone.now()
    count = 0
    for case in Complaint.objects.exclude(status='disposed').filter(due_at__lte=now + timedelta(days=7)):
        remaining = case.due_at - now
        kind = 'overdue' if remaining.total_seconds() < 0 else 'due_1_day' if remaining <= timedelta(days=1) else 'due_7_days'
        recipients = User.objects.filter(is_active=True).filter(
            Q(membership__role='coordinator') | Q(membership__role='officer', membership__bureau_id=case.bureau_id))
        for user in recipients:
            _, created = Notification.objects.get_or_create(user=user, case=case, kind=kind, deadline=case.due_at)
            count += created
    return count
