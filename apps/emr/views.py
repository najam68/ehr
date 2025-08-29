from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from datetime import datetime
from .models import Encounter, ProgressNote, Vital, Problem, Medication, Allergy, LabOrder, LabResult
from apps.patients.models import Patient  # patients app exists:contentReference[oaicite:9]{index=9}

# --- Pages (HTML) ---

def chart(request, patient_id: int):
    p = get_object_or_404(Patient, pk=patient_id)
    encounters = (Encounter.objects.filter(patient=p).order_by("-start")[:10])
    problems = p.problems.order_by("-status","-onset_date")[:20] if hasattr(p, "problems") else []
    meds = p.medications.order_by("-status","-start_date")[:20] if hasattr(p, "medications") else []
    allergies = p.allergies.order_by("-status")[:20] if hasattr(p, "allergies") else []
    last_vital = None
    if encounters:
        last_enc = encounters[0]
        last_vital = last_enc.vitals.order_by("-measured_at").first()
    ctx = {"patient": p, "encounters": encounters, "problems": problems,
           "meds": meds, "allergies": allergies, "last_vital": last_vital}
    return render(request, "emr/chart.html", ctx)

def new_encounter(request, patient_id: int):
    p = get_object_or_404(Patient, pk=patient_id)
    enc = Encounter.objects.create(patient=p, reason=request.GET.get("reason",""))
    messages.success(request, f"Encounter {enc.id} created.")
    return redirect(reverse("emr-encounter", args=[enc.id]))

def encounter_detail(request, enc_id: int):
    enc = get_object_or_404(Encounter, pk=enc_id)
    if request.method == "POST":
        if request.POST.get("action") == "add_note":
            body = request.POST.get("body","").strip()
            if body:
                ProgressNote.objects.create(encounter=enc, body=body, note_type=request.POST.get("note_type","PROGRESS"))
                messages.success(request, "Note added.")
            return redirect(reverse("emr-encounter", args=[enc.id]))
        if request.POST.get("action") == "add_vitals":
            def _i(x): 
                try: 
                    return int(x) if x not in (None,"") else None
                except: 
                    return None
            def _d(x):
                try:
                    return float(x) if x not in (None,"") else None
                except:
                    return None
            Vital.objects.create(
                encounter=enc,
                height_cm=_d(request.POST.get("height_cm")),
                weight_kg=_d(request.POST.get("weight_kg")),
                temp_c=_d(request.POST.get("temp_c")),
                pulse_bpm=_i(request.POST.get("pulse_bpm")),
                resp_rate=_i(request.POST.get("resp_rate")),
                bp_systolic=_i(request.POST.get("bp_systolic")),
                bp_diastolic=_i(request.POST.get("bp_diastolic")),
                spo2=_i(request.POST.get("spo2")),
            )
            messages.success(request, "Vitals saved.")
            return redirect(reverse("emr-encounter", args=[enc.id]))

    ctx = {
        "enc": enc,
        "notes": enc.notes.order_by("-created_at"),
        "vitals": enc.vitals.order_by("-measured_at"),
        "orders": enc.lab_orders.order_by("-ordered_at"),
    }
    return render(request, "emr/encounter_detail.html", ctx)
