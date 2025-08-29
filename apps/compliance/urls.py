from django.urls import path
from . import views

urlpatterns = [
    path('export/complete.json', views.export_complete, name='compliance-export-complete'),
    path('export/start.json', views.export_start, name='compliance-export-start'),
    path('health', views.health, name='compliance-health'),
    path('disclosures/recent.json', views.disclosures_recent, name='compliance-disclosures-recent'),
    path('disclosures/log.json', views.disclosures_log, name='compliance-disclosures-log'),
    path('security/recent.json', views.security_recent, name='compliance-security-recent'),
]
