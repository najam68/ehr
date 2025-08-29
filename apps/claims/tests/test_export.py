# apps/claims/tests/test_export.py
import csv
from io import StringIO
from django.urls import reverse
from rest_framework.test import APIClient
from apps.claims.models import Claim, Denial

def test_denials_export_csv(db):
    # Create minimal Claims (match required fields of your Claim model)
    c1 = Claim.objects.create(
        patient_id=1,
        payer_name="PAYER A",
        billing_provider_npi="1234567890",
        rendering_provider_npi="1234567890",
        pos="11",
        status="DRAFT",
        total_charge=0,
    )
    c2 = Claim.objects.create(
        patient_id=2,
        payer_name="PAYER B",
        billing_provider_npi="1234567890",
        rendering_provider_npi="1234567890",
        pos="11",
        status="DRAFT",
        total_charge=0,
    )

    # Now create Denials referencing real Claims (FK)
    d1 = Denial.objects.create(claim=c1, status="OPEN", reason="Missing code")
    d2 = Denial.objects.create(claim=c2, status="WORKING", reason="Eligibility")

    client = APIClient()
    url = reverse("denial-export")  # DRF action: basename 'denial' + 'export'
    resp = client.get(url, {"format": "csv"})

    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/csv")

    content = resp.content.decode()
    rows = list(csv.reader(StringIO(content)))
    assert rows[0] == ["id", "claim_id", "status", "reason", "created_at"]
    # check our two denials are present
    body = "\n".join(",".join(r) for r in rows[1:])
    assert str(d1.id) in body
    assert str(d2.id) in body
