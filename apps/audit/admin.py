from django.contrib import admin
from .models import AuditEvent

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('when','user','action','model','object_id')
    search_fields = ('action','model','object_id','user__username')
    list_filter = ('action',)
