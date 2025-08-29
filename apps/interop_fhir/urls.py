from django.urls import path
from .views import patient_read, coverage_read, bundle_patient_coverages

urlpatterns = [
    path("Patient/<int:id>", patient_read, name="fhir-patient-read"),
    path("Coverage/<int:id>", coverage_read, name="fhir-coverage-read"),
    path("Bundle/PatientCoverages/<int:patient_id>", bundle_patient_coverages, name="fhir-bundle-patient-coverages"),
]
