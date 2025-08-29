from django.core.management.base import BaseCommand
from django.utils.timezone import localdate
from datetime import timedelta
import json

class Command(BaseCommand):
    help = "List provider credentialing items expiring within N days (licenses, DEA, payer credentials)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=60, help="Look ahead this many days (default 60)")
        parser.add_argument("--json", action="store_true", help="Output JSON instead of text")

    def handle(self, *args, **opts):
        from apps.registry.models import Provider, ProviderPayerCredential

        # Optional models (tolerate missing)
        try:
            from apps.registry.models import ProviderLicense
        except Exception:
            ProviderLicense = None
        try:
            from apps.registry.models import ProviderDEARegistration
        except Exception:
            ProviderDEARegistration = None

        days = int(opts["days"])
        today = localdate()
        cutoff = today + timedelta(days=days)

        items = []

        # --- Licenses expiring ---
        if ProviderLicense is not None:
            lic_qs = ProviderLicense.objects.select_related("provider")\
                        .filter(expiry__isnull=False, expiry__lte=cutoff)
            for lic in lic_qs:
                items.append({
                    "type": "license",
                    "provider_id": lic.provider_id,
                    "provider": f"{getattr(lic.provider,'last_name','')}, {getattr(lic.provider,'first_name','')}",
                    "state": lic.state,
                    "number": lic.number,
                    "expiry": str(lic.expiry) if lic.expiry else None,
                    "notes": lic.notes or "",
                })

        # --- DEA registrations expiring ---
        if ProviderDEARegistration is not None:
            dea_qs = ProviderDEARegistration.objects.select_related("provider")\
                        .filter(expiry__isnull=False, expiry__lte=cutoff)
            for dea in dea_qs:
                items.append({
                    "type": "dea",
                    "provider_id": dea.provider_id,
                    "provider": f"{getattr(dea.provider,'last_name','')}, {getattr(dea.provider,'first_name','')}",
                    "dea_number": dea.dea_number,
                    "schedules": list(dea.schedules or []),
                    "expiry": str(dea.expiry) if dea.expiry else None,
                    "notes": dea.notes or "",
                })

        # --- Payer credentials (end_date) — always present ---
        ppc_fields = {f.name for f in ProviderPayerCredential._meta.get_fields()}
        cred_end_qs = ProviderPayerCredential.objects.select_related("provider","payer")\
                         .filter(end_date__isnull=False, end_date__lte=cutoff)
        for c in cred_end_qs:
            items.append({
                "type": "credential-end",
                "provider_id": c.provider_id,
                "provider": f"{getattr(c.provider,'last_name','')}, {getattr(c.provider,'first_name','')}",
                "payer": str(c.payer),
                "status": c.status,
                "network_status": getattr(c, "network_status", "") if "network_status" in ppc_fields else "",
                "plan_id": getattr(c, "plan_id", "") if "plan_id" in ppc_fields else "",
                "plan_name": getattr(c, "plan_name", "") if "plan_name" in ppc_fields else "",
                "effective_date": str(c.effective_date) if c.effective_date else None,
                "end_date": str(c.end_date) if c.end_date else None,
                "last_verified": str(getattr(c, "last_verified", "")) or None if "last_verified" in ppc_fields else None,
                "reminder_date": str(getattr(c, "reminder_date", "")) or None if "reminder_date" in ppc_fields else None,
            })

        # --- Payer credentials (reminder_date) — only if field exists ---
        if "reminder_date" in ppc_fields:
            cred_rem_qs = ProviderPayerCredential.objects.select_related("provider","payer")\
                              .filter(reminder_date__isnull=False, reminder_date__lte=cutoff)
            for c in cred_rem_qs:
                items.append({
                    "type": "credential-reminder",
                    "provider_id": c.provider_id,
                    "provider": f"{getattr(c.provider,'last_name','')}, {getattr(c.provider,'first_name','')}",
                    "payer": str(c.payer),
                    "status": c.status,
                    "network_status": getattr(c, "network_status", "") if "network_status" in ppc_fields else "",
                    "plan_id": getattr(c, "plan_id", "") if "plan_id" in ppc_fields else "",
                    "plan_name": getattr(c, "plan_name", "") if "plan_name" in ppc_fields else "",
                    "effective_date": str(c.effective_date) if c.effective_date else None,
                    "end_date": str(c.end_date) if c.end_date else None,
                    "last_verified": str(getattr(c, "last_verified", "")) or None if "last_verified" in ppc_fields else None,
                    "reminder_date": str(c.reminder_date),
                })

        data = {
            "as_of": str(today),
            "cutoff": str(cutoff),
            "days": days,
            "count": len(items),
            "items": items,
        }

        if opts["json"]:
            self.stdout.write(json.dumps(data, indent=2))
            return

        # Pretty text
        if not items:
            self.stdout.write(self.style.SUCCESS(f"No credentialing items due within {days} days."))
            return

        self.stdout.write(self.style.WARNING(f"Expiring items within {days} days (as of {today}):"))
        from collections import defaultdict
        def date_key(it):
            # sort by the earliest relevant date we have
            return it.get("end_date") or it.get("expiry") or it.get("reminder_date") or ""
        by_provider = defaultdict(list)
        for it in items:
            by_provider[(it["provider_id"], it["provider"])].append(it)
        for (pid, pname), rows in sorted(by_provider.items(), key=lambda kv: date_key(sorted(kv[1], key=date_key)[0])):
            self.stdout.write(self.style.MIGRATE_HEADING(f"• {pname} (#{pid})"))
            for it in sorted(rows, key=date_key):
                t = it["type"]
                if t == "license":
                    self.stdout.write(f"  - LICENSE {it['state']} #{it['number']}  exp {it['expiry']}")
                elif t == "dea":
                    self.stdout.write(f"  - DEA {it['dea_number']}  sched {','.join(it['schedules'])}  exp {it['expiry']}")
                elif t == "credential-end":
                    self.stdout.write(f"  - CREDENTIAL {it['payer']} status {it['status']}  END {it['end_date']}  (eff {it.get('effective_date') or '-'})")
                else:
                    self.stdout.write(f"  - CREDENTIAL {it['payer']} status {it['status']}  REMINDER {it['reminder_date']}")
            self.stdout.write("")
