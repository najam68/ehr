from django.db import models

class Provenance(models.Model):
    source_system = models.CharField(max_length=120, blank=True)  # e.g., OpenEMR, VendorX
    file_name = models.CharField(max_length=200)
    file_hash = models.CharField(max_length=64)
    format = models.CharField(max_length=40)  # CSV, CCDA, FHIR
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
