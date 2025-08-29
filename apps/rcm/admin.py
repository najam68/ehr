from django.contrib import admin
from .models import Rule, PayerPlan

@admin.register(PayerPlan)
class PayerPlanAdmin(admin.ModelAdmin):
    list_display = ('id','payer_label','name','plan_id','network_type')

@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('id','active','severity','scope','name','cpt_code','payer_id_str','payer_plan')
    list_filter = ('active','severity','scope')
    search_fields = ('name','cpt_code','payer_id_str','message')
