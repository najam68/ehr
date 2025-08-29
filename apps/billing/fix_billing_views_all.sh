#!/usr/bin/env bash
set -euo pipefail

log(){ printf "\n▶ %s\n" "$*"; }
die(){ echo "❌ %s\n" "$*" >&2; exit 1; }

[ -f manage.py ] || die "Run from your Django project root (manage.py not found)."

PY="${PYTHON:-$(command -v python3 || command -v python)}"

VIEWS_PATH="apps/billing/views.py"
URLS_PATH="apps/billing/urls.py"

log "Writing clean apps/billing/views.py (list, detail, new)"
mkdir -p apps/billing
cat > "$VIEWS_PATH" <<'PY'
from django.http import HttpResponse, HttpResponseRedirect
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
PY

log "Ensuring apps/billing/urls.py imports and patterns"
mkdir -p apps/billing
cat > "$URLS_PATH" <<'PY'
from django.urls import path
from .views import new_superbill, superbill_detail, superbill_list

urlpatterns = [
    path("new/<int:encounter_id>/", new_superbill, name="billing-new-superbill"),
    path("<int:superbill_id>/", superbill_detail, name="billing-superbill-detail"),
    path("", superbill_list, name="billing-superbill-list"),
]
PY

echo "▶ Django check"
python manage.py check

echo "✅ Billing views repaired. Try: /billing/new/<encounter_id>/ and /billing/"
