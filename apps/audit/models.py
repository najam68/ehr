from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AuditEvent(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_events')
    action = models.CharField(max_length=100)
    model = models.CharField(max_length=120, blank=True, default='')
    object_id = models.CharField(max_length=64, blank=True, default='')
    meta = models.JSONField(default=dict, blank=True)
    when = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['model','object_id','when'])]
        ordering = ['-when']

    def __str__(self):
        return f"{self.when:%Y-%m-%d %H:%M} {self.action} {self.model}#{self.object_id}"
