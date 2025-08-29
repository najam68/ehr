from django.contrib import admin
from . import views

from django.urls import path, include
from apps.patients import views as patient_views
from .views import home, fhir_demo_view, quick_patient_new

urlpatterns = [
    path('specialties/', include('apps.specialties.urls')),

    path('patients/<int:patient_id>/edit/', patient_views.patient_registration_edit, name='patient-registration-edit'),
    path('patients/register/', patient_views.patient_registration_new, name='patient-registration-new'),
    path('intake/<int:patient_id>/edit/', patient_views.patient_intake_edit, name='patient-intake-edit'),
    path('intake/new/', patient_views.patient_intake_new, name='patient-intake-new'),
    path('rcm/', include('apps.rcm.urls')),

    path('compliance/', include('apps.compliance.urls')),

    path('quick/new-encounter/', views.quick_new_encounter, name='quick-new-encounter'),
    path('', home, name='home'),                           # root -> dashboard
    path('dashboard/fhir-demo', fhir_demo_view, name='dashboard-fhir-demo'),
    path('patients/quick_new/', quick_patient_new, name='patients-quick-new'),
    path('registry/', include('apps.registry.urls')),

    path('codes/', include('apps.codes.urls')),

    #path('quick/new-encounter/', views.quick_new_encounter, name='quick-new-encounter'),
    path('accounts/', include('django.contrib.auth.urls')),

    path('billing/', include('apps.billing.urls')),
    path('chart/', include('apps.chart.urls')),
    path('fhir/', include('apps.fhir_api.urls')),

    path('claims/', include('apps.claims.urls')),
    path('patients/', include('apps.patients.urls')),
    path("admin/", admin.site.urls),
    
]

# Optional app urls (import if available)
try:
    import apps.patients.urls  # type: ignore
    urlpatterns += [path("patients/", include("apps.patients.urls"))]
except Exception:
    pass

try:
    import apps.claims.urls  # type: ignore
    urlpatterns += [path("claims/", include("apps.claims.urls"))]
except Exception:
    pass

try:
    import apps.api.urls  # type: ignore
    urlpatterns += [path("api/", include("apps.api.urls"))]
except Exception:
    pass

# FHIR routes (if present)
try:
    import apps.fhir_api.urls  # type: ignore
    urlpatterns += [path("fhir/", include("apps.fhir_api.urls"))]
except Exception:
    pass
