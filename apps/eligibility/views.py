from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import date
from .models import CoverageSnapshot
from .connectors import EligibilityRequest, stub_verify

@api_view(["POST"])
def check(request):
    """
    Simulated eligibility check; persists a CoverageSnapshot.
    Always returns JSON (even on error).
    """
    try:
        data = request.data or {}
        req = EligibilityRequest(
            payer_id=str(data.get("payer_id", "")),
            member_id=str(data.get("member_id", "")),
            patient_dob=str(data.get("patient_dob", "")),
            patient_name=str(data.get("patient_name", "")),
            provider_npi=str(data.get("provider_npi", "")),
            tin=str(data.get("tin", "")),
            dos=str(data.get("dos", "")) or str(date.today()),
            service_types=data.get("service_types") or ["30", "98"],
        )
        res = stub_verify(req)

        # Persist snapshot (expects existing patient_id/coverage_id)
        patient_id = int(data.get("patient_id"))
        coverage_id = int(data.get("coverage_id"))
        snap = CoverageSnapshot.objects.create(
            patient_id=patient_id,
            coverage_id=coverage_id,
            dos=req.dos,
            mode="SIMULATED",
            payload={
                "active": res.active,
                "network_status": res.network_status,
                "plan": res.plan,
                "benefits": res.benefits,
                "notes": res.notes,
                "raw": res.raw,
            },
        )
        return Response({"snapshot_id": snap.id, "payload": snap.payload}, status=status.HTTP_200_OK)

    except Exception as e:
        # Return a clear JSON error instead of an HTML debug page
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
