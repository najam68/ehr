from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class ConsentRecord(models.Model):
    patient_id = models.PositiveIntegerField()
    type = models.CharField(max_length=64)  # e.g., 'treatment', 'privacy', 'research'
    given = models.BooleanField(default=True)
    effective_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    def __str__(self): return f"{self.type} for patient {self.patient_id}"

class DisclosureLog(models.Model):
    patient_id = models.PositiveIntegerField()
    purpose = models.CharField(max_length=128)  # 'treatment','payment','operations','law','patient-request',etc.
    recipient = models.CharField(max_length=256)  # org/person
    when = models.DateTimeField(auto_now_add=True)
    minimum_necessary = models.BooleanField(default=True)
    meta = models.JSONField(default=dict, blank=True)  # what fields, request_id, ip, UA
    def __str__(self): return f"Disclosure p{self.patient_id} -> {self.recipient}"

class SecurityEvent(models.Model):
    severity = models.CharField(max_length=16, default='info')  # info|warn|high|critical
    event_type = models.CharField(max_length=128)               # 'login-failure','policy-change','phi-export','breach-suspect'
    message = models.TextField(blank=True, default='')
    who = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    when = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)
    def __str__(self): return f"{self.when:%Y-%m-%d %H:%M} {self.severity} {self.event_type}"

class RetentionRule(models.Model):
    category = models.CharField(max_length=64)   # 'ehr-note','lab-result','billing','audit'
    days = models.PositiveIntegerField(default=365*7)  # placeholder; not enforced yet
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    def __str__(self): return f"{self.category} -> {self.days}d"


class ExportJob(models.Model):
    STATUS = (('QUEUED','QUEUED'),('PROCESSING','PROCESSING'),('COMPLETED','COMPLETED'),('FAILED','FAILED'))
    scope = models.CharField(max_length=64)         # 'patient-chart','billing','full-phi', etc.
    patient_id = models.PositiveIntegerField(null=True, blank=True)
    requested_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='export_jobs')
    status = models.CharField(max_length=16, choices=STATUS, default='QUEUED')
    location = models.CharField(max_length=512, blank=True, default='')  # URL or storage path placeholder
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    def __str__(self): return f"{self.scope} job #{self.id} {self.status}"
