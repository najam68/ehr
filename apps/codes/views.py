from django.http import JsonResponse
from django.db.models import Q
from .models import Code

def _serialize(qs, limit=15):
    data = [{"system": c.system, "code": c.code, "description": c.description} for c in qs[:limit]]
    return JsonResponse({"results": data})

def search_codes(request):
    q = (request.GET.get("q") or "").strip()
    system = (request.GET.get("system") or "").strip().upper()
    qs = Code.objects.filter(is_active=True)
    if system in {"ICD10","CPT"}:
        qs = qs.filter(system=system)
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(description__icontains=q))
    else:
        qs = qs.order_by("code")
    return _serialize(qs)

def most_common(request):
    system = (request.GET.get("system") or "").strip().upper()
    qs = Code.objects.filter(is_active=True)
    if system in {"ICD10","CPT"}:
        qs = qs.filter(system=system)
    qs = qs.order_by("code")
    return _serialize(qs)
