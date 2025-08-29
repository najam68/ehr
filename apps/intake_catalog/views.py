from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import Field
from apps.clinical_directory.models import Specialty

@api_view(["POST"])
def resolve(request):
    spec_slug = request.data.get("specialty")
    step = request.data.get("step")

    qs = Field.objects.filter(active=True)
    if spec_slug:
        try:
            spec = Specialty.objects.get(slug=spec_slug)
            qs = qs.filter(Q(specialties__isnull=True) | Q(specialties=spec)).distinct()
        except Specialty.DoesNotExist:
            qs = qs.filter(specialties__isnull=True)

    fields = list(qs.order_by("order", "id_stable"))
    if step:
        # Filter in Python to avoid DB JSON contains on SQLite
        fields = [f for f in fields if step in (f.intake_steps or [])]

    data = [{
        "id": f.id_stable,
        "label": f.label,
        "ui_type": f.ui_type,
        "required": f.required,
        "intake_steps": f.intake_steps,
        "fhir_map": f.fhir_map,
        "order": f.order,
    } for f in fields]
    return Response({"count": len(data), "fields": data})
