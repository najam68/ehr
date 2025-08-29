from django.contrib import admin
from .models import Specialty, Subspecialty, FieldDefinition

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('id','name','slug')
    search_fields = ('name','slug')
    ordering = ('name',)

@admin.register(Subspecialty)
class SubspecialtyAdmin(admin.ModelAdmin):
    list_display = ('id','specialty','name','slug')
    search_fields = ('name','slug','specialty__name')
    list_filter = ('specialty',)
    ordering = ('specialty__name','name')

@admin.register(FieldDefinition)
class FieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ('id','label','key','input_type','required','group','order','is_active')
    list_filter = ('input_type','required','is_active','group','specialties')
    search_fields = ('label','key','help_text')
    filter_horizontal = ('specialties','subspecialties')
    ordering = ('group','order','label')
