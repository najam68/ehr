from django.db import models
from apps.patients.models import Patient, Coverage

class CoverageSnapshot(models.Model):
    MODE_CHOICES = [("SIMULATED","SIMULATED"),("MANUAL","MANUAL"),("REAL","REAL")]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    coverage = models.ForeignKey(Coverage, on_delete=models.CASCADE)
    dos = models.DateField()
    mode = models.CharField(max_length=12, choices=MODE_CHOICES, default="SIMULATED")
    payload = models.JSONField()  # normalized eligibility response
    created_at = models.DateTimeField(auto_now_add=True)
