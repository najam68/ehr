from django.urls import path
from . import views
from .views import (
    PatientBundleView,
    FirstPatientBundleView,
    PatientResourceView,
    CapabilityStatementView,
)

urlpatterns = [
    path('ping', views.FHIRPing.as_view(), name='fhir-ping'),
    path('Organization/facility/<int:pk>', views.OrganizationFromFacility.as_view(), name='fhir-org-fac'),
    path('ClaimResponse/<int:pk>', views.ClaimResponseView.as_view(), name='fhir-claimresponse'),
    path('PractitionerRole/provider/<int:pk>', views.PractitionerRoleForProvider.as_view(), name='fhir-practitionerrole-bundle'),
    path('Observation/vitals/<int:pk>', views.VitalsObservationBundle.as_view(), name='fhir-vitals-bundle'),
    path('CoverageEligibilityResponse/<int:pk>', views.CoverageEligibilityResponseView.as_view(), name='fhir-cer'),
    path('Claim/<int:pk>', views.ClaimFromSuperbill.as_view(), name='fhir-claim'),
    path('DocumentReference/soap/<int:pk>', views.DocumentReferenceSoap.as_view(), name='fhir-docref-soap'),
    path('Encounter/<int:pk>', views.EncounterResource.as_view(), name='fhir-encounter'),
    path('Coverage/<int:pk>', views.CoverageResource.as_view(), name='fhir-coverage'),
    path('Organization/payer/<int:pk>', views.OrganizationFromPayer.as_view(), name='fhir-org-from-payer'),
    path('PractitionerRole/<int:pk>', views.PractitionerRoleResource.as_view(), name='fhir-practitionerrole'),
    path('Practitioner/<int:pk>', views.PractitionerResource.as_view(), name='fhir-practitioner'),
    path('Patient/<int:pk>/everything', views.PatientEverything.as_view(), name='fhir-patient-everything'),
    path('Patient/<int:pk>', views.PatientResource.as_view(), name='fhir-patient'),
    path('health', views.FHIRHealthView.as_view(), name='fhir-health'),
    path("patient/<int:pk>/bundle/", PatientBundleView.as_view(), name="fhir-patient-bundle"),
    path("patient/first/bundle/", FirstPatientBundleView.as_view(), name="fhir-first-patient-bundle"),
    path("Patient/<int:pk>", PatientResourceView.as_view(), name="fhir-patient-resource"),
    path("metadata", CapabilityStatementView.as_view(), name="fhir-metadata"),
]
