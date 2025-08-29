from apps.scheduling.models import Appointment
from django.utils.timezone import now
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import make_aware
from datetime import datetime, time, timedelta

from .models import Appointment
from apps.patients.models import Patient
from apps.registry.models import Provider, Facility

@require_GET
def appointments_day_json(request):
    """List appointments for a given date (UTC-aware) with optional provider/facility filters."""
    date_str = request.GET.get('date') or ''
    d = parse_date(date_str)
    if not d:
        return JsonResponse({'ok': False, 'error': 'date=YYYY-MM-DD required'}, status=400)
    start_dt = make_aware(datetime.combine(d, time.min))
    end_dt = start_dt + timedelta(days=1)
    qs = Appointment.objects.filter(start__gte=start_dt, start__lt=end_dt)
    pid = request.GET.get('provider_id') or ''
    fid = request.GET.get('facility_id') or ''
    if pid.isdigit():
        qs = qs.filter(provider_id=int(pid))
    if fid.isdigit():
        qs = qs.filter(facility_id=int(fid))
    items = []
    for a in qs.order_by('start','provider_id'):
        items.append({
            'id': a.id,
            'patient_id': a.patient_id,
            'provider_id': a.provider_id,
            'facility_id': a.facility_id,
            'start': a.start.isoformat(),
            'end': a.end.isoformat(),
            'status': a.status,
            'reason': a.reason,
        })
    return JsonResponse({'ok': True, 'count': len(items), 'items': items})

@csrf_exempt
@require_POST
def appointment_new_json(request):
    """Create appointment: patient_id, provider_id, facility_id, start, end, status?, reason?, notes?"""
    import json
    try:
        p = json.loads(request.body.decode() or '{}')
    except Exception:
        return JsonResponse({'ok': False, 'error': 'bad-json'}, status=400)
    try:
        pat = Patient.objects.get(pk=int(p['patient_id']))
        prov = Provider.objects.get(pk=int(p['provider_id']))
        fac  = Facility.objects.get(pk=int(p['facility_id']))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'bad-ids'}, status=400)
    st = parse_datetime(p.get('start') or '')
    en = parse_datetime(p.get('end') or '')
    if not (st and en):
        return JsonResponse({'ok': False, 'error': 'start/end ISO datetimes required'}, status=400)
    ap = Appointment.objects.create(
        patient=pat, provider=prov, facility=fac,
        start=st, end=en,
        status=(p.get('status') or 'SCHEDULED')[:12],
        reason=p.get('reason') or '',
        notes=p.get('notes') or '',
    )
    return JsonResponse({'ok': True, 'id': ap.id})

@csrf_exempt
@require_POST
def appointment_update_json(request, appt_id: int):
    """Update minimal fields: start, end, status, reason, notes."""
    import json
    ap = Appointment.objects.filter(pk=appt_id).first()
    if not ap:
        return JsonResponse({'ok': False, 'error': 'not-found'}, status=404)
    try:
        p = json.loads(request.body.decode() or '{}')
    except Exception:
        return JsonResponse({'ok': False, 'error': 'bad-json'}, status=400)
    if 'start' in p:
        st = parse_datetime(p.get('start') or '')
        if st: ap.start = st
    if 'end' in p:
        en = parse_datetime(p.get('end') or '')
        if en: ap.end = en
    if 'status' in p:
        ap.status = (p.get('status') or ap.status)[:12]
    if 'reason' in p:
        ap.reason = p.get('reason') or ''
    if 'notes' in p:
        ap.notes = p.get('notes') or ''
    ap.save()
    return JsonResponse({'ok': True, 'id': ap.id})


def _ensure_encounter(ap: Appointment):
    from apps.chart.models import Encounter
    if ap.encounter_id:
        return ap.encounter
    enc = Encounter.objects.create(patient=ap.patient, status='OPEN', reason=ap.reason or 'Visit')
    ap.encounter = enc
    ap.save(update_fields=['encounter'])
    return enc

def _ensure_superbill(ap: Appointment):
    from apps.billing.models import Superbill
    if ap.superbill_id:
        return ap.superbill
    sb = Superbill.objects.create(patient=ap.patient, status='DRAFT', total=0)
    ap.superbill = sb
    ap.save(update_fields=['superbill'])
    return sb


@csrf_exempt
@require_POST
def appointment_checkin_json(request, appt_id: int):
    """POST {coverage_id?} -> set status CHECKIN; optionally update Coverage eligibility."""
    import json
    try:
        ap = Appointment.objects.select_related('patient','provider','facility').get(pk=appt_id)
    except Appointment.DoesNotExist:
        return JsonResponse({"ok": False, "error":"not-found"}, status=404)

    payload = {}
    try:
        if request.body:
            payload = json.loads(request.body.decode() or "{}")
    except Exception:
        payload = {}

    cov_id = payload.get("coverage_id")
    if cov_id:
        try:
            from apps.registry.models import Coverage
            cov = Coverage.objects.filter(pk=int(cov_id)).first()
            if cov and cov.patient_id == ap.patient_id:
                # same logic as other eligibility: simple status based on dates + member_id
                from datetime import date
                today = date.today()
                has_member = bool(cov.member_id)
                window_ok  = ((cov.effective_start is None or cov.effective_start <= today) and (cov.effective_end is None or cov.effective_end >= today))
                cov.eligibility_status = "ACTIVE" if (has_member and window_ok) else ("INACTIVE" if not window_ok else "NEEDS_UPDATE")
                cov.eligibility_last_checked = now()
                cov.eligibility_payload = {"source":"checkin","checked_at": cov.eligibility_last_checked.isoformat()}
                cov.save(update_fields=["eligibility_status","eligibility_last_checked","eligibility_payload"])
        except Exception:
            pass

    ap.status = "CHECKIN"
    ap.save(update_fields=["status"])
    return JsonResponse({"ok": True, "id": ap.id, "status": ap.status})


@csrf_exempt
@require_POST
def appointment_start_json(request, appt_id: int):
    try:
        ap = Appointment.objects.select_related('patient').get(pk=appt_id)
    except Appointment.DoesNotExist:
        return JsonResponse({"ok": False, "error":"not-found"}, status=404)
    enc = _ensure_encounter(ap)
    ap.status = "INROOM"
    ap.save(update_fields=["status"])
    return JsonResponse({"ok": True, "id": ap.id, "status": ap.status, "encounter_id": enc.id})


@csrf_exempt
@require_POST
def appointment_create_superbill_json(request, appt_id: int):
    try:
        ap = Appointment.objects.select_related('patient').get(pk=appt_id)
    except Appointment.DoesNotExist:
        return JsonResponse({"ok": False, "error":"not-found"}, status=404)
    sb = _ensure_superbill(ap)
    return JsonResponse({"ok": True, "id": ap.id, "superbill_id": sb.id})


@require_GET
def appointment_summary_json(request, appt_id: int):
    ap = Appointment.objects.filter(pk=appt_id).select_related('patient','provider','facility').first()
    if not ap:
        return JsonResponse({"ok": False, "error":"not-found"}, status=404)
    out = {
        "id": ap.id,
        "patient_id": ap.patient_id,
        "provider_id": ap.provider_id,
        "facility_id": ap.facility_id,
        "start": ap.start.isoformat() if ap.start else None,
        "end": ap.end.isoformat() if ap.end else None,
        "status": ap.status,
        "reason": ap.reason,
        "encounter_id": ap.encounter_id,
        "superbill_id": ap.superbill_id,
    }
    return JsonResponse({"ok": True, **out})
