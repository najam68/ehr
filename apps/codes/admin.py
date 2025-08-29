from django.contrib import admin
from .models import Code

@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):
    list_display = ("system","code","description","is_active")
    list_filter = ("system","is_active")
    search_fields = ("code","description")
