from django.db import models
from django.core.validators import MinValueValidator
from apps.patients.models import Patient
from apps.chart.models import Encounter

class Superbill(models.Model):
    STATUS_CHOICES = [('DRAFT','Draft'),('SUBMITTED','Submitted')]
    encounter = models.OneToOneField(Encounter, on_delete=models.CASCADE, related_name='superbill')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='billing_superbills')
    icd_codes = models.JSONField(default=list, blank=True)
    cpt_codes = models.JSONField(default=list, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Superbill #{self.pk} for Encounter {self.encounter_id}"


class SuperbillLine(models.Model):
    """Itemized service line for a Superbill."""
    superbill = models.ForeignKey('Superbill', on_delete=models.CASCADE, related_name='billing_lines')
    # CPT / HCPCS
    code = models.CharField(max_length=10)  # e.g., 99213
    mod1 = models.CharField(max_length=2, blank=True, default="")
    mod2 = models.CharField(max_length=2, blank=True, default="")
    mod3 = models.CharField(max_length=2, blank=True, default="")
    mod4 = models.CharField(max_length=2, blank=True, default="")
    units = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Diagnosis pointers: indexes into the parent Superbill.icd_codes (1..n)
    dx_ptrs = models.JSONField(default=list, blank=True)  # e.g., [1,2]
    # Place of Service (2-digit CMS POS), free text ok
    pos = models.CharField(max_length=4, blank=True, default="")
    # Rendering provider (optional, if registry installed)
    rendering_provider = models.ForeignKey('registry.Provider', null=True, blank=True, on_delete=models.SET_NULL, related_name='rendered_lines')

    auth_number = models.CharField(max_length=40, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=['superbill','code'])]

    def __str__(self):
        return f"{self.superbill_id} {self.code} x{self.units} ${self.charge}"


class ClaimResponseStore(models.Model):
    superbill = models.OneToOneField(Superbill, on_delete=models.CASCADE, related_name='claim_response')
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"CR for SB {self.superbill_id}"
