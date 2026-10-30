from django.contrib import admin
from .models import Institution, Bureau, Membership, Complaint, CaseAction, OverlapCandidate, Attachment, AuditEvent, Notification, ImportJob, ImportRow, SummaryRecord, ModelRelease, ReportExport

admin.site.site_header = 'Coordination · Demo administration'
admin.site.register([Institution, Bureau, Membership])

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

for model in [Complaint, CaseAction, OverlapCandidate, Attachment, AuditEvent, Notification, ImportJob, ImportRow, SummaryRecord, ModelRelease, ReportExport]:
    admin.site.register(model, ReadOnlyAdmin)
