from django.urls import path
from . import api, imports, exports, institutions

urlpatterns = [
    path('institution-registry', institutions.registry),
    path('institutions/<uuid:institution_id>', institutions.detail),
    path('institutions/<uuid:institution_id>/cases', institutions.institution_cases),
    path('institutions/<uuid:institution_id>/history', institutions.history),
    path('imports', imports.imports), path('imports/templates/<str:kind>', imports.template),
    path('imports/<uuid:job_id>', imports.import_detail), path('imports/<uuid:job_id>/errors.csv', imports.import_errors),
    path('imports/<uuid:job_id>/report', imports.import_report), path('imports/<uuid:job_id>/report.csv', imports.import_summary_csv),
    path('exports', exports.exports), path('exports/<uuid:export_id>', exports.export_detail),
    path('exports/<uuid:export_id>/download', exports.export_download),
    path('session', api.session), path('options', api.options), path('institutions', api.institutions),
    path('cases', api.cases), path('cases/<uuid:case_id>', api.case_detail),
    path('cases/<uuid:case_id>/actions', api.actions), path('cases/<uuid:case_id>/attachments', api.upload),
    path('attachments/<uuid:attachment_id>', api.download), path('overlaps', api.overlaps),
    path('overlaps/<int:overlap_id>/review', api.review), path('dashboard', api.dashboard),
    path('reports.csv', api.report), path('notifications', api.notifications),
]
