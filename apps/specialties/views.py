from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Specialty, Subspecialty, FieldDefinition

@require_GET
def list_specialties(request):
    specs = list(Specialty.objects.order_by('name').values('id','name','slug'))
    subs = list(Subspecialty.objects.select_related('specialty').order_by('specialty__name','name')
                .values('id','name','slug','specialty_id'))
    return JsonResponse({"ok": True, "specialties": specs, "subspecialties": subs})

@require_GET
def fields_for_specialty(request):
    sid = request.GET.get('specialty_id') or ''
    ssid = request.GET.get('subspecialty_id') or ''
    qs = FieldDefinition.objects.filter(is_active=True)

    if sid.isdigit():
        qs = qs.filter(models.Q(specialties__id=int(sid)) | models.Q(specialties__isnull=True))
    if ssid.isdigit():
        qs = qs.filter(models.Q(subspecialties__id=int(ssid)) | models.Q(subspecialties__isnull=True))

    # distinct to avoid dupes when both M2Ms match
    qs = qs.distinct().order_by('group','order','label')

    items = []
    for f in qs:
        items.append({
            "key": f.key, "label": f.label, "type": f.input_type,
            "required": f.required, "group": f.group, "order": f.order,
            "help": f.help_text, "choices": f.choices_json,
        })
    return JsonResponse({"ok": True, "count": len(items), "items": items})
