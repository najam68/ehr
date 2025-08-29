from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any
from django.conf import settings
from .models import Claim, ClaimLine, MUE, NCCIEdit
from apps.patients.models import Coverage
from .scrubber import run_scrubber

FLAGS = getattr(settings, "AUTOFIX_FLAGS", {})

def _dec(x):
    try:
        return Decimal(str(x))
    except Exception:
        return None

def _sum_line_total(claim: Claim) -> Decimal:
    total = Decimal("0")
    for ln in claim.lines.all():
        u = _dec(ln.units) or Decimal("0")
        ch = _dec(ln.charge) or Decimal("0")
        total += u * ch
    return total

def propose_changes(claim: Claim) -> List[Dict[str, Any]]:
    """
    Build a list of proposed changes to fix common ERROR/WARN findings.
    """
    changes: List[Dict[str, Any]] = []
    run_scrubber(claim)  # refresh findings before proposing

    # Lookup helpers
    mue_map = {m.code: m.max_units for m in MUE.objects.all()}
    pairs = list(NCCIEdit.objects.all().values("code_primary","code_secondary","edit_type"))

    # 1) POS_CONFLICT -> POS=11 if office E/M present
    has_office_em = False
    for ln in claim.lines.all():
        try:
            n = int(ln.cpt)
            if 99202 <= n <= 99215:
                has_office_em = True
                break
        except Exception:
            pass
    if FLAGS.get("POS_CONFLICT", True) and has_office_em and claim.pos != "11":
        changes.append({
            "action": "update_claim", "field": "pos",
            "from": claim.pos, "to": "11", "reason": "POS_CONFLICT"
        })

    # 2) MUE_EXCEEDED -> cap units
    for ln in claim.lines.all():
        lim = mue_map.get(ln.cpt)
        units = _dec(ln.units)
        if FLAGS.get("MUE_EXCEEDED", True) and lim is not None and units is not None and units > lim:
            changes.append({
                "action": "update_line", "line_id": ln.id, "field": "units",
                "from": str(units), "to": str(lim), "reason": "MUE_EXCEEDED"
            })

    # 3) NCCI_PAIR -> remove secondary
    codes_on_claim = [ln.cpt for ln in claim.lines.all()]
    if FLAGS.get("NCCI_PAIR", True):
        for p in pairs:
            if p["code_primary"] in codes_on_claim and p["code_secondary"] in codes_on_claim:
                sec = next((ln for ln in claim.lines.all() if ln.cpt == p["code_secondary"]), None)
                if sec:
                    changes.append({
                        "action": "delete_line", "line_id": sec.id,
                        "reason": f"NCCI_PAIR {p['code_primary']} vs {p['code_secondary']} ({p['edit_type']})"
                    })

    # 4) REQUIRED_PAYER_NAME -> use latest coverage payer
    if FLAGS.get("REQUIRED_PAYER_NAME", True) and not (claim.payer_name or "").strip():
        cov = Coverage.objects.filter(patient_id=claim.patient_id).order_by("-effective_date","-id").first()
        if cov and cov.payer_name:
            changes.append({
                "action": "update_claim", "field": "payer_name",
                "from": claim.payer_name, "to": cov.payer_name, "reason": "REQUIRED_PAYER_NAME"
            })

    # 5) TOTAL_CHARGE_ZERO -> set to sum(lines)
    try:
        cur_total = _dec(claim.total_charge) or Decimal("0")
    except InvalidOperation:
        cur_total = Decimal("0")
    new_total = _sum_line_total(claim)
    if FLAGS.get("TOTAL_CHARGE_ZERO", True) and new_total > 0 and cur_total <= 0:
        changes.append({
            "action": "update_claim", "field": "total_charge",
            "from": str(cur_total), "to": str(new_total), "reason": "TOTAL_CHARGE_ZERO"
        })

    return changes

def apply_changes(claim: Claim, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply the proposed changes to DB and re-scrub.
    """
    committed = []
    for ch in changes:
        act = ch.get("action")
        if act == "update_claim":
            field = ch["field"]
            setattr(claim, field, ch["to"])
            committed.append(ch)
        elif act == "update_line":
            ln = ClaimLine.objects.filter(id=ch["line_id"], claim=claim).first()
            if not ln:
                continue
            setattr(ln, ch["field"], ch["to"])
            ln.save()
            committed.append(ch)
        elif act == "delete_line":
            ln = ClaimLine.objects.filter(id=ch["line_id"], claim=claim).first()
            if not ln:
                continue
            ln.delete()
            committed.append(ch)
    claim.save()
    run_scrubber(claim)
    return committed
