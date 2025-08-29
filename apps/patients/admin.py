from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from .models import Patient

# Unregister if it was already registered in a previous pass
try:
    admin.site.unregister(Patient)
except NotRegistered:
    pass

# Build dynamic picks so we only include fields that actually exist on your Patient
P_FIELDS = {f.name for f in Patient._meta.get_fields()}
def pick(*names):
    return [n for n in names if n in P_FIELDS]

IDENTITY   = pick('first_name','middle_name','last_name','dob','gender','ssn')
CONTACT    = pick('phone','phone_alt','email')
ADDRESS    = pick('address_line1','address_line2','city','state','postal_code','country')
DEMOS      = pick('race','ethnicity','language','marital_status','preferred_contact_method')
EMPLOYER   = pick('employer_name','occupation')
GUARANTOR  = pick('guarantor_name','guarantor_relationship','guarantor_phone')
CONSENTS   = pick('portal_enrolled','consent_to_treat','assignment_of_benefits','hipaa_privacy_ack','consent_ack_at')
TS_READONLY= pick('created_at','updated_at')

# Safe list/search for changelist
LIST_COLS  = (pick('id','last_name','first_name','dob','gender','email','phone') or ['id'])
SEARCH_COLS= (pick('last_name','first_name','email','phone') or ['id'])

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    # clean list
    list_display  = tuple(LIST_COLS)
    search_fields = tuple(SEARCH_COLS)
    ordering      = tuple(pick('last_name','first_name')) or ('id',)

    # explicit, pro-level form layout (only fields we intend to show)
    fieldsets = (
        ('Identity', {'fields': tuple(IDENTITY)}),
        ('Contact', {'fields': tuple(CONTACT)}),
        ('Address', {'fields': tuple(ADDRESS)}),
        ('Demographics', {'fields': tuple(DEMOS)}),
        ('Employment', {'fields': tuple(EMPLOYER)}),
        ('Guarantor', {'fields': tuple(GUARANTOR)}),
        ('Consents / Portal', {'fields': tuple(CONSENTS)}),
        (None, {'fields': tuple(TS_READONLY)}),
    )

    # make system timestamps read-only
    readonly_fields = tuple(TS_READONLY)
