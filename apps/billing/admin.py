# apps/billing/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Superbill, SuperbillLine

class SuperbillLineInline(admin.TabularInline):
    model = SuperbillLine
    extra = 1
    fields = ("code","mod1","mod2","mod3","mod4","units","charge","pos","dx_ptrs","auth_number","notes")

@admin.register(Superbill)
class SuperbillAdmin(admin.ModelAdmin):
    list_display = ("id","patient","status","total","claim_link")
    search_fields = ("id","patient__last_name","patient__first_name")
    inlines = [SuperbillLineInline]

    def claim_link(self, obj):
        return format_html(
            "<a href='/fhir/Claim/{}/' target='_blank' rel='noopener'>FHIR Claim</a>",
            obj.id
        )
    claim_link.short_description = "Export"

@admin.register(SuperbillLine)
class SuperbillLineAdmin(admin.ModelAdmin):
    list_display = ("id","superbill","code","units","charge","pos")
    list_filter = ("pos",)
    search_fields = ("superbill__id","code","auth_number","notes")
