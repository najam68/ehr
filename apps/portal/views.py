from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages

from apps.patients.models import Patient, Coverage
from apps.claims.models import Claim, EdiExport, Denial, DenialStatusHistory
from apps.claims.scrubber import run_scrubber
# If these helpers exist in your repo, keep them. If not, you can comment them out.
try:
    from apps.claims.autofix import propose_changes, apply_changes
except Exception:
    propose_changes = apply_changes = None
try:
    from apps.claims.x12_837p import build_and_write_837p
except Exception:
    build_and_write_837p = None

def spa(request):
    return render(request, "portal/spa.html")

def dashboard(request):
    counts = {
        "patients": Patient.objects.count(),
        "coverages": Coverage.objects.count(),
        "claims": Claim.objects.count(),
        "exports": EdiExport.objects.count(),
        "errors": Claim.objects.filter(findings__severity="ERROR").distinct().count(),
    }
    return render(request, "portal/dashboard.html", {"counts": counts})

def patients_list(request):
    rows = Patient.objects.all().order_by("last_name","first_name")[:200]
    return render(request, "portal/patients_list.html", {"rows": rows})

def claims_list(request):
    rows = (Claim.objects.all().order_by("-id")
            .values("id","patient_id","payer_name","pos","total_charge","status")[:200])
    return render(request, "portal/claims_list.html", {"rows": rows})

def claim_detail(request, pk: int):
    c = get_object_or_404(Claim, pk=pk)
    ctx = {
        "c": c,
        "lines": list(c.lines.all()),
        "dx": list(c.diagnoses.order_by("order")),
        "findings": list(c.findings.all().values("code","severity","message","suggestion")),
        "exports": list(c.edi_exports.all().order_by("-created_at")
                        .values("id","file_path","status","sha256","created_at")),
    }
    return render(request, "portal/claim_detail.html", ctx)

def claim_scrub(request, pk: int):
    c = get_object_or_404(Claim, pk=pk)
    run_scrubber(c)
    messages.success(request, "Scrub completed.")
    return redirect(reverse("portal-claim-detail", args=[pk]))

def claim_autofix(request, pk: int):
    if not (propose_changes and apply_changes):
        messages.error(request, "Auto-fix module not available.")
        return redirect(reverse("portal-claim-detail", args=[pk]))
    c = get_object_or_404(Claim, pk=pk)
    preview = propose_changes(c)
    if request.method == "POST":
        apply_changes(c, preview)
        messages.success(request, "Auto-fix applied.")
        return redirect(reverse("portal-claim-detail", args=[pk]))
    return render(request, "portal/autofix_preview.html", {"claim": c, "changes": preview})

def claim_submit(request, pk: int):
    if not build_and_write_837p:
        messages.error(request, "837 generator not available.")
        return redirect(reverse("portal-claim-detail", args=[pk]))
    c = get_object_or_404(Claim, pk=pk)
    if c.findings.filter(severity="ERROR").exists():
        messages.error(request, "Claim has blocking errors.")
        return redirect(reverse("portal-claim-detail", args=[pk]))
    pat = Patient.objects.filter(pk=c.patient_id).first()
    cov = (Coverage.objects.filter(patient_id=getattr(pat, "id", None))
           .order_by("-effective_date").first()) if pat else None
    payer_name = (cov.payer_name if cov and cov.payer_name else (c.payer_name or "PAYER"))
    fpath = build_and_write_837p(c, pat, cov, payer_name)
    from hashlib import sha256
    h = sha256(open(fpath,"rb").read()).hexdigest()
    EdiExport.objects.create(claim=c, file_path=fpath, sha256=h, status="QUEUED")
    messages.success(request, f"837 generated: {fpath}")
    return redirect(reverse("portal-claim-detail", args=[pk]))

def denials_list(request):
    rows = (Denial.objects.filter(status__in=["OPEN","WORKING"])
            .select_related("claim").order_by("-created_at"))
    # use your existing claims template namespace
    return render(request, "claims/claims_home.html", {"rows": rows})

def denial_detail(request, denial_id: int):
    d = get_object_or_404(Denial, pk=denial_id)
    if request.method == "POST":
        st = request.POST.get("status")
        note = request.POST.get("note","")
        valid = {s for s, _ in Denial.STATUS}
        if st in valid:
            old = d.status
            d.status = st
            d.save(update_fields=["status"])
            if note:
                DenialStatusHistory.objects.create(
                    denial=d, from_status=old or "", to_status=st, note=note
                )
            messages.success(request, "Denial updated.")
            # fall through to render
    hist = list(d.history.order_by("-created_at").values("from_status","to_status","note","created_at"))
    ctx = {"denial": d, "history": hist}
    # render your existing /templates/claims/denial_detail.html
    return render(request, "claims/denial_detail.html", ctx)
