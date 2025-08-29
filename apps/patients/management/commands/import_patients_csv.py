import csv, os, json, hashlib
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.patients.models import Patient, Coverage
from apps.ingestion.models import Provenance
from datetime import datetime

def sha256_path(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()

class Command(BaseCommand):
    help = ("Import patients + primary coverage from CSV. "
            "Columns: first_name,last_name,date_of_birth,phone,email,"
            "address_line,city,state,postal,"
            "payer_name,member_id,group_number,effective_date,termination_date,relation_to_subscriber,plan_json")

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to CSV file")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["csv_path"]
        if not os.path.exists(path):
            raise CommandError(f"File not found: {path}")

        prov = Provenance.objects.create(
            source_system="CSV (manual)",
            file_name=os.path.basename(path),
            file_hash=sha256_path(path),
            format="CSV",
            notes="Patients + Coverage import",
        )

        created_patients = 0
        created_coverages = 0
        with open(path, "r", encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.DictReader(f), start=1):
                fn = (row.get("first_name") or "").strip()
                ln = (row.get("last_name") or "").strip()
                dob = (row.get("date_of_birth") or "").strip()
                if not (fn and ln and dob):
                    raise CommandError(f"Row {i}: first_name, last_name, date_of_birth are required")

                # upsert patient by (first,last,dob)
                pat, p_created = Patient.objects.update_or_create(
                    first_name=fn,
                    last_name=ln,
                    date_of_birth=parse_date(dob),
                    defaults={
                        "phone": (row.get("phone") or "").strip(),
                        "email": (row.get("email") or "").strip(),
                        "address": {
                            "line": (row.get("address_line") or "").strip(),
                            "city": (row.get("city") or "").strip(),
                            "state": (row.get("state") or "").strip(),
                            "postal": (row.get("postal") or "").strip(),
                        },
                    },
                )
                if p_created:
                    created_patients += 1

                payer = (row.get("payer_name") or "").strip()
                member = (row.get("member_id") or "").strip()
                if payer and member:
                    plan_json = (row.get("plan_json") or "").strip()
                    plan = {}
                    if plan_json:
                        try:
                            plan = json.loads(plan_json)
                        except Exception:
                            raise CommandError(f"Row {i}: plan_json must be valid JSON")

                    cov, c_created = Coverage.objects.update_or_create(
                        patient=pat,
                        member_id=member,
                        payer_name=payer,
                        defaults={
                            "group_number": (row.get("group_number") or "").strip(),
                            "effective_date": parse_date(row.get("effective_date")),
                            "termination_date": parse_date(row.get("termination_date")),
                            "relation_to_subscriber": (row.get("relation_to_subscriber") or "").strip(),
                            "plan": plan,
                        },
                    )
                    if c_created:
                        created_coverages += 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported patients={created_patients}, coverages={created_coverages}. provenance_id={prov.id}"
        ))

