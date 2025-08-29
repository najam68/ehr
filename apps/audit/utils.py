from .models import AuditEvent

def log_event(user, action, model, object_id, meta=None):
    try:
        AuditEvent.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            action=action, model=model, object_id=str(object_id or ''), meta=meta or {}
        )
    except Exception:
        # never break prod flow due to audit write
        pass
