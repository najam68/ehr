from django.contrib import admin
from .models import Patient
from .forms import PatientForm

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    form = PatientForm
    list_display = ("id","last_name","first_name","dob")
    search_fields = ("id","last_name","first_name","email","phone")
