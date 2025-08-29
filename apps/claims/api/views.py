import csv
from io import StringIO
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from apps.claims.models import Denial, DenialStatusHistory, Claim
from apps.claims.scrubber import run_scrubber

from .serializers import DenialSerializer

class DenialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    - GET /api/claims/denials/
    - GET /api/claims/denials/{id}/
    - POST /api/claims/denials/{id}/status/  body: {"status":"WORKING","note":"..."}
    - GET /api/claims/denials/export/?format=csv
    """
    queryset = Denial.objects.select_related("claim").all().order_by("-created_at")
    serializer_class = DenialSerializer

    @action(detail=True, methods=["post"], url_path="status")
    def update_status(self, request, pk=None):
        denial = self.get_object()
        new_status = (request.data or {}).get("status")
        note = (request.data or {}).get("note", "")

        valid = {s for s, _ in Denial.STATUS}
        if new_status not in valid:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        old_status = denial.status
        denial.status = new_status
        denial.save(update_fields=["status"])
        DenialStatusHistory.objects.create(
            denial=denial, from_status=old_status or "", to_status=new_status, note=note
        )
        return Response(DenialSerializer(denial).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        fmt = (request.query_params.get("format") or "csv").lower()
        qs = self.get_queryset()
        if fmt != "csv":
            return Response({"detail": "Unsupported format"}, status=400)

        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(["id", "claim_id", "status", "reason", "created_at"])
        for d in qs:
            w.writerow([d.id, getattr(d, "claim_id", getattr(d.claim, "id", "")), d.status, d.reason, d.created_at.isoformat()])
        resp = HttpResponse(buf.getvalue(), content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="denials_export.csv"'
        return resp

@api_view(["GET"])
def workqueue(request):
    """
    GET /api/claims/workqueue/?rescrub=1
    Returns recent claims with ERROR/WARN findings (after optional re-scrub).
    """
    rescrub = request.query_params.get("rescrub") in {"1", "true", "yes"}
    # keep it lightweight; feel free to tune slice
    claims = Claim.objects.all().order_by("-id")[:200]
    if rescrub:
        for c in claims:
            run_scrubber(c)

    rows = []
    for c in claims:
        errs = list(c.findings.filter(severity="ERROR").values("code", "message"))
        warns = list(c.findings.filter(severity="WARN").values("code", "message"))
        if errs or warns:
            rows.append({
                "id": c.id,
                "patient_id": c.patient_id,
                "payer_name": c.payer_name,
                "pos": c.pos,
                "total_charge": str(c.total_charge),
                "status": c.status,
                "errors": errs,
                "warnings": warns,
            })
    return Response({"count": len(rows), "results": rows})
