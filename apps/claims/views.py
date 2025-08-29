from django.http import HttpResponse

def _html_page(title, body):
    return HttpResponse(
        "<!doctype html><html><head>"
        "<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>"
        f"<title>{title}</title></head><body class='bg-light'>"
        "<div class='container py-4'>"
        f"<h1 class='h4 mb-3'>{title}</h1>{body}"
        "</div></body></html>"
    )

def claims_list(request):
    rows = []
    total = 0
    err = None
    tried = []
    # Try common model names in your repo
    candidates = [
        ("apps.claims.models", "Claim"),
        ("apps.claims.models", "InsuranceClaim"),
    ]
    model = None
    for mod, cls in candidates:
        try:
            m = __import__(mod, fromlist=[cls])
            model = getattr(m, cls)
            break
        except Exception as e:
            tried.append(f"{mod}.{cls}: {e}")
            continue
    if model:
        try:
            qs = model.objects.all().order_by('id')[:50]
            total = model.objects.count()
            for c in qs:
                status = getattr(c, 'status', '')
                patient_id = getattr(c, 'patient_id', '')
                amount = getattr(c, 'amount', '') or getattr(c, 'total', '')
                rows.append(f"<tr><td>{c.pk}</td><td>{patient_id}</td><td>{status}</td><td>{amount}</td></tr>")
        except Exception as e:
            err = str(e)
    if rows:
        table = (
            "<div class='table-responsive'><table class='table table-sm table-striped'>"
            "<thead><tr><th>ID</th><th>Patient</th><th>Status</th><th>Amount</th></tr></thead>"
            "<tbody>" + "".join(rows) + "</tbody></table></div>"
            f"<p class='text-muted'>Showing up to 50 of {total} claims.</p>"
        )
    else:
        table = "<div class='alert alert-warning'>No claims found or model not importable.</div>"
        if err:
            table += f"<pre class='small text-danger'>{err}</pre>"
        if tried:
            table += "<details class='mt-2'><summary>Import attempts</summary><pre class='small'>" + "\n".join(tried) + "</pre></details>"
    return _html_page("Claims", table)
