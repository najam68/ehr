from django.urls import path
from . import views

urlpatterns = [
    path("p/<int:patient_id>/", views.chart, name="emr-chart"),
    path("p/<int:patient_id>/encounters/new", views.new_encounter, name="emr-new-encounter"),
    path("encounters/<int:enc_id>/", views.encounter_detail, name="emr-encounter"),
]
