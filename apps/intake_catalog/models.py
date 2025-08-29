from django.db import models
from apps.clinical_directory.models import Specialty

class Field(models.Model):
    id_stable = models.CharField(max_length=120, primary_key=True)
    label = models.CharField(max_length=160)
    help_text = models.TextField(blank=True)
    ui_type = models.CharField(max_length=40, default="text")  # text, number, date, code, list, score, complex
    intake_steps = models.JSONField(default=list)  # ["schedule","previsit","checkin","rooming","clinical"]
    required = models.CharField(max_length=1, default="N")  # Y/N/C
    privacy_flags = models.JSONField(default=list, blank=True)  # ["Part2","Psych"]
    fhir_map = models.CharField(max_length=200, blank=True)
    value_set = models.JSONField(default=dict, blank=True)
    constraints = models.JSONField(default=dict, blank=True)  # min/max, regex, dependencies
    specialties = models.ManyToManyField(Specialty, blank=True)  # empty = GLOBAL
    order = models.IntegerField(default=1000)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.id_stable
