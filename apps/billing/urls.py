from django.urls import path
from . import views

from .views import new_superbill, superbill_detail, superbill_list

urlpatterns = [
    path('superbill/<int:superbill_id>/lines/new.json', views.lines_intake_json, name='billing-lines-intake-json'),
    path('claim-export/<int:superbill_id>.json', views.claim_export_json, name='billing-claim-export-json'),
    path('superbill/list.json', views.superbill_list_json, name='billing-superbill-list-json'),
    path('claimresponse/<int:superbill_id>/store.json', views.claimresponse_store_json, name='billing-claimresponse-store'),
    path('superbill-json/<int:superbill_id>', views.superbill_json, name='billing-superbill-json-alt'),
    path('superbill/<int:superbill_id>/json', views.superbill_json, name='billing-superbill-json'),
    path('claim/<int:superbill_id>/fhir.json', views.superbill_claim_fhir, name='billing-claim-fhir'),
    path("new/<int:encounter_id>/", new_superbill, name="billing-new-superbill"),
    path("<int:superbill_id>/", superbill_detail, name="billing-superbill-detail"),
    path("", superbill_list, name="billing-superbill-list"),
]
