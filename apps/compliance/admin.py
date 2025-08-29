from django.contrib import admin
from .models import ConsentRecord, DisclosureLog, SecurityEvent, RetentionRule

@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ('id','patient_id','type','given','effective_at','expires_at')
    search_fields = ('patient_id','type')

@admin.register(DisclosureLog)
class DisclosureLogAdmin(admin.ModelAdmin):
    list_display = ('id','patient_id','purpose','recipient','when','minimum_necessary')
    search_fields = ('patient_id','recipient','purpose')
    list_filter = ('purpose','minimum_necessary')

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('id','severity','event_type','who','when')
    list_filter = ('severity','event_type')
    search_fields = ('event_type','message','who__username')

@admin.register(RetentionRule)
class RetentionRuleAdmin(admin.ModelAdmin):
    list_display = ('id','category','days','active')
    list_filter = ('category','active')


from .models import ExportJob
@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ('id','scope','patient_id','status','requested_by','requested_at','completed_at')
    list_filter = ('status','scope')
    search_fields = ('id','patient_id','requested_by__username')
