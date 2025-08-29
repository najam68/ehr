from django.contrib import admin
from .models import Encounter, SoapNote

class SoapInline(admin.StackedInline):
    model = SoapNote
    extra = 0

@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ("id","patient","started_at","status","reason")
    list_filter = ("status",)
    search_fields = ("id","patient__last_name","patient__first_name","reason")
    inlines = [SoapInline]

@admin.register(SoapNote)
class SoapNoteAdmin(admin.ModelAdmin):
    list_display = ("id","encounter","updated_at")
    search_fields = ("encounter__id",)
