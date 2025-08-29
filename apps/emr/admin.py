from django.contrib import admin
from .models import Encounter, ProgressNote, Vital, Problem, Medication, Allergy, LabOrder, LabResult

admin.site.register(Encounter)
admin.site.register(ProgressNote)
admin.site.register(Vital)
admin.site.register(Problem)
admin.site.register(Medication)
admin.site.register(Allergy)
admin.site.register(LabOrder)
admin.site.register(LabResult)
