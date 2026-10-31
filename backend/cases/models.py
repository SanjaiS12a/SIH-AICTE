import uuid
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.db.models import Q
from pgvector.django import VectorField

class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    permanent_id = models.CharField(max_length=40, unique=True)
    region = models.CharField(max_length=60)
    district = models.CharField(max_length=80)
    address = models.CharField(max_length=500, blank=True)
    official_email = models.EmailField(blank=True)
    official_phone = models.CharField(max_length=30, blank=True)
    version = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

class Bureau(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.code

class Membership(models.Model):
    ROLES = [(x, x.title()) for x in ['officer', 'coordinator', 'auditor']]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membership')
    role = models.CharField(max_length=20, choices=ROLES)
    bureau = models.ForeignKey(Bureau, on_delete=models.PROTECT, null=True, blank=True)

class Complaint(models.Model):
    CLASSIFICATIONS = [('grievance', 'Grievance'), ('regulatory_compliance', 'Regulatory / Compliance'), ('unclassified', 'Unclassified')]
    STATUSES = [(x, x.replace('_', ' ').title()) for x in ['registered', 'under_review', 'awaiting_response', 'disposed']]
    CATEGORIES = [(x, x.title()) for x in ['admissions', 'refunds', 'documents', 'facilities', 'scholarships', 'administration']]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=32, unique=True)
    submission_id = models.UUIDField(unique=True)
    submission_fingerprint = models.CharField(max_length=64, blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT, related_name='complaints')
    source_system = models.CharField(max_length=40, default='manual')
    source_reference = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    classification = models.CharField(max_length=24, choices=CLASSIFICATIONS, default='unclassified', db_index=True)
    next_action = models.CharField(max_length=1000, blank=True, default='')
    next_action_date = models.DateField(null=True, blank=True)
    summary = models.TextField(max_length=2000)
    description = models.TextField(max_length=10000)
    incident_date = models.DateField(null=True, blank=True)
    bureau = models.ForeignKey(Bureau, on_delete=models.PROTECT)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='assigned_cases')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_cases')
    received_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField()
    disposed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=STATUSES, default='registered')
    version = models.PositiveIntegerField(default=1)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    model_revision = models.CharField(max_length=150, blank=True)
    matching_state = models.CharField(max_length=16, default='pending', choices=[(x, x) for x in ['pending', 'complete', 'failed']])
    matching_error = models.CharField(max_length=200, blank=True)
    matched_at = models.DateTimeField(null=True, blank=True)
    matching_duration_ms = models.FloatField(null=True, blank=True)
    matching_queue_ms = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-received_at', '-id']
        constraints = [models.UniqueConstraint(fields=['source_system', 'source_reference'], name='unique_source_reference'),
                       models.CheckConstraint(condition=Q(classification__in=['grievance', 'regulatory_compliance', 'unclassified']), name='valid_case_classification'),
                       models.CheckConstraint(condition=Q(next_action_date__isnull=True) | ~Q(next_action=''), name='next_action_date_needs_text'),
                       models.CheckConstraint(condition=~Q(status='disposed') | Q(next_action='', next_action_date__isnull=True), name='closed_case_no_next_action')]
        indexes = [models.Index(fields=['institution']), models.Index(fields=['bureau', 'status']),
                   models.Index(fields=['due_at']), models.Index(fields=['received_at'])]

    def __str__(self):
        return self.reference

class CaseAction(models.Model):
    case = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name='actions')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=30)
    reason = models.TextField(max_length=4000)
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['created_at', 'id']

class OverlapCandidate(models.Model):
    left = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name='left_overlaps')
    right = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name='right_overlaps')
    score = models.FloatField(null=True, blank=True)
    origin = models.CharField(max_length=12, choices=[('semantic', 'Model-scored'), ('manual', 'Manual')], default='semantic')
    evidence = models.JSONField(default=dict)
    model_revision = models.CharField(max_length=150, blank=True, default='')
    decision = models.CharField(max_length=24, default='pending', choices=[(x, x) for x in ['pending', 'same_incident', 'related_issue', 'unrelated']])
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    reason = models.TextField(blank=True, max_length=4000)
    reviewed_at = models.DateTimeField(null=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['left', 'right'], name='unique_ordered_pair'),
                       models.CheckConstraint(condition=Q(left__lt=models.F('right')), name='ordered_pair'),
                       models.CheckConstraint(condition=Q(origin='semantic', score__isnull=False) | (Q(origin='manual', score__isnull=True) & ~Q(decision='pending')), name='relationship_origin_score')]
        ordering = ['-created_at', '-id']

class CoordinationRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_id = models.UUIDField(unique=True)
    submission_fingerprint = models.CharField(max_length=64)
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT)
    cases = models.ManyToManyField(Complaint)
    lead_bureau = models.ForeignKey(Bureau, on_delete=models.PROTECT)
    lead_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.TextField(max_length=4000)
    state = models.CharField(max_length=20, default='in_coordination', choices=[('in_coordination', 'In coordination'), ('closed', 'Closed')])
    outcome = models.TextField(max_length=4000, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='opened_coordinations')
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    closed_at = models.DateTimeField(null=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [models.CheckConstraint(condition=Q(state='in_coordination', closed_at__isnull=True, outcome='') | (Q(state='closed', closed_at__isnull=False) & ~Q(outcome='')), name='coordination_closure_state')]


class CoordinationParticipant(models.Model):
    record = models.ForeignKey(CoordinationRecord, on_delete=models.PROTECT, related_name='participants')
    bureau = models.ForeignKey(Bureau, on_delete=models.PROTECT)
    officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    instruction = models.TextField(max_length=2000)
    action_date = models.DateField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    completion_note = models.TextField(max_length=2000, blank=True)

    class Meta:
        ordering = ['bureau__code']
        constraints = [models.UniqueConstraint(fields=['record', 'bureau'], name='one_coordination_participant_per_bureau'),
            models.CheckConstraint(condition=~Q(instruction=''), name='coordination_instruction_required'),
            models.CheckConstraint(condition=Q(completed_at__isnull=True, completion_note='') | (Q(completed_at__isnull=False, acknowledged_at__isnull=False) & ~Q(completion_note='')), name='coordination_participant_completion')]


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name='attachments')
    file = models.FileField(upload_to='evidence/')
    original_name = models.CharField(max_length=180)
    content_type = models.CharField(max_length=80)
    size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class Escalation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_id = models.UUIDField(unique=True)
    case = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name='escalations')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_escalations')
    reason = models.TextField(max_length=4000)
    status = models.CharField(max_length=12, choices=[('pending', 'Pending review'), ('resolved', 'Resolved')], default='pending')
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='resolved_escalations')
    resolution_reason = models.TextField(max_length=4000, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['status', 'created_at'])]
        constraints = [
            models.UniqueConstraint(fields=['case'], condition=Q(status='pending'), name='one_pending_escalation_per_case'),
            models.CheckConstraint(condition=~Q(reason=''), name='escalation_reason_required'),
            models.CheckConstraint(condition=Q(status='pending', resolved_by__isnull=True, resolved_at__isnull=True, resolution_reason='') |
                (Q(status='resolved', resolved_by__isnull=False, resolved_at__isnull=False) & ~Q(resolution_reason='')), name='escalation_resolution_state'),
        ]

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case = models.ForeignKey(Complaint, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20)
    deadline = models.DateTimeField(null=True, blank=True)
    escalation = models.ForeignKey(Escalation, on_delete=models.PROTECT, null=True, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'case', 'kind', 'deadline'], name='unique_reminder'),
                       models.UniqueConstraint(fields=['user', 'escalation'], condition=Q(escalation__isnull=False), name='unique_escalation_notification'),
                       models.CheckConstraint(condition=(Q(escalation__isnull=True, deadline__isnull=False) & ~Q(kind='escalation')) |
                           Q(escalation__isnull=False, deadline__isnull=True, kind='escalation'), name='notification_event_shape')]
        ordering = ['-created_at', '-id']

class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=40)
    detail = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class ImportJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20, choices=[(x, x) for x in ['complaints', 'monthly', 'snapshot']])
    filename = models.CharField(max_length=180)
    headers = models.JSONField(default=list)
    mapping = models.JSONField(default=dict)
    state = models.CharField(max_length=20, default='preview')
    error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ImportRow(models.Model):
    job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='rows')
    number = models.PositiveIntegerField()
    raw = models.JSONField(default=dict)
    data = models.JSONField(default=dict)
    state = models.CharField(max_length=20, default='pending')
    error = models.CharField(max_length=1000, blank=True)
    case = models.ForeignKey(Complaint, null=True, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['job', 'number'], name='unique_import_row')]
        indexes = [models.Index(fields=['job', 'state'])]

class SummaryRecord(models.Model):
    job = models.ForeignKey(ImportJob, on_delete=models.PROTECT, related_name='summaries')
    institution = models.ForeignKey(Institution, on_delete=models.PROTECT)
    bureau = models.ForeignKey(Bureau, on_delete=models.PROTECT)
    category = models.CharField(max_length=30)
    period = models.DateField()
    counts = models.JSONField()
    fingerprint = models.CharField(max_length=64, unique=True)

class StagedEmbedding(models.Model):
    case = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    revision = models.CharField(max_length=150)
    embedding = VectorField(dimensions=384)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['case', 'revision'], name='unique_staged_embedding')]

class ReportExport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    filters = models.JSONField(default=dict)
    state = models.CharField(max_length=20, default='pending')
    file = models.FileField(upload_to='reports/', blank=True)
    scope_hash = models.CharField(max_length=64, blank=True)
    error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ModelRelease(models.Model):
    revision = models.CharField(max_length=150, unique=True)
    path = models.CharField(max_length=300)
    threshold = models.FloatField()
    active = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['active'], condition=Q(active=True), name='one_active_model')]
