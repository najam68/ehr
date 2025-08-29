
from django.contrib import admin
from .models import (
    Employer, Payer, Facility, Provider, ProviderPayerCredential,
    PatientProfile, EmergencyContact, Guarantor, Coverage, Authorization, Referral, Document
)

@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ("id","name","phone")
    search_fields = ("name","phone")

@admin.register(Payer)
class PayerAdmin(admin.ModelAdmin):
    list_display = ("id","name","payer_id","phone")
    search_fields = ("name","payer_id")

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ("id","name","type","npi_2")
    list_filter = ("type",)
    search_fields = ("name","npi_2","tax_id")

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("id","last_name","first_name","npi","specialty","license_state")
    search_fields = ("last_name","first_name","npi","taxonomy_code","license_number")
    list_filter = ("license_state","board_certified")

@admin.register(ProviderPayerCredential)
class ProviderPayerCredentialAdmin(admin.ModelAdmin):
    list_display = ("id","provider","payer","status","effective_date","end_date")
    list_filter = ("status", "payer")
    search_fields = ("provider__last_name","provider__first_name","payer__name","contract_id","fee_schedule_name")

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("id","patient","mrn","marital_status","employment_status","portal_enrolled")
    list_filter = ("marital_status","employment_status","portal_enrolled")
    search_fields = ("patient__last_name","patient__first_name","mrn","ssn")

@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("id","patient","name","relationship","priority","phone")
    list_filter = ("relationship",)
    search_fields = ("patient__last_name","patient__first_name","name")

@admin.register(Guarantor)
class GuarantorAdmin(admin.ModelAdmin):
    list_display = ("id","patient","name","relationship","phone")
    search_fields = ("patient__last_name","patient__first_name","name","ssn")

@admin.register(Coverage)
class CoverageAdmin(admin.ModelAdmin):
    list_display = ("id","patient","payer","member_id","is_primary","eligibility_status")
    list_filter = ("is_primary","eligibility_status","payer")
    search_fields = ("patient__last_name","patient__first_name","member_id","group_number")

@admin.register(Authorization)
class AuthorizationAdmin(admin.ModelAdmin):
    list_display = ("id","patient","procedure_code","authorized_units","used_units","start_date","end_date")
    list_filter = ("start_date","end_date")
    search_fields = ("patient__last_name","patient__first_name","procedure_code","auth_number")

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("id","patient","from_provider","to_provider","date","expires")
    list_filter = ("date","expires")
    search_fields = ("patient__last_name","patient__first_name","from_provider__last_name","to_provider__last_name")

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id","title","uploaded_by","uploaded_at","content_type","object_id")
    list_filter = ("content_type",)
    search_fields = ("title","notes","uploaded_by__username")
