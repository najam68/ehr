from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from .models import DisclosureLog, SecurityEvent

@require_GET
def health(request):
    # Placeholder: extend with env assertions (TLS, SECURE_ settings on)
    return JsonResponse({"ok": True, "hipaa_mode": bool(getattr(request, 'hipaa_mode', False))})

@require_GET
def disclosures_recent(request):
    limit = int(request.GET.get('limit', '50'))
    rows = DisclosureLog.objects.order_by('-when')[:limit]
    items = [{"patient_id": r.patient_id, "purpose": r.purpose, "recipient": r.recipient,
              "when": r.when.isoformat(), "minimum_necessary": r.minimum_necessary, "meta": r.meta} for r in rows]
    return JsonResponse({"ok": True, "count": len(items), "items": items})

@require_POST
@csrf_exempt
def disclosures_log(request):
    # Just a placeholder – accept a minimal JSON and log it.
    import json
    try:
        p = json.loads(request.body.decode() or "{}")
        from .utils import log_disclosure
        log_disclosure(int(p.get("patient_id",0)), p.get("purpose",""), p.get("recipient",""), bool(p.get("minimum_necessary",True)), p.get("meta") or {})
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

@require_GET
def security_recent(request):
    limit = int(request.GET.get('limit', '50'))
    rows = SecurityEvent.objects.order_by('-when')[:limit]
    items = [{"severity": r.severity, "event_type": r.event_type, "when": r.when.isoformat(),
              "who": getattr(r.who,'username',None), "message": r.message, "meta": r.meta} for r in rows]
    return JsonResponse({"ok": True, "count": len(items), "items": items})


@require_POST
@csrf_exempt
def export_start(request):
    """Start a PHI export job (skeleton). Body: {scope: 'patient-chart'|'billing'|'full-phi', patient_id?} """
    import json
    from django.utils.timezone import now
    from .models import ExportJob
    try:
        p = json.loads(request.body.decode() or "{}")
        scope = (p.get("scope") or "").strip()
        patient_id = p.get("patient_id")
        if not scope:
            return JsonResponse({"ok": False, "error": "scope required"}, status=400)
        job = ExportJob.objects.create(scope=scope, patient_id=patient_id or None,
                                       requested_by=getattr(request,'user',None),
                                       status='QUEUED', meta={"request_id": getattr(request,'request_id',None)})
        return JsonResponse({"ok": True, "job_id": job.id, "status": job.status})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


@require_GET
def export_status(request, job_id:int):
    from .models import ExportJob
    job = ExportJob.objects.filter(pk=job_id).first()
    if not job:
        return JsonResponse({"ok": False, "error": "not-found"}, status=404)
    return JsonResponse({"ok": True, "job_id": job.id, "status": job.status, "location": job.location, "meta": job.meta})


@require_POST
@csrf_exempt
def export_complete(request):
    """Mark job COMPLETE and log disclosure; Body: {job_id:int, location:'url-or-path', recipient:'patient'|'third-party'|'payer', purpose:'patient-request'|...} """
    import json
    from django.utils.timezone import now
    from .models import ExportJob
    from .utils import log_disclosure
    try:
        p = json.loads(request.body.decode() or "{}")
        job_id = int(p.get("job_id"))
        location = (p.get("location") or '').strip()
        recipient = (p.get("recipient") or 'patient').strip()
        purpose = (p.get("purpose") or 'patient-request').strip()
    except Exception as e:
        return JsonResponse({"ok": False, "error":"bad json"}, status=400)
    job = ExportJob.objects.filter(pk=job_id).first()
    if not job:
        return JsonResponse({"ok": False, "error":"not-found"}, status=404)
    job.status = 'COMPLETED'
    job.location = location
    job.completed_at = now()
    job.save(update_fields=['status','location','completed_at'])
    # disclosure log (placeholder)
    if job.patient_id:
        log_disclosure(job.patient_id, purpose, recipient, minimum_necessary=True, meta={"job_id": job.id, "location": location})
    return JsonResponse({"ok": True, "job_id": job.id, "status": job.status, "location": job.location})
