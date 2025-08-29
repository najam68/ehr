from django.db import models
from apps.patients.models import Patient
from apps.registry.models import Provider, Facility
from django.utils import timezone 


class Appointment(models.Model):
    STATUS = (
        ('SCHEDULED','SCHEDULED'),
        ('CHECKIN','CHECKIN'),
        ('INROOM','INROOM'),
        ('COMPLETED','COMPLETED'),
        ('CANCELED','CANCELED'),
        ('NOSHOW','NOSHOW'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, related_name='appointments')
    facility = models.ForeignKey(Facility,null=True, blank=True, on_delete=models.PROTECT,related_name='appointments')
    start = models.DateTimeField()
    end = models.DateTimeField()
    status = models.CharField(max_length=12, choices=STATUS, default='SCHEDULED')
    reason = models.CharField(max_length=160, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    # links into EHR/Billing (nullable)
    encounter = models.ForeignKey('chart.Encounter', null=True, blank=True, on_delete=models.SET_NULL, related_name='appointments')
    superbill = models.ForeignKey('billing.Superbill', null=True, blank=True, on_delete=models.SET_NULL, related_name='appointments')
    created_at = models.DateTimeField(default=timezone.now, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    class Meta:
        indexes = [models.Index(fields=['start','provider','facility'])]

    def __str__(self):
        return f"{self.start:%Y-%m-%d %H:%M} p{self.patient_id} with prov {self.provider_id}"
