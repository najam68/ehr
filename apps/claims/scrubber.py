from decimal import Decimal, InvalidOperation
from .models import ScrubFinding, Claim, MUE, NCCIEdit

def _add(claim, code, severity, message, line=None, suggestion=""):
    ScrubFinding.objects.create(
        claim=claim, code=code, severity=severity,
        message=message, line=line, suggestion=suggestion
    )

def _to_dec(x):
    try:
        return Decimal(str(x))
    except InvalidOperation:
        return None

def run_scrubber(claim: Claim):
    """Starter rules + MUE/NCCI lookups."""
    claim.findings.all().delete()

    # R1: required payer
    if not (claim.payer_name or "").strip():
        _add(claim, "REQUIRED_PAYER_NAME", "ERROR", "Payer name is required on claim.")

    # R2: POS vs Office E/M mismatch (simple)
    def _is_office_em(cpt: str):
        try:
            n = int(cpt)
            return 99202 <= n <= 99215
        except Exception:
            return False
    if claim.pos != "11":  # 11 = Office
        for ln in claim.lines.all():
            if _is_office_em(ln.cpt):
                _add(claim, "POS_CONFLICT", "ERROR",
                     f"Office E/M {ln.cpt} cannot be used with POS {claim.pos}.",
                     line=ln, suggestion="Use appropriate E/M code or correct POS.")

    # R3: TOTAL_CHARGE > 0
    total = _to_dec(claim.total_charge)
    if total is None or total <= 0:
        _add(claim, "TOTAL_CHARGE_ZERO", "WARN",
             "Total charge is zero or invalid.", suggestion="Set a positive total_charge.")

    # R4: MUE check (per code)
    mue_map = {m.code: m.max_units for m in MUE.objects.all()}
    for ln in claim.lines.all():
        lim = mue_map.get(ln.cpt)
        units = _to_dec(ln.units)
        if lim is not None and units is not None and units > lim:
            _add(claim, "MUE_EXCEEDED", "ERROR",
                 f"Units {units} for {ln.cpt} exceed limit {lim}.",
                 line=ln, suggestion=f"Reduce to <= {lim} or split per policy.")

    # R5: NCCI mutual edits (same-claim pairs)
    codes_on_claim = [ln.cpt for ln in claim.lines.all()]
    pairs = list(NCCIEdit.objects.all().values("code_primary","code_secondary","edit_type"))
    for p in pairs:
        if p["code_primary"] in codes_on_claim and p["code_secondary"] in codes_on_claim:
            _add(claim, "NCCI_PAIR", "ERROR",
                 f"{p['code_primary']} conflicts with {p['code_secondary']} ({p['edit_type']}).",
                 suggestion="Remove one code or apply appropriate modifier per policy.")

    return list(claim.findings.values("code","severity","message","suggestion"))
