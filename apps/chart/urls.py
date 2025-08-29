from django.urls import path
from . import views
from .views import new_encounter, encounter_detail, encounter_list
urlpatterns = [
    path('encounter/<int:encounter_id>/vitals/new.json', views.vitals_intake_json, name='chart-vitals-intake-json'),
    path("patient/<int:patient_id>/encounter/new/", new_encounter, name="chart-new-encounter"),
    path("encounter/<int:encounter_id>/", encounter_detail, name="chart-encounter-detail"),
    path("encounters/", encounter_list, name="chart-encounter-list"),
]
