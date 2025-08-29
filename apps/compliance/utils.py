from .models import DisclosureLog, SecurityEvent

# Placeholder: call this wherever PHI leaves the system (e.g., export, API client)
def log_disclosure(patient_id:int, purpose:str, recipient:str, minimum_necessary:bool=True, meta:dict|None=None):
    try:
        DisclosureLog.objects.create(
            patient_id=patient_id, purpose=purpose, recipient=recipient,
            minimum_necessary=minimum_necessary, meta=meta or {}
        )
    except Exception:  # never break prod flow due to logging
        pass

# Placeholder: security events (auth failures, policy toggles, breach suspects)
def log_security_event(user, event_type:str, severity:str='info', message:str='', meta:dict|None=None):
    try:
        SecurityEvent.objects.create(
            who=user if getattr(user, 'is_authenticated', False) else None,
            event_type=event_type, severity=severity, message=message, meta=meta or {}
        )
    except Exception:
        pass

# Future swap: PHI field encryption wrappers (currently no-op)
def encrypt(value:str) -> str: return value
def decrypt(value:str) -> str: return value


from functools import wraps
from django.http import JsonResponse
from django.conf import settings

# feature flags / placeholders
def _hipaa_mode(): return bool(getattr(settings, 'HIPAA_MODE', False))
def _roles_for(user):
    try:
        return set(user.groups.values_list('name', flat=True))
    except Exception:
        return set()

def require_role(*roles):
    """Allow only if user in any of the named Django Groups (Biller, Clinician, FrontDesk, Admin...). 
       NO-OP if HIPAA_MODE=False (returns through)."""
    roles = {r for r in roles if r}
    def deco(fn):
        @wraps(fn)
        def _w(request, *a, **kw):
            if not _hipaa_mode():
                return fn(request, *a, **kw)
            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                return JsonResponse({'ok': False, 'error': 'auth-required'}, status=401)
            if not roles or _roles_for(request.user) & roles:
                return fn(request, *a, **kw)
            # log as security event
            from .utils import log_security_event
            log_security_event(request.user, 'rbac-deny', 'warn', f'roles={list(roles)}', 
                               {'route': request.path, 'roles': list(_roles_for(request.user))})
            return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)
        return _w
    return deco

def min_necessary(*allowed_purposes):
    """Gate by PHI purpose (treatment/payment/operations/patient-request/law/etc.). 
       NO-OP if HIPAA_MODE=False."""
    allowed = {p.lower() for p in allowed_purposes if p}
    def deco(fn):
        @wraps(fn)
        def _w(request, *a, **kw):
            if not _hipaa_mode():
                return fn(request, *a, **kw)
            if not allowed:
                return fn(request, *a, **kw)
            if getattr(request, 'phi_purpose', '') in allowed:
                return fn(request, *a, **kw)
            from .utils import log_security_event
            log_security_event(getattr(request,'user',None), 'purpose-deny', 'warn', f'need={list(allowed)} have={getattr(request,"phi_purpose","")}',
                               {'route': request.path})
            return JsonResponse({'ok': False, 'error': 'purpose-forbidden'}, status=403)
        return _w
    return deco
