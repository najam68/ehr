# config/views.py

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.utils.html import escape
from django.contrib.auth import get_user
from django.middleware.csrf import get_token
from django.utils.timezone import now
from datetime import timedelta



def home(request):
    user = get_user(request)
    uname = user.get_username() if getattr(user,'is_authenticated',False) else 'Anonymous'
    csrf = get_token(request)
    html = (
      "<!doctype html><html lang='en'><head>"
      "<meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
      "<title>EHR Starter</title>"
      "<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>"
      "<style>body{background:#f7f7fb}.card{border:0;box-shadow:0 1px 2px rgba(0,0,0,.05),0 4px 16px rgba(0,0,0,.04)}</style>"
      "</head><body class='bg-light'>"
      "<nav class='navbar navbar-expand-lg bg-white border-bottom mb-4'><div class='container'>"
      "<a class='navbar-brand fw-semibold' href='/'>EHR Starter</a>"
      "<ul class='navbar-nav ms-auto'>"
      "<li class='nav-item'><a class='nav-link' href='/patients/quick_new/'>+ Quick Registration</a></li>"
      "<li class='nav-item'><a class='nav-link' href='/dashboard/fhir-demo'>FHIR Viewer</a></li>"
      "<li class='nav-item'><a class='nav-link' href='/quick/new-encounter/'>New Encounter</a></li>"
      "<li class='nav-item'>"
      "<form method='post' action='/accounts/logout/' class='d-inline m-0 p-0'>"
      "<input type='hidden' name='csrfmiddlewaretoken' value='" + csrf + "'>"
      "<button class='nav-link btn btn-link p-0' type='submit' style='text-decoration:none'>Logout</button>"
      "</form>"
      "</li>"
      "</ul></div></nav>"
      "<main class='container'>"
      "<div class='h5 mb-3'>Welcome, " + escape(uname) + "</div>"
      "<div class='card'><div class='card-body'><div class='text-muted small'>Minimal dashboard</div></div></div>"
      "</main></body></html>"
    )
    return HttpResponse(html)


def fhir_demo_view(request):
    html = """<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FHIR Viewer</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>pre{white-space:pre-wrap;word-break:break-word}</style>
</head>
<body class="bg-light">
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="h5 m-0">FHIR Patient Bundle (First Patient)</h1>
      <div class="d-flex gap-2">
        <a class="btn btn-secondary" href="/">Back</a>
        <button class="btn btn-outline-secondary" id="toggle">Show raw JSON</button>
        <a class="btn btn-outline-primary" href="/fhir/patient/first/bundle/" target="_blank" rel="noopener">Open raw JSON</a>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <h2 class="h6 mb-3">Patient</h2>
        <div class="row g-2">
          <div class="col-md-6"><div class="text-muted small">Name</div><div id="p_name" class="fw-semibold">—</div></div>
          <div class="col-md-3"><div class="text-muted small">Gender</div><div id="p_gender">—</div></div>
          <div class="col-md-3"><div class="text-muted small">Birth Date</div><div id="p_birthDate">—</div></div>
          <div class="col-12"><div class="text-muted small">Address</div><div id="p_address">—</div></div>
        </div>
        <div class="mt-3">
          <a id="registry_link" class="btn btn-sm btn-primary" href="#" target="_blank" rel="noopener">Open in Registry</a>
        </div>
      </div>
    </div>

    <div class="card" id="raw_wrap" style="display:none">
      <div class="card-body">
        <h2 class="h6 mb-2">Raw JSON</h2>
        <pre id="raw" class="bg-white p-3 rounded border"></pre>
      </div>
    </div>
  </div>

  <script>
  const toggleBtn = document.getElementById('toggle');
  const rawWrap = document.getElementById('raw_wrap');
  toggleBtn.addEventListener('click', ()=> {
    const vis = rawWrap.style.display !== 'none';
    rawWrap.style.display = vis ? 'none' : 'block';
    toggleBtn.textContent = vis ? 'Show raw JSON' : 'Hide raw JSON';
  });

  async function load() {
    try {
      const r = await fetch('/fhir/patient/first/bundle/');
      const bundle = await r.json();
      // Find the Patient resource
      const entries = Array.isArray(bundle.entry) ? bundle.entry : [];
      let patient = null;
      for (const e of entries) {
        if (e && e.resource && e.resource.resourceType === 'Patient') { patient = e.resource; break; }
      }
      if (!patient) {
        document.getElementById('p_name').textContent = 'No Patient in bundle';
        document.getElementById('raw').textContent = JSON.stringify(bundle, null, 2);
        return;
      }
      // Name
      const n = (patient.name && patient.name[0]) || {};
      const family = n.family || '';
      const given = Array.isArray(n.given) && n.given.length ? n.given[0] : '';
      document.getElementById('p_name').textContent = (family ? family : '') + (given ? ', ' + given : '');
      // Gender
      document.getElementById('p_gender').textContent = patient.gender || '—';
      // Birth Date
      document.getElementById('p_birthDate').textContent = patient.birthDate || '—';
      // Address
      const a = (patient.address && patient.address[0]) || {};
      const parts = [];
      if (Array.isArray(a.line) && a.line.length) parts.push(a.line[0]);
      if (a.city) parts.push(a.city);
      if (a.state) parts.push(a.state);
      if (a.postalCode) parts.push(a.postalCode);
      document.getElementById('p_address').textContent = parts.join(', ') || '—';
      // Link to registry if we have an id
      if (patient.id) {
        document.getElementById('registry_link').href = '/registry/patient/' + encodeURIComponent(patient.id) + '/';
      } else {
        document.getElementById('registry_link').classList.add('disabled');
      }
      // Raw
      document.getElementById('raw').textContent = JSON.stringify(bundle, null, 2);
    } catch(e) {
      document.getElementById('p_name').textContent = 'Error loading bundle';
      document.getElementById('raw').textContent = String(e);
      rawWrap.style.display = 'block';
      toggleBtn.textContent = 'Hide raw JSON';
    }
  }
  document.addEventListener('DOMContentLoaded', load);
  </script>
</body></html>"""
    return HttpResponse(html)


def quick_patient_new(request):
    try:
        from apps.patients.models import Patient
    except Exception:
        return HttpResponse("<div class='container py-5'><div class='alert alert-danger'>Patients app not available.</div></div>")
    if request.method == "POST":
        fn=(request.POST.get('first_name') or '').strip()
        ln=(request.POST.get('last_name') or '').strip()
        dob=(request.POST.get('dob') or '').strip()
        gender=(request.POST.get('gender') or '').strip()
        email=(request.POST.get('email') or '').strip()
        phone=(request.POST.get('phone') or '').strip()
        obj=Patient.objects.create(first_name=fn,last_name=ln,dob=dob or None,gender=gender or '',email=email,phone=phone)
        return HttpResponseRedirect(f"/registry/patient/{obj.id}/")
    html = """<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Quick Registration</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container py-4">
    <h1 class="h5 mb-3">Quick Patient Registration</h1>
    <form method="post">
      <div class="row g-2">
        <div class="col-md-4"><label class="form-label">First Name</label><input name="first_name" class="form-control" required></div>
        <div class="col-md-4"><label class="form-label">Last Name</label><input name="last_name" class="form-control" required></div>
        <div class="col-md-4"><label class="form-label">DOB (YYYY-MM-DD)</label><input name="dob" class="form-control"></div>
        <div class="col-md-3"><label class="form-label">Gender</label><input name="gender" class="form-control" placeholder="male/female/other"></div>
        <div class="col-md-4"><label class="form-label">Email</label><input name="email" class="form-control"></div>
        <div class="col-md-3"><label class="form-label">Phone</label><input name="phone" class="form-control"></div>
      </div>
      <div class="mt-3">
        <button class="btn btn-primary">Create</button>
        <a class="btn btn-secondary ms-2" href="/">Cancel</a>
      </div>
    </form>
  </div>
</body></html>"""
    return HttpResponse(html)

def quick_new_encounter(request):
    """Helper: /quick/new-encounter/?patient_id=123 -> /chart/patient/123/encounter/new/"""
    pid = (request.GET.get('patient_id') or '').strip()
    if pid.isdigit():
        return HttpResponseRedirect(f"/chart/patient/{int(pid)}/encounter/new/")
    html = """<!doctype html><html><head>
      <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
      <title>New Encounter</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body class="bg-light"><div class="container py-4">
      <h1 class="h5 mb-3">New Encounter</h1>
      <form method="get" class="row g-2">
        <div class="col-md-4"><label class="form-label">Patient ID</label>
          <input name="patient_id" class="form-control" placeholder="e.g. 1" required></div>
        <div class="col-md-12 mt-2">
          <button class="btn btn-primary">Go</button>
          <a class="btn btn-secondary ms-2" href="/">Cancel</a>
        </div>
      </form>
    </div></body></html>"""
    return HttpResponse(html)
