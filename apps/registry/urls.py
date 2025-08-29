from django.urls import path
from . import views

from .views import (
    patient_registry_summary,
    edit_patient_profile,
    new_coverage,
    edit_coverage,
    new_emergency_contact,
)

urlpatterns = [
    path('coverage/<int:pk>/eligibility/check', views.coverage_check_and_back, name='registry-eligibility-check'),
    path('audit/recent.json', views.audit_recent_json, name='registry-audit-recent-json'),
    path('provider/<int:provider_id>/facility/unlink.json', views.provider_facility_unlink_json, name='registry-provider-facility-unlink-json'),
    path('provider/<int:provider_id>/facility/link.json', views.provider_facility_link_json, name='registry-provider-facility-link-json'),
    path('facility/list.json', views.facility_list_json, name='registry-facility-list-json'),
    path('coverage/list.json', views.coverage_list_json, name='registry-coverage-list-json'),
    path('provider/<int:provider_id>/payers.json', views.provider_payers_json, name='registry-provider-payers-json'),
    path('provider/<int:provider_id>/dea.json', views.provider_dea_json, name='registry-provider-dea-json'),
    path('provider/<int:provider_id>/licenses.json', views.provider_licenses_json, name='registry-provider-licenses-json'),
    path('coverage/<int:pk>/eligibility/check.json', views.coverage_check_json, name='registry-eligibility-check-json'),
    path('provider/<int:provider_id>/credentialing.json', views.provider_credentialing_json, name='registry-provider-credentialing-json'),
    path('payers/search_json/', views.payers_search_json, name='registry-payers-search'),
    path('credentialing/expiring/', views.credentialing_expiring, name='registry-credentialing-expiring'),
    path('credential/<int:credential_id>/edit/', views.edit_provider_credential, name='registry-edit-provider-credential'),
    path('provider/<int:provider_id>/credential/new/', views.new_provider_credential, name='registry-new-provider-credential'),
    path('provider/<int:provider_id>/', views.provider_detail, name='registry-provider'),
    path('providers/', views.providers_list, name='registry-providers'),
    path("patient/<int:patient_id>/", patient_registry_summary, name="registry-patient-summary"),
    path("patient/<int:patient_id>/profile/edit/", edit_patient_profile, name="registry-edit-profile"),
    path("patient/<int:patient_id>/coverage/new/", new_coverage, name="registry-new-coverage"),
    path("coverage/<int:coverage_id>/edit/", edit_coverage, name="registry-edit-coverage"),
    path("patient/<int:patient_id>/contact/new/", new_emergency_contact, name="registry-new-contact"),
]
