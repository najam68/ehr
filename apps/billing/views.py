from django.http import HttpResponse, JsonResponse, JsonResponse, JsonResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# Optional role guard: fall back to no-op if missing so file always loads
try:
    from apps.common.decorators import group_required
except Exception:
    def group_required(_name):
        def _wrap(fn): return fn
        return _wrap

from .models import Superbill
from apps.chart.models import Encounter

def _page(title, body):
    return HttpResponse(
        "<!doctype html><html><head>"
        "<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>"
        f"<title>{title}</title></head><body class='bg-light'><div class='container py-4'>"
        f"<h1 class='h4 mb-3'>{title}</h1>{body}</div></body></html>"
    )

@login_required
@group_required('Biller')
def superbill_list(request):
    rows = []
    for sb in Superbill.objects.select_related('encounter','patient').order_by('-id')[:50]:
        rows.append(
            f"<tr><td>{sb.id}</td><td>{sb.patient_id}</td><td>{sb.status}</td>"
            f"<td>${sb.total}</td><td><a href='/billing/{sb.id}/'>View</a></td></tr>"
        )
    table = ("<div class='table-responsive'><table class='table table-sm table-striped'>"
             "<thead><tr><th>ID</th><th>Patient</th><th>Status</th><th>Total</th><th></th></tr></thead>"
             "<tbody>" + "".join(rows) + "</tbody></table></div>") if rows else "<div class='alert alert-info'>No superbills yet.</div>"
    return _page("Superbills", table)

@login_required
@group_required('Biller')
def superbill_detail(request, superbill_id: int):
    sb = Superbill.objects.select_related('encounter','patient').get(pk=superbill_id)
    body = [
        f"<p><b>Encounter:</b> {sb.encounter_id}</p>",
        f"<p><b>Patient:</b> {sb.patient_id}</p>",
        f"<p><b>Status:</b> {sb.status}</p>",
        f"<p><b>Total:</b> ${sb.total}</p>",
        "<hr><h2 class='h6'>Codes</h2>",
        f"<p><b>ICD-10:</b> {', '.join(sb.icd_codes) if sb.icd_codes else '(none)'}",
        f"<br><b>CPT:</b> {', '.join(sb.cpt_codes) if sb.cpt_codes else '(none)'}",
    ]
    return _page(f"Superbill #{sb.id}", "".join(body))

@csrf_exempt  # dev speed; replace with CSRF template later
@login_required
@group_required('Biller')   # no-op if decorator missing
def new_superbill(request, encounter_id: int):
    # Lazy import audit logger
    try:
        from apps.audit.utils import log_event as _log
    except Exception:
        _log = None

    try:
        e = Encounter.objects.select_related('patient').get(pk=encounter_id)
    except Encounter.DoesNotExist:
        return _page("New Superbill", "<div class='alert alert-danger'>Encounter not found.</div>")

    if request.method == "POST":
        icd = [c.strip().upper() for c in (request.POST.get('icd') or "").split(",") if c.strip()]
        cpt = [c.strip().upper() for c in (request.POST.get('cpt') or "").split(",") if c.strip()]
        total_raw = (request.POST.get("total") or "0").strip()
        try:
            total_val = float(total_raw)
        except Exception:
            total_val = 0.0
        sb = Superbill.objects.create(encounter=e, patient=e.patient, icd_codes=icd, cpt_codes=cpt, total=total_val)
        if _log: _log(request.user, "CREATE", "Superbill", sb.id, {"icd": icd, "cpt": cpt, "total": total_val})
        return HttpResponseRedirect(f"/billing/{sb.id}/")

    # Safer HTML: placeholders for IDs to avoid formatting pitfalls
    tpl = '''
    <div class="mb-3">For Encounter <b>#__EID__</b> (Patient __PID__)</div>
    <form method="post">
      <div class="row g-2">
        <div class="col-md-6">
          <label class="form-label">ICD-10</label>
          <div class="input-group mb-1">
            <input id="icd_q" class="form-control" placeholder="Search ICD-10 (e.g., J06)">
            <button class="btn btn-outline-secondary" type="button" onclick="searchCodes('ICD10')">Search</button>
          </div>
          <div class="small text-muted mb-1">Most common:</div>
          <select id="icd_results" class="form-select form-select-sm" size="8"></select>
          <div class="mt-2"><b>Selected ICD-10:</b>
            <select id="icd_selected" class="form-select form-select-sm" size="4" multiple></select>
          </div>
        </div>
        <div class="col-md-6">
          <label class="form-label">CPT</label>
          <div class="input-group mb-1">
            <input id="cpt_q" class="form-control" placeholder="Search CPT (e.g., 9921)">
            <button class="btn btn-outline-secondary" type="button" onclick="searchCodes('CPT')">Search</button>
          </div>
          <div class="small text-muted mb-1">Most common:</div>
          <select id="cpt_results" class="form-select form-select-sm" size="8"></select>
          <div class="mt-2"><b>Selected CPT:</b>
            <select id="cpt_selected" class="form-select form-select-sm" size="4" multiple></select>
          </div>
        </div>
      </div>
      <div class="mt-2">
        <label class="form-label">Total amount (USD)</label>
        <input name="total" class="form-control" value="0.00">
      </div>
      <input type="hidden" name="icd" id="icd_input">
      <input type="hidden" name="cpt" id="cpt_input">
      <div class="mt-3">
        <button class="btn btn-primary">Save Superbill</button>
        <a class="btn btn-secondary ms-2" href="/chart/encounter/__EID__/">Cancel</a>
      </div>
    </form>
    <script>
      const icdSel = new Set(); const cptSel = new Set();
      function renderSel(){
        function fill(id, arr){
          const sel = document.getElementById(id);
          sel.innerHTML = '';
          for(const v of arr){ const o=document.createElement('option'); o.value=v; o.text=v; sel.appendChild(o); }
        }
        fill('icd_selected', Array.from(icdSel));
        fill('cpt_selected', Array.from(cptSel));
        document.getElementById('icd_input').value = Array.from(icdSel).join(',');
        document.getElementById('cpt_input').value = Array.from(cptSel).join(',');
      }
      function addCode(sys, code){ if(sys==='ICD10'){ icdSel.add(code); } else { cptSel.add(code); } renderSel(); }
      function loadMostCommon(sys){
        fetch('/codes/most_common/?system='+sys).then(r=>r.json()).then(d=>{
          const list = document.getElementById(sys==='ICD10'?'icd_results':'cpt_results');
          list.innerHTML = '';
          for(const item of d.results){
            const o=document.createElement('option'); o.value=item.code; o.text=item.code+' — '+item.description;
            list.appendChild(o);
          }
          list.onchange = () => { const val = list.value; if(val){ addCode(sys, val); } };
        });
      }
      function searchCodes(sys){
        const q = document.getElementById(sys==='ICD10'?'icd_q':'cpt_q').value;
        fetch('/codes/search/?system='+sys+'&q='+encodeURIComponent(q)).then(r=>r.json()).then(d=>{
          const list = document.getElementById(sys==='ICD10'?'icd_results':'cpt_results');
          list.innerHTML = '';
          for(const item of d.results){
            const o=document.createElement('option'); o.value=item.code; o.text=item.code+' — '+item.description;
            list.appendChild(o);
          }
        });
      }
      loadMostCommon('ICD10'); loadMostCommon('CPT'); renderSel();
    </script>
    '''
    html = tpl.replace('__EID__', str(e.id)).replace('__PID__', str(e.patient_id))
    return _page("New Superbill", html)


def superbill_claim_fhir(request, superbill_id: int):
    """Return a minimal FHIR Claim JSON for the given Superbill id."""
    from .models import Superbill
    try:
        sb = Superbill.objects.select_related('patient','encounter').get(pk=superbill_id)
    except Superbill.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Superbill not found"}, status=404)

    patient_id = getattr(sb.patient, 'id', None)
    icds = list(getattr(sb, 'icd_codes', []) or [])
    cpts = list(getattr(sb, 'cpt_codes', []) or [])
    total = float(sb.total) if getattr(sb, 'total', None) is not None else 0.0

    # Minimal FHIR Claim (no strict validation; simple mapping)
    claim = {
        "resourceType": "Claim",
        "status": "active",
        "type": {"coding": [{"system":"http://terminology.hl7.org/CodeSystem/claim-type","code":"professional"}]},
        "use": "claim",
        "priority": {"coding":[{"system":"http://terminology.hl7.org/CodeSystem/processpriority","code":"normal"}]},
        "patient": {"reference": f"Patient/{patient_id}"} if patient_id else {"display":"Unknown Patient"},
        "diagnosis": [],
        "item": [],
        "total": {"value": round(total, 2), "currency":"USD"}
    }

    # Diagnosis (ICD-10)
    for i, icd in enumerate(icds):
        if icd:
            claim["diagnosis"].append({
                "sequence": i+1,
                "diagnosisCodeableConcept": {
                    "coding":[{"system":"http://hl7.org/fhir/sid/icd-10-cm","code":icd}]
                }
            })

    # Items (CPT)
    for j, cpt in enumerate(cpts):
        if cpt:
            claim["item"].append({
                "sequence": j+1,
                "productOrService": {
                    "coding":[{"system":"http://www.ama-assn.org/go/cpt","code":cpt}]
                }
            })

    return JsonResponse({"ok": True, "resource": claim})


def superbill_json(request, superbill_id: int):
    """
    Read-only JSON for a Superbill. Includes line items if SuperbillLine exists,
    otherwise returns the legacy fields only.
    """
    from .models import Superbill
    try:
        sb = Superbill.objects.select_related('patient').get(pk=superbill_id)
    except Superbill.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Superbill not found"}, status=404)

    # Try to import SuperbillLine, but don't fail if it doesn't exist yet
    lines_data = []
    try:
        from .models import SuperbillLine
        for ln in SuperbillLine.objects.filter(superbill=sb).order_by('id'):
            lines_data.append({
                "id": ln.id,
                "code": ln.code,
                "modifiers": [m for m in [ln.mod1, ln.mod2, ln.mod3, ln.mod4] if m],
                "units": ln.units,
                "charge": float(ln.charge or 0),
                "pos": ln.pos,
                "dx_ptrs": list(ln.dx_ptrs or []),
                "auth_number": ln.auth_number,
                "notes": ln.notes,
                "rendering_provider_id": getattr(ln, "rendering_provider_id", None),
            })
    except Exception:
        # model not present or other non-fatal issue
        lines_data = []

    out = {
        "ok": True,
        "id": sb.id,
        "patient_id": getattr(sb, "patient_id", None),
        "icd_codes": list(getattr(sb, "icd_codes", []) or []),
        "cpt_codes": list(getattr(sb, "cpt_codes", []) or []),  # legacy flat list
        "total": float(getattr(sb, "total", 0) or 0),
        "status": getattr(sb, "status", ""),
        "lines": lines_data,
    }
    return JsonResponse(out)

@csrf_exempt
def superbill_list_json(request):
    from .models import Superbill
    rows = [{"id": sb.id, "patient_id": getattr(sb,"patient_id",None), "status": getattr(sb,"status","")} for sb in Superbill.objects.order_by("-id")[:50]]
    return JsonResponse({"ok": True, "count": len(rows), "items": rows})

@csrf_exempt
def claimresponse_store_json(request, superbill_id: int):
    from .models import Superbill, ClaimResponseStore
    import json, traceback
    if request.method != "POST":
        return JsonResponse({"ok": False, "error":"Use POST"}, status=405)
    try:
        sb = Superbill.objects.get(pk=superbill_id)
    except Superbill.DoesNotExist:
        return JsonResponse({"ok": False, "error":"Superbill not found"}, status=404)
    try:
        payload = json.loads(request.body.decode() or "{}")
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Bad JSON: {e}"}, status=400)
    try:
        cr, _ = ClaimResponseStore.objects.get_or_create(superbill=sb)
        cr.payload = payload or {}
        cr.save(update_fields=["payload"])
        return JsonResponse({"ok": True, "stored": True, "superbill_id": sb.id})
    except Exception as e:
        # Return JSON instead of HTML 500 so you can see the error
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def claim_export_json(request, superbill_id: int):
    from .models import Superbill, SuperbillLine
    sb = Superbill.objects.filter(pk=superbill_id).first()
    if not sb:
        return JsonResponse({"ok": False, "error":"not-found"}, status=404)
    # Enrich header: try primary Coverage for this patient; compute age/sex if available
    payer_id = payer_name = plan_name = member_id = ''
    try:
        from apps.registry.models import Coverage as DbCoverage
        cov = DbCoverage.objects.filter(patient_id=getattr(sb,'patient_id',None)).order_by('-is_primary','priority','id').first()
        if cov:
            payer_id = str(getattr(cov.payer,'id', ''))
            payer_name = str(getattr(cov.payer,'name', '') or cov.payer)
            plan_name = getattr(cov,'plan_name','') or ''
            member_id = getattr(cov,'member_id','') or ''
    except Exception:
        pass
    patient_sex = ''
    patient_age = None
    try:
        from apps.patients.models import Patient as DbPatient
        p = DbPatient.objects.filter(pk=getattr(sb,'patient_id',None)).first()
        if p:
            patient_sex = (getattr(p,'gender','') or '').lower()
            dob = getattr(p,'dob',None)
            if dob:
                from datetime import date
                today = date.today()
                patient_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        pass
    hdr = {
        "claim_id": sb.id,
        "patient_id": getattr(sb,'patient_id',None),
        "diagnoses": list(getattr(sb,'icd_codes',[]) or []),
        "total": float(getattr(sb,'total',0) or 0),
        "status": getattr(sb,'status','') or '',
        "payer_id": payer_id,
        "payer_name": payer_name,
        "plan_name": plan_name,
        "member_id": member_id,
        "patient_sex": patient_sex,
        "patient_age": patient_age
    }
    items = []
    for ln in SuperbillLine.objects.filter(superbill=sb).order_by('id'):
        items.append({
            "code": ln.code,
            "modifiers": [m for m in [ln.mod1,ln.mod2,ln.mod3,ln.mod4] if m],
            "units": ln.units,
            "charge": float(ln.charge or 0),
            "pos": ln.pos,
            "diagnosisPointers": list(ln.dx_ptrs or []),
        })
    return JsonResponse({"ok": True, "header": hdr, "items": items})


@csrf_exempt
def lines_intake_json(request, superbill_id: int):
    """POST JSON to add lines:
       {
         "items":[
           {"code":"99213","modifiers":["25"],"units":1,"charge":125.0,"pos":"11","dx_ptrs":[1]},
           ...
         ]
       }
    """
    import json
    from .models import Superbill, SuperbillLine
    if request.method != "POST":
        return JsonResponse({"ok": False, "error":"Use POST"}, status=405)
    sb = Superbill.objects.filter(pk=superbill_id).first()
    if not sb:
        return JsonResponse({"ok": False, "error":"not-found"}, status=404)
    try:
        payload = json.loads(request.body.decode() or "{}")
    except Exception:
        payload = {}
    created = []
    for it in (payload.get("items") or []):
        code = (it.get("code") or "").strip()
        if not code:
            continue
        mods = it.get("modifiers") or []
        units = int(it.get("units") or 1)
        charge = float(it.get("charge") or 0)
        pos = (it.get("pos") or "").strip()
        dx_ptrs = it.get("dx_ptrs") or []
        ln = SuperbillLine.objects.create(
            superbill=sb, code=code,
            mod1=(mods[0] if len(mods)>0 else ""), mod2=(mods[1] if len(mods)>1 else ""),
            mod3=(mods[2] if len(mods)>2 else ""), mod4=(mods[3] if len(mods)>3 else ""),
            units=units, charge=charge, pos=pos, dx_ptrs=dx_ptrs
        )
        created.append(ln.id)
    return JsonResponse({"ok": True, "created": created})
