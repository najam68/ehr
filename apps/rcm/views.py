from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.rcm.models import Rule
from apps.billing.models import Superbill, SuperbillLine

def _line_dict(ln: SuperbillLine):
    return {
        "code": ln.code,
        "mods": [m for m in [ln.mod1,ln.mod2,ln.mod3,ln.mod4] if m],
        "pos": ln.pos,
        "dx_ptrs": list(ln.dx_ptrs or []),
        "units": ln.units,
        "charge": float(ln.charge or 0),
    }

def _evaluate(sb: Superbill):
    # assemble claim context
    hdr = {
        "patient_id": getattr(sb,'patient_id',None),
        "sex": "", "age": None,  # placeholders (wire later to demographics/DOB)
        "payer_id": "",          # placeholder; wire to Coverage later
    }
    # legacy dx on header
    dx_list = list(getattr(sb,'icd_codes',[]) or [])
    lines = []
    issues = []
    for ln in SuperbillLine.objects.filter(superbill=sb).order_by('id'):
        lines.append(_line_dict(ln))

    # run rules (coarse MVP)
    rules = Rule.objects.filter(active=True)
    for r in rules:
        # scope
        if r.scope == 'CLAIM':
            # dx constraints
            if r.dx_allowed and any(dx not in r.dx_allowed for dx in dx_list if dx):
                issues.append({"severity": r.severity, "scope": "CLAIM", "rule": r.name, "msg": r.message or "DX not allowed"})
            if r.dx_required_any and not any(dx in r.dx_required_any for dx in dx_list if dx):
                issues.append({"severity": r.severity, "scope": "CLAIM", "rule": r.name, "msg": r.message or "Required DX missing"})
        else:
            # LINE rules
            for idx, ln in enumerate(lines, start=1):
                if r.cpt_code and r.cpt_code != ln["code"]:
                    continue
                if r.pos_allowed and ln["pos"] and ln["pos"] not in r.pos_allowed:
                    issues.append({"severity": r.severity, "scope":"LINE", "line": idx, "rule": r.name, "msg": r.message or f"POS {ln['pos']} not allowed"})
                if r.modifiers_required:
                    missing = [m for m in r.modifiers_required if m not in ln["mods"]]
                    if missing:
                        issues.append({"severity": r.severity, "scope":"LINE", "line": idx, "rule": r.name, "msg": r.message or f"Missing modifier(s): {', '.join(missing)}"})
                if r.dx_required_any:
                    # map dx_ptrs (1-based) to header dx list
                    ptr_any = any( (p>0 and p<=len(dx_list) and dx_list[p-1] in r.dx_required_any) for p in ln["dx_ptrs"] )
                    if not ptr_any:
                        issues.append({"severity": r.severity, "scope":"LINE", "line": idx, "rule": r.name, "msg": r.message or "Required DX pointer missing"})
    return {"header": hdr, "lines": lines, "dx": dx_list, "issues": issues}

@require_GET
def rules_check_superbill(request, superbill_id:int):
    sb = Superbill.objects.filter(pk=superbill_id).first()
    if not sb:
        return JsonResponse({"ok": False, "error": "not-found"}, status=404)
    out = _evaluate(sb)
    return JsonResponse({"ok": True, **out})
