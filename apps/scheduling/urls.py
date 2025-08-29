from django.urls import path
from . import views
urlpatterns = [
    path('appointment/<int:appt_id>/summary.json', views.appointment_summary_json, name='sched-appointment-summary-json'),
    path('appointment/<int:appt_id>/create-superbill.json', views.appointment_create_superbill_json, name='sched-appointment-create-superbill-json'),
    path('appointment/<int:appt_id>/start.json', views.appointment_start_json, name='sched-appointment-start-json'),
    path('appointment/<int:appt_id>/checkin.json', views.appointment_checkin_json, name='sched-appointment-checkin-json'),
    path('appointments.json', views.appointments_day_json, name='sched-appointments-day-json'),
    path('appointment/new.json', views.appointment_new_json, name='sched-appointment-new-json'),
    path('appointment/<int:appt_id>/update.json', views.appointment_update_json, name='sched-appointment-update-json'),
]
