from django.contrib import admin
from .models import Denial, DenialStatusHistory

class DenialStatusHistoryInline(admin.TabularInline):
    model = DenialStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ("from_status", "to_status", "note", "created_at")
    fields = ("created_at", "from_status", "to_status", "note")
    ordering = ("-created_at",)

@admin.register(Denial)
class DenialAdmin(admin.ModelAdmin):
    list_display = ("id", "claim", "status")
    list_filter = ("status",)
    search_fields = ("id", "claim__id", "status")
    ordering = ("-id",)
    inlines = [DenialStatusHistoryInline]

@admin.register(DenialStatusHistory)
class DenialStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("denial", "from_status", "to_status", "created_at")
    list_filter = ("to_status", "created_at")
    search_fields = ("denial__id", "from_status", "to_status", "note")
    ordering = ("-created_at",)
    readonly_fields = ("denial", "from_status", "to_status", "note", "created_at")
