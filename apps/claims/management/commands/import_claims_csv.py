import csv, os, hashlib
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.claims.models import Claim, Diagnosis, ClaimLine
from apps.ingestion.models import Provenance

def sha256_path(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _dec(x, default="0"):
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError):
        return Decimal(default)

class Command(BaseCommand):
    help = "Import claims from a CSV. Columns: patient_id,payer_name,pos,total_charge,dx_list,lines. lines= 'CPT|UNITS|CHARGE;...'"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to claims CSV")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["csv_path"]
        if not os.path.exists(path):
            raise CommandError(f"File not found: {path}")

        # provenance
        prov = Provenance.objects.create(
            source_system="CSV (manual)",
            file_name=os.path.basename(path),
            file_hash=sha256_path(path),
            format="CSV",
            notes="Claims import (Claim + Diagnosis + ClaimLine)",
        )

        created = 0
        with open(path, "r", encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.DictReader(f), start=1):
                try:
                    patient_id = int((row.get("patient_id") or "").strip())
                except ValueError:
                    raise CommandError(f"Row {i}: invalid patient_id")

                payer_name = (row.get("payer_name") or "").strip()
                pos = (row.get("pos") or "").strip()
                total_charge = _dec(row.get("total_charge"))

                if not payer_name or not pos:
                    raise CommandError(f"Row {i}: payer_name and pos are required")

                claim = Claim.objects.create(
                    patient_id=patient_id,
                    payer_name=payer_name,
                    billing_provider_npi="1234567890",
                    rendering_provider_npi="1234567890",
                    facility_name="Imported Clinic",
                    pos=pos,
                    status="READY",
                    total_charge=total_charge,
                )

                # diagnoses (pipe-separated)
                dx_list = (row.get("dx_list") or "").strip()
                if dx_list:
                    for order, dx in enumerate([d.strip() for d in dx_list.split("|") if d.strip()], start=1):
                        Diagnosis.objects.create(claim=claim, code=dx, order=order)

                # lines (semicolon-separated entries: CPT|UNITS|CHARGE)
                lines = (row.get("lines") or "").strip()
                if lines:
                    for chunk in [c for c in lines.split(";") if c.strip()]:
                        parts = [p.strip() for p in chunk.split("|")]
                        if len(parts) < 3:
                            raise CommandError(f"Row {i}: bad line entry '{chunk}'")
                        cpt, units, charge = parts[0], _dec(parts[1], "1"), _dec(parts[2], "0")
                        ClaimLine.objects.create(
                            claim=claim,
                            cpt=cpt,
                            modifiers=[],
                            units=units,
                            diagnosis_pointers=[1],  # simplest case: points to first dx
                            charge=charge,
                        )

                created += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created} claims. provenance_id={prov.id}"))

