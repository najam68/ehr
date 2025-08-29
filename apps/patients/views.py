from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.utils import timezone

from .forms import PatientIntakeForm
from .models import Patient, EmergencyContact
from apps.registry.models import Coverage, Payer


def _save_coverages(patient, data):
    # PRIMARY
    payer_id = (data.get('payer_id') or '').strip()
    if payer_id.isdigit():
        Coverage.objects.create(
            patient=patient, payer=Payer.objects.get(pk=int(payer_id)),
            plan_name=(data.get('plan_name') or '').strip(),
            member_id=(data.get('member_id') or '').strip(),
            group_number=(data.get('group_number') or '').strip(),
            relationship=(data.get('cov_relationship') or 'self').strip() or 'self',
            is_primary=True, priority=1, cob_order=1,
            rx_bin=(data.get('rx_bin') or '').strip(),
            rx_pcn=(data.get('rx_pcn') or '').strip(),
            rx_group=(data.get('rx_group') or '').strip(),
            rx_id=(data.get('rx_id') or '').strip(),
            effective_start=(data.get('effective_start') or None),
            effective_end=(data.get('effective_end') or None),
        )
    # SECONDARY (only if payer selected or any secondary field present)
    sec_payer_id = (data.get('sec_payer_id') or '').strip()
    sec_any = any((data.get(k) for k in (
        'sec_plan_name','sec_member_id','sec_group_number','sec_relationship',
        'sec_subscriber_name','sec_subscriber_dob','sec_subscriber_phone',
        'sec_rx_bin','sec_rx_pcn','sec_rx_group','sec_rx_id',
        'sec_effective_start','sec_effective_end')))
    if sec_payer_id.isdigit() or sec_any:
        if sec_payer_id.isdigit():
            Coverage.objects.create(
                patient=patient, payer=Payer.objects.get(pk=int(sec_payer_id)),
                plan_name=(data.get('sec_plan_name') or '').strip(),
                member_id=(data.get('sec_member_id') or '').strip(),
                group_number=(data.get('sec_group_number') or '').strip(),
                relationship=(data.get('sec_relationship') or 'self').strip() or 'self',
                is_primary=False, priority=2, cob_order=2,
                subscriber_name=(data.get('sec_subscriber_name') or '').strip(),
                subscriber_dob=(data.get('sec_subscriber_dob') or None),
                subscriber_phone=(data.get('sec_subscriber_phone') or '').strip(),
                rx_bin=(data.get('sec_rx_bin') or '').strip(),
                rx_pcn=(data.get('sec_rx_pcn') or '').strip(),
                rx_group=(data.get('sec_rx_group') or '').strip(),
                rx_id=(data.get('sec_rx_id') or '').strip(),
                effective_start=(data.get('sec_effective_start') or None),
                effective_end=(data.get('sec_effective_end') or None),
            )


def patient_registration_new(request):
    if request.method == "POST":
        form = PatientIntakeForm(request.POST)
        if form.is_valid():
            p = form.save()
            data = request.POST
            # Emergency Contact (optional)
            ec_name = (data.get('ec_name') or '').strip()
            if ec_name:
                EmergencyContact.objects.create(
                    patient=p,
                    name=ec_name,
                    relationship=(data.get('ec_relationship') or '').strip(),
                    phone=(data.get('ec_phone') or '').strip(),
                    email=(data.get('ec_email') or '').strip(),
                )
            # Specialty dynamic fields -> extra_json
            spec_fields = {k[5:]: v for k,v in data.items() if k.startswith('spec_')}
            try: p.extra_json = p.extra_json or {}
            except Exception: p.extra_json = {}
            p.extra_json['specialty_fields'] = spec_fields
            p.save(update_fields=['extra_json'])
            # Coverages
            _save_coverages(p, data)
            return HttpResponseRedirect(f"/registry/patient/{p.id}/")
    else:
        form = PatientIntakeForm()
    return render(request, "patients/registration.html", {"form": form})


def patient_registration_edit(request, patient_id: int):
    p = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        form = PatientIntakeForm(request.POST, instance=p)
        if form.is_valid():
            p = form.save()
            data = request.POST
            # Update specialty dynamic values
            spec_fields = {k[5:]: v for k,v in data.items() if k.startswith('spec_')}
            try: p.extra_json = p.extra_json or {}
            except Exception: p.extra_json = {}
            p.extra_json['specialty_fields'] = spec_fields
            p.save(update_fields=['extra_json'])
            # (Optional) you can allow editing coverages here later
            return HttpResponseRedirect(f"/registry/patient/{p.id}/")
    else:
        form = PatientIntakeForm(instance=p)
    return render(request, "patients/registration.html", {"form": form, "edit_mode": True, "patient_id": p.id})


# Compatibility wrappers (older routes)
def patient_intake_new(request):        # uses same form/template
    return patient_registration_new(request)

def patient_intake_edit(request, patient_id: int):
    return patient_registration_edit(request, patient_id)
