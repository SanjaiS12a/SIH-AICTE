from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from .models import Institution, Bureau, Complaint, CaseAction, Attachment

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'permanent_id', 'region', 'district']

class CaseSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    bureau = serializers.CharField(source='bureau.code', read_only=True)
    assigned_name = serializers.CharField(source='assigned_to.get_full_name', default='', read_only=True)
    overdue = serializers.SerializerMethodField()

    def get_overdue(self, obj):
        return obj.status != 'disposed' and obj.due_at < timezone.now()

    class Meta:
        model = Complaint
        fields = ['id', 'reference', 'institution', 'bureau', 'category', 'summary', 'description',
                  'source_system', 'source_reference', 'incident_date', 'status', 'received_at', 'due_at',
                  'disposed_at', 'assigned_to', 'assigned_name', 'matching_state', 'matching_error', 'matched_at',
                  'model_revision', 'version', 'overdue', 'created_at', 'matching_duration_ms', 'matching_queue_ms']

class CreateCaseSerializer(serializers.Serializer):
    submission_id = serializers.UUIDField()
    institution = serializers.PrimaryKeyRelatedField(queryset=Institution.objects.all())
    bureau = serializers.SlugRelatedField(slug_field='code', queryset=Bureau.objects.all())
    source_system = serializers.CharField(max_length=40, default='manual')
    source_reference = serializers.CharField(max_length=100)
    category = serializers.ChoiceField(choices=Complaint.CATEGORIES)
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
    kind = serializers.ChoiceField(choices=['note', 'status', 'transfer', 'assign', 'deadline', 'retry_matching'])
    expected_version = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=4000)
    status = serializers.ChoiceField(choices=Complaint.STATUSES, required=False)
    bureau = serializers.SlugRelatedField(slug_field='code', queryset=Bureau.objects.all(), required=False)
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True), required=False, allow_null=True)
    due_at = serializers.DateTimeField(required=False)

    def validate(self, data):
        required = {'status': 'status', 'transfer': 'bureau', 'assign': 'assigned_to', 'deadline': 'due_at'}
        key = required.get(data['kind'])
        if key and key not in data:
            raise serializers.ValidationError({key: 'This field is required for this action.'})
        return data

class ActionReadSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source='actor.get_full_name')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context.get('restricted') and instance.kind == 'overlap_review':
            data.update(reason='Restricted coordination review recorded.', changes={})
        return data

    class Meta:
        model = CaseAction
        fields = ['id', 'kind', 'actor', 'reason', 'changes', 'created_at']

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
    category = serializers.ChoiceField(choices=[''] + [x[0] for x in Complaint.CATEGORIES], required=False)
    status = serializers.ChoiceField(choices=[''] + [x[0] for x in Complaint.STATUSES], required=False)
    overdue = serializers.BooleanField(required=False)
    pending = serializers.BooleanField(required=False)
    age = serializers.ChoiceField(choices=['0-7', '8-30', '31-60', '61+'], required=False)
    locals()['from'] = serializers.DateField(required=False)
    to = serializers.DateField(required=False)
    disposed_from = serializers.DateField(required=False)
    disposed_to = serializers.DateField(required=False)

    def validate(self, data):
        for start, end in [('from', 'to'), ('disposed_from', 'disposed_to')]:
            if data.get(start) and data.get(end) and data[start] > data[end]:
                raise serializers.ValidationError('The end date must not precede the start date.')
        return data

class ReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['same_incident', 'related_issue', 'unrelated'])
    reason = serializers.CharField(max_length=4000)
    expected_version = serializers.IntegerField(min_value=1)
