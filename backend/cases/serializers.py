from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from .models import Institution, Bureau, Complaint, CaseAction, Attachment, Escalation

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'permanent_id', 'region', 'district']

class CaseSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    bureau = serializers.CharField(source='bureau.code', read_only=True)
    source_bureau = serializers.CharField(source='source_bureau.code', default=None, read_only=True)
    assigned_name = serializers.CharField(source='assigned_to.get_full_name', default='', read_only=True)
    overdue = serializers.SerializerMethodField()
    has_unresolved_escalation = serializers.SerializerMethodField()

    def get_has_unresolved_escalation(self, obj):
        if hasattr(obj, 'has_unresolved_escalation'):
            return obj.has_unresolved_escalation
        if hasattr(obj, 'pending_escalations'):
            return bool(obj.pending_escalations)
        return Escalation.objects.filter(case=obj, status='pending').exists()

    def get_overdue(self, obj):
        return obj.status != 'disposed' and obj.due_at < timezone.now()

    class Meta:
        model = Complaint
        fields = ['id', 'reference', 'institution', 'bureau', 'category', 'classification', 'next_action', 'next_action_date', 'summary', 'description',
                  'source_system', 'source_reference', 'source_status', 'source_bureau', 'source_last_seen_at', 'incident_date', 'status', 'received_at', 'due_at',
                  'disposed_at', 'assigned_to', 'assigned_name', 'matching_state', 'matching_error', 'matched_at',
                  'model_revision', 'version', 'overdue', 'created_at', 'matching_duration_ms', 'matching_queue_ms', 'has_unresolved_escalation']

class CreateCaseSerializer(serializers.Serializer):
    submission_id = serializers.UUIDField()
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all())
    bureau = serializers.SlugRelatedField(slug_field='code', queryset=Bureau.objects.all())
    source_system = serializers.CharField(max_length=40, default='manual')
    source_reference = serializers.CharField(max_length=100)
    category = serializers.ChoiceField(choices=Complaint.CATEGORIES)
    classification = serializers.ChoiceField(choices=Complaint.CLASSIFICATIONS, default='unclassified')
    summary = serializers.CharField(max_length=2000)
    description = serializers.CharField(max_length=10000)
    incident_date = serializers.DateField(required=False, allow_null=True)
    received_at = serializers.DateTimeField(default=timezone.now)

    def validate_summary(self, value):
        from .matching import tokenizer
        model_tokenizer = self.context.get('tokenizer') or tokenizer()
        if len(model_tokenizer.encode(value, add_special_tokens=True).ids) > 256:
            raise serializers.ValidationError('Keep the allegation summary within 256 model wordpieces. Put supporting detail in the full description.')
        return value

    def validate_received_at(self, value):
        if value > timezone.now() + timedelta(minutes=5):
            raise serializers.ValidationError('Receipt date cannot be in the future.')
        return value

class ActionSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=['note', 'status', 'transfer', 'assign', 'deadline', 'retry_matching', 'classification', 'next_action'])
    expected_version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=4000)
    status = serializers.ChoiceField(choices=Complaint.STATUSES, required=False)
    bureau = serializers.SlugRelatedField(slug_field='code', queryset=Bureau.objects.all(), required=False)
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True), required=False, allow_null=True)
    due_at = serializers.DateTimeField(required=False)
    classification = serializers.ChoiceField(choices=Complaint.CLASSIFICATIONS, required=False)
    next_action = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    next_action_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, data):
        required = {'status': 'status', 'transfer': 'bureau', 'assign': 'assigned_to', 'deadline': 'due_at',
                    'classification': 'classification', 'next_action': 'next_action'}
        key = required.get(data['kind'])
        if key and key not in data:
            raise serializers.ValidationError({key: 'This field is required for this action.'})
        if data['kind'] == 'next_action' and data.get('next_action_date') and not data['next_action']:
            raise serializers.ValidationError({'next_action': 'An expected action date requires a description.'})
        return data

class ActionReadSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source='actor.get_full_name')
    bureau_at_action = serializers.CharField(source='bureau_at_action.code', allow_null=True, read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context.get('restricted') and (instance.kind == 'overlap_review' or instance.kind.startswith('coordination_')):
            data.update(reason='Restricted coordination review recorded.', changes={})
        return data

    class Meta:
        model = CaseAction
        fields = ['id', 'kind', 'actor', 'reason', 'changes', 'created_at', 'bureau_at_action']

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'original_name', 'content_type', 'size', 'created_at']

class FilterSerializer(serializers.Serializer):
    import_id = serializers.UUIDField(required=False)
    q = serializers.CharField(max_length=200, required=False, allow_blank=True)
    institution = serializers.UUIDField(required=False)
    bureau = serializers.CharField(max_length=20, required=False, allow_blank=True)
    region = serializers.CharField(max_length=60, required=False, allow_blank=True)
    district = serializers.CharField(max_length=80, required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=[''] + [x[0] for x in Complaint.CATEGORIES], required=False)
    classification = serializers.ChoiceField(choices=[''] + [x[0] for x in Complaint.CLASSIFICATIONS], required=False)
    status = serializers.ChoiceField(choices=[''] + [x[0] for x in Complaint.STATUSES], required=False)
    overdue = serializers.BooleanField(required=False)
    pending = serializers.BooleanField(required=False)
    under_process = serializers.BooleanField(required=False)
    escalated = serializers.BooleanField(required=False)
    approaching = serializers.BooleanField(required=False)
    with_cases = serializers.BooleanField(required=False)
    closed = serializers.BooleanField(required=False)
    district_exact = serializers.BooleanField(required=False)
    age = serializers.CharField(max_length=10, required=False)
    locals()['from'] = serializers.DateField(required=False)
    to = serializers.DateField(required=False)
    disposed_from = serializers.DateField(required=False)
    disposed_to = serializers.DateField(required=False)

    def validate_age(self, value):
        if not value:
            return value
        cleaned = value.strip().replace(' ', '+')
        if cleaned in ('30', '30+'):
            return '30+'
        if cleaned in ('61', '61+'):
            return '61+'
        valid = ['0-7', '8-15', '16-30', '30+', '8-30', '31-60', '61+']
        if cleaned not in valid:
            raise serializers.ValidationError('Invalid age band.')
        return cleaned

    def validate(self, data):
        for start, end in [('from', 'to'), ('disposed_from', 'disposed_to')]:
            if data.get(start) and data.get(end) and data[start] > data[end]:
                raise serializers.ValidationError('The end date must not precede the start date.')
        return data

class ReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['same_incident', 'related_issue', 'unrelated'])
    reason = serializers.CharField(max_length=4000)
    expected_version = serializers.IntegerField(min_value=1)
