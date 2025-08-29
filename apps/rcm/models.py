from django.db import models

class PayerPlan(models.Model):
    # link to registry.Payer if present, but keep string fields to avoid hard coupling
    payer_label = models.CharField(max_length=120, blank=True, default="")  # e.g., "BCBS IL"
    payer_id_str = models.CharField(max_length=64, blank=True, default="")  # e.g., payer_id
    plan_id = models.CharField(max_length=64, blank=True, default="")
    name = models.CharField(max_length=160, blank=True, default="")
    network_type = models.CharField(max_length=32, blank=True, default="")  # PPO/HMO/etc.
    def __str__(self): return f"{self.payer_label} {self.name or self.plan_id}"

class Rule(models.Model):
    SEVERITY = (('BLOCK','BLOCK'),('WARN','WARN'))
    SCOPE = (('LINE','LINE'),('CLAIM','CLAIM'))
    active = models.BooleanField(default=True)
    name = models.CharField(max_length=160)
    scope = models.CharField(max_length=8, choices=SCOPE, default='LINE')

    # optional targeting
    payer_plan = models.ForeignKey(PayerPlan, null=True, blank=True, on_delete=models.SET_NULL, related_name='rules')
    payer_id_str = models.CharField(max_length=64, blank=True, default="")  # for quick targeting without plan
    cpt_code = models.CharField(max_length=10, blank=True, default="")
    pos_allowed = models.JSONField(default=list, blank=True)           # e.g., ["11","22"]
    modifiers_required = models.JSONField(default=list, blank=True)    # e.g., ["25"]
    dx_required_any = models.JSONField(default=list, blank=True)       # e.g., ["I10","E11.9"] any of these must be present
    dx_allowed = models.JSONField(default=list, blank=True)            # restrict to this set (optional)

    provider_taxonomy_allowed = models.JSONField(default=list, blank=True)
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    max_age = models.PositiveSmallIntegerField(null=True, blank=True)
    sex_allowed = models.JSONField(default=list, blank=True)           # ["M","F"]

    message = models.CharField(max_length=240, blank=True, default="")
    severity = models.CharField(max_length=8, choices=SEVERITY, default='WARN')
    effective_start = models.DateField(null=True, blank=True)
    effective_end = models.DateField(null=True, blank=True)

    def __str__(self): return f"{self.severity} {self.name}"
