from django.urls import path
from .views import resolve

urlpatterns = [
    path("resolve", resolve, name="intake-resolve"),
]
