from django.urls import path
from .views import claims_list
urlpatterns = [
    path("", claims_list, name="claims-list"),
]
