from django.urls import path
from . import views
urlpatterns = [
    path('rules/check/superbill/<int:superbill_id>.json', views.rules_check_superbill, name='rcm-rules-check-superbill'),
]
