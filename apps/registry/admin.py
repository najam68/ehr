from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from .models import Provider, Facility

# Helper to safely pick fields that exist
def pick(model, *names):
    fields = {f.name for f in model._meta.get_fields()}
    return [n for n in names if n in fields]

# Provider admin (idempotent)
try:
    admin.site.unregister(Provider)
except NotRegistered:
    pass

prov_list = pick(Provider, 'id','last_name','first_name','npi','license_state','license_number','taxonomy_code') or ['id']
prov_search = pick(Provider, 'last_name','first_name','npi','license_number') or ['id']

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = tuple(prov_list)
    search_fields = tuple(prov_search)
    ordering = tuple(pick(Provider, 'last_name','first_name')) or ('id',)

# Facility admin (idempotent)
try:
    admin.site.unregister(Facility)
except NotRegistered:
    pass

fac_list = pick(Facility, 'id','name','type','npi_2') or ['id']
fac_search = pick(Facility, 'name','type') or ['id']

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = tuple(fac_list)
    search_fields = tuple(fac_search)
    ordering = tuple(pick(Facility, 'name')) or ('id',)
