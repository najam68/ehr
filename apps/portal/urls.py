# apps/portal/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Project urls.py provides the "portal/" prefix.
    # So this should be the empty string to map /portal/ -> views.dashboard
    path("", views.dashboard, name="portal_dashboard"),
]
