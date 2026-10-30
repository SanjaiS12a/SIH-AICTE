import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
from pgvector.django import VectorField

class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    permanent_id = models.CharField(max_length=40, unique=True)
    region = models.CharField(max_length=60)
    district = models.CharField(max_length=80)

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
        constraints = [models.UniqueConstraint(fields=['source_system', 'source_reference'], name='unique_source_reference')]
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']

class OverlapCandidate(models.Model):
    left = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name='left_overlaps')
    right = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name='right_overlaps')
    score = models.FloatField()
    evidence = models.JSONField(default=dict)
    model_revision = models.CharField(max_length=150)
    decision = models.CharField(max_length=24, default='pending', choices=[(x, x) for x in ['pending', 'same_incident', 'related_issue', 'unrelated']])
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    reason = models.TextField(blank=True, max_length=4000)
    reviewed_at = models.DateTimeField(null=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['left', 'right'], name='unique_ordered_pair'),
                       models.CheckConstraint(condition=Q(left__lt=models.F('right')), name='ordered_pair')]
        ordering = ['-created_at', '-id']

class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Complaint, on_delete=models.PROTECT, related_name='attachments')
    file = models.FileField(upload_to='evidence/')
    original_name = models.CharField(max_length=180)
    content_type = models.CharField(max_length=80)
    size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    case = models.ForeignKey(Complaint, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20)
    deadline = models.DateTimeField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'case', 'kind', 'deadline'], name='unique_reminder')]
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
