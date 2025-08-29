from django.db import models
from apps.patients.models import Patient

class Encounter(models.Model):
    STATUS_CHOICES = [('OPEN','Open'),('CLOSED','Closed')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='chart_encounters')
    started_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='OPEN')

    def __str__(self):
        return f"Encounter #{self.pk} - Patient {self.patient_id}"

class SoapNote(models.Model):
    encounter = models.OneToOneField(Encounter, on_delete=models.CASCADE, related_name='soap')
    subjective = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SOAP for Encounter {self.encounter_id}"


class VitalSign(models.Model):
    """One vital reading (use LOINC codes where possible)."""
    encounter = models.ForeignKey('Encounter', on_delete=models.CASCADE, related_name='chart_vitals')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='chart_vitals')
    code_system = models.CharField(max_length=64, default="http://loinc.org")
    code = models.CharField(max_length=32)  # e.g., 8867-4 HR; 9279-1 RR; 8310-5 Temp; 8462-4/8480-6 BP dia/sys
    display = models.CharField(max_length=128, blank=True, default="")
    value = models.FloatField()
    unit = models.CharField(max_length=32, default="")
    effective_time = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=['encounter','patient','code'])]

    def __str__(self):
        return f"{self.patient_id} {self.code} {self.value}{self.unit}"


class ConditionEntry(models.Model):
    """Problem list item."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='chart_conditions')
    encounter = models.ForeignKey('Encounter', on_delete=models.SET_NULL, null=True, blank=True, related_name='chart_conditions')
    code_system = models.CharField(max_length=64, default="http://snomed.info/sct")
    code = models.CharField(max_length=32, blank=True, default="")
    display = models.CharField(max_length=256, blank=True, default="")
    clinical_status = models.CharField(max_length=24, default="active")          # active|recurrence|remission|resolved
    verification_status = models.CharField(max_length=24, default="confirmed")   # unconfirmed|confirmed|refuted|entered-in-error
    onset_date = models.DateField(null=True, blank=True)
    abatement_date = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=['patient','clinical_status'])]

    def __str__(self):
        return f"{self.patient_id} {self.display or self.code}"


class AllergyEntry(models.Model):
    """Allergies/intolerances (simplified)."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='chart_allergies')
    substance_system = models.CharField(max_length=64, default="http://snomed.info/sct")
    substance_code = models.CharField(max_length=32, blank=True, default="")
    substance_display = models.CharField(max_length=256, blank=True, default="")
    status = models.CharField(max_length=24, default="active")   # active|inactive|resolved
    severity = models.CharField(max_length=16, default="", blank=True)  # mild|moderate|severe (optional)
    reaction_text = models.TextField(blank=True, default="")
    note = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=['patient','status'])]

    def __str__(self):
        return f"{self.patient_id} {self.substance_display or self.substance_code}"
