from django.urls import path
from . import views

urlpatterns = [
    path('list.json', views.list_specialties, name='specialties-list'),
    path('fields.json', views.fields_for_specialty, name='specialties-fields'),
]
