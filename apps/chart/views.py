from django.http import JsonResponse
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from apps.patients.models import Patient
from .models import Encounter, SoapNote
from apps.audit.utils import log_event
from apps.common.decorators import group_required

def _page(title, body):
    return HttpResponse(
        "<!doctype html><html><head>"
        "<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>"
        f"<title>{title}</title></head><body class='bg-light'><div class='container py-4'>"
        f"<h1 class='h4 mb-3'>{title}</h1>{body}</div></body></html>"
    )
@group_required('Clinician')
@group_required('Clinician')

@login_required
def encounter_list(request):
    rows = []
    for e in Encounter.objects.select_related('patient').order_by('-id')[:50]:
        rows.append(f"<tr><td>{e.id}</td><td>{e.patient_id}</td><td>{e.status}</td>"
                    f"<td><a href='/chart/encounter/{e.id}/'>View</a></td></tr>")
    table = ("<div class='table-responsive'><table class='table table-sm table-striped'>"
             "<thead><tr><th>ID</th><th>Patient</th><th>Status</th><th></th></tr></thead>"
             "<tbody>" + "".join(rows) + "</tbody></table></div>") if rows else "<div class='alert alert-info'>No encounters yet.</div>"
    return _page("Encounters", table)
@group_required('Clinician')
@group_required('Clinician')

@login_required
def encounter_detail(request, encounter_id: int):
    e = Encounter.objects.select_related('patient').get(pk=encounter_id)
    log_event(request.user, "VIEW", "Encounter", e.id, {})
    s = getattr(e, "soap", None)
    body = [f"<p><b>Patient:</b> {e.patient_id}</p>",
            f"<p><b>Status:</b> {e.status}</p>",
            f"<p><b>Reason:</b> {e.reason}</p>"]
    if s:
        body.append("<hr><h2 class='h5'>SOAP Note</h2>")
        body.append(f"<p><b>Subjective:</b><br>{(s.subjective or '').replace(chr(10),'<br>')}</p>")
        body.append(f"<p><b>Objective:</b><br>{(s.objective or '').replace(chr(10),'<br>')}</p>")
        body.append(f"<p><b>Assessment:</b><br>{(s.assessment or '').replace(chr(10),'<br>')}</p>")
        body.append(f"<p><b>Plan:</b><br>{(s.plan or '').replace(chr(10),'<br>')}</p>")
    body.append(f"<hr><a class='btn btn-outline-primary' href='/billing/new/{e.id}/'>Create Superbill</a>")
    return _page(f"Encounter #{e.id}", "".join(body))
@group_required('Clinician')
@group_required('Clinician')

@csrf_exempt  # dev speed; replace with CSRF template later
@login_required
def new_encounter(request, patient_id: int):
    try:
        p = Patient.objects.get(pk=patient_id)
    except Patient.DoesNotExist:
        return _page("New Encounter", "<div class='alert alert-danger'>Patient not found.</div>")
    if request.method == "POST":
        reason = request.POST.get("reason","")
        subjective = request.POST.get("subjective","")
        objective = request.POST.get("objective","")
        assessment = request.POST.get("assessment","")
        plan = request.POST.get("plan","")
        e = Encounter.objects.create(patient=p, reason=reason)
        SoapNote.objects.create(encounter=e, subjective=subjective, objective=objective, assessment=assessment, plan=plan)
        log_event(request.user, "CREATE", "Encounter", e.id, {"reason": reason})
        return HttpResponseRedirect(f"/chart/encounter/{e.id}/")
    form = (
        "<form method='post'>"
        "<div class='mb-2'>"
        "<label class='form-label'>Reason</label>"
        "<input name='reason' class='form-control' placeholder='Chief complaint / reason for visit'>"
        "</div>"
        "<div class='row'>"
        "<div class='col-md-6'>"
        "<label class='form-label'>Subjective</label>"
        "<textarea name='subjective' class='form-control' rows='4'></textarea>"
        "</div>"
        "<div class='col-md-6'>"
        "<label class='form-label'>Objective</label>"
        "<textarea name='objective' class='form-control' rows='4'></textarea>"
        "</div>"
        "</div>"
        "<div class='row mt-2'>"
        "<div class='col-md-6'>"
        "<label class='form-label'>Assessment</label>"
        "<textarea name='assessment' class='form-control' rows='4'></textarea>"
        "</div>"
        "<div class='col-md-6'>"
        "<label class='form-label'>Plan</label>"
        "<textarea name='plan' class='form-control' rows='4'></textarea>"
        "</div>"
        "</div>"
        "<div class='mt-3'>"
        "<button class='btn btn-primary'>Save Encounter + SOAP</button>"
        "<a class='btn btn-secondary ms-2' href='/'>Cancel</a>"
        "</div>"
        "</form>"
    )
    return _page(f"New Encounter for Patient {p.id}", form)

from apps.chart.models import Encounter as DbEncounter, VitalSign as DbVital

@csrf_exempt
@csrf_exempt
@csrf_exempt
def vitals_intake_json(request, encounter_id: int):
    """POST JSON {items:[{code,display,value,unit,effective_time?},...]} to create vitals."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Use POST"}, status=405)

    import json
    try:
        enc = DbEncounter.objects.get(pk=encounter_id)
    except DbEncounter.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Encounter not found"}, status=404)

    try:
        payload = json.loads(request.body.decode() or "{}")
    except Exception:
        payload = {}

    items = payload.get("items") or []
    created = []
    for it in items:
        code    = (it.get("code") or "").strip()
        display = (it.get("display") or "").strip()
        value   = it.get("value")
        unit    = (it.get("unit") or "").strip()
        eff     = it.get("effective_time") or None
        if not code or value is None:
            continue
        v = DbVital.objects.create(
            encounter=enc, patient=enc.patient,
            code_system="http://loinc.org", code=code, display=display,
            value=float(value), unit=unit, effective_time=eff
        )
        created.append(v.id)

    # audit before returning
    try:
        log_event(request.user, "vitals-intake", "Encounter", enc.id, {"created": created})
    except Exception:
        pass

    return JsonResponse({"ok": True, "created": created})
