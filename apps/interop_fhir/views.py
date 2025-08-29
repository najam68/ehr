from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import date
from apps.patients.models import Patient, Coverage

def patient_to_fhir(p: Patient) -> dict:
    addr = p.address or {}
    return {
        "resourceType": "Patient",
        "id": str(p.id),
        "name": [{"family": p.last_name, "given": [p.first_name]}],
        "telecom": (
            ([{"system":"phone","value":p.phone}] if p.phone else [])
            + ([{"system":"email","value":p.email}] if p.email else [])
        ),
        "birthDate": p.date_of_birth.isoformat(),
        "address": [{
            "line": [addr.get("line","")],
            "city": addr.get("city",""),
            "state": addr.get("state",""),
            "postalCode": addr.get("postal",""),
            "country": addr.get("country","US") or "US",
        }],
    }

def coverage_to_fhir(c: Coverage) -> dict:
    today = date.today()
    status_val = "active"
    if c.termination_date and c.termination_date < today:
        status_val = "cancelled"
    return {
        "resourceType": "Coverage",
        "id": str(c.id),
        "status": status_val,
        "beneficiary": {"reference": f"Patient/{c.patient_id}"},
        "subscriberId": c.member_id,
        "relationship": {"coding":[{"code": (c.relation_to_subscriber or "self")}]},
        "payor": [{"display": c.payer_name}],
        "period": {
            **({"start": c.effective_date.isoformat()} if c.effective_date else {}),
            **({"end": c.termination_date.isoformat()} if c.termination_date else {}),
        },
        "class": (
            [{"type":{"text":"group"}, "value": c.group_number}] if c.group_number else []
        ),
    }

@api_view(["GET"])
def patient_read(request, id: int):
    try:
        p = Patient.objects.get(pk=id)
        return Response(patient_to_fhir(p))
    except Patient.DoesNotExist:
        return Response({"issue":[{"severity":"error","diagnostics":"Patient not found"}]}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
def coverage_read(request, id: int):
    try:
        c = Coverage.objects.get(pk=id)
        return Response(coverage_to_fhir(c))
    except Coverage.DoesNotExist:
        return Response({"issue":[{"severity":"error","diagnostics":"Coverage not found"}]}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
def bundle_patient_coverages(request, patient_id: int):
    try:
        p = Patient.objects.get(pk=patient_id)
    except Patient.DoesNotExist:
        return Response({"issue":[{"severity":"error","diagnostics":"Patient not found"}]}, status=status.HTTP_404_NOT_FOUND)
    covs = Coverage.objects.filter(patient_id=p.id).order_by("id")
    entries = [{"resource": patient_to_fhir(p)}] + [{"resource": coverage_to_fhir(c)} for c in covs]
    return Response({"resourceType":"Bundle","type":"collection","entry": entries})
