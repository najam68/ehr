from django.urls import path
from .views import patients_list
urlpatterns = [
    path("", patients_list, name="patients-list"),
]
