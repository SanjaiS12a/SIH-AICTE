from django.contrib import admin
from django import forms
from .models import Institution, Bureau, Membership, Complaint, CaseAction, OverlapCandidate, Attachment, AuditEvent, Notification, ImportJob, ImportRow, SummaryRecord, ModelRelease, ReportExport, Escalation

admin.site.site_header = 'Coordination · Demo administration'
admin.site.register([Bureau, Membership])

class InstitutionAdminForm(forms.ModelForm):
    version = forms.IntegerField(min_value=1, initial=1, widget=forms.HiddenInput)
    reason = forms.CharField(max_length=4000, widget=forms.Textarea)

    class Meta:
        model = Institution
        fields = '__all__'

    def clean(self):
        data = super().clean()
        if self.instance.pk and not self.instance._state.adding:
            # Admin wraps POSTs in a transaction; hold this lock through save_model.
            current = Institution.objects.select_for_update().get(pk=self.instance.pk)
            if data.get('version') != current.version:
                raise forms.ValidationError('Institution changed. Reload before saving.')
        return data


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    form = InstitutionAdminForm
    list_display = ['name', 'permanent_id', 'region', 'version']
    search_fields = ['name', 'permanent_id']

    def get_readonly_fields(self, request, obj=None):
        return ['permanent_id'] if obj else []

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        from .institutions import PROFILE_FIELDS, save_profile
        saved = save_profile(request.user, {key: getattr(obj, key) for key in PROFILE_FIELDS},
                             institution_id=obj.pk if change else None,
                             expected_version=form.cleaned_data['version'] if change else None,
                             reason=form.cleaned_data['reason'])
        obj.__dict__.update(saved.__dict__)

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

for model in [Complaint, CaseAction, OverlapCandidate, Attachment, AuditEvent, Notification, ImportJob, ImportRow, SummaryRecord, ModelRelease, ReportExport, Escalation]:
    admin.site.register(model, ReadOnlyAdmin)
