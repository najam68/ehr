from django.db import models

class Code(models.Model):
    SYSTEMS = [('ICD10','ICD-10-CM'), ('CPT','CPT')]
    system = models.CharField(max_length=16, choices=SYSTEMS)
    code = models.CharField(max_length=16)
    description = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('system','code')
        indexes = [
            models.Index(fields=['system','code']),
            models.Index(fields=['description']),
        ]

    def __str__(self):
        return f"{self.system}:{self.code} {self.description}"
