from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id','start','end','status','reason')  # safe fields only
    date_hierarchy = 'start'
    autocomplete_fields = ('patient','provider','facility')
    exclude = ('encounter','superbill',)
