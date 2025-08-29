"""
X12 005010X222A1 837P skeleton builder (validator-friendly baseline).
This is NOT production-complete, but it lays out proper loops/segments with
safe placeholders where your data is incomplete.
"""
from datetime import datetime
from typing import List
from decimal import Decimal
from django.conf import settings
import os

def _now():
    dt = datetime.utcnow()
    return dt.strftime("%Y%m%d"), dt.strftime("%H%M")

def _ns(v):
    """Normalize to string safely (handles Decimal, int, None)."""
    return "" if v is None else str(v).strip()

def _money(x) -> str:
    try:
        return f"{Decimal(x):.2f}"
    except Exception:
        return "0.00"

def build_837p_segments(claim, patient, coverage, payer_name: str, control="0001") -> List[str]:
    ymd, hms = _now()
    sender_id = "SENDERID"
    receiver_id = "RECEIVERID"

    segs = []
    # Interchange/Functional/Transaction headers
    segs.append(f"ISA*00*          *00*          *ZZ*{sender_id:<15}*ZZ*{receiver_id:<15}*{ymd[2:]}*{hms}*^*00501*000000905*0*T*:~")
    segs.append(f"GS*HC*{sender_id}*{receiver_id}*{ymd}*{hms}*1*X*005010X222A1~")
    segs.append(f"ST*837*{control}*005010X222A1~")
    segs.append(f"BHT*0019*00*{control}*{ymd}*{hms}*CH~")

    # 1000A Submitter
    submitter_name = "Demo Submitter"
    submitter_id = "123456789"
    segs.append(f"NM1*41*2*{submitter_name}*****46*{submitter_id}~")
    segs.append("PER*IC*SUBMITTER CONTACT*TE*5551231234*EM*submitter@example.com~")

    # 1000B Receiver
    segs.append(f"NM1*40*2*{receiver_id}*****46*RECEIVER~")

    # 2000A Billing Provider HL
    hl1 = 1
    segs.append(f"HL*{hl1}**20*1~")
    segs.append("PRV*BI*PXC*207Q00000X~")  # taxonomy placeholder
    # 2010AA Billing Provider
    bp_name = "Sample Clinic"
    bp_npi = "1234567890"
    segs.append(f"NM1*85*2*{bp_name}*****XX*{bp_npi}~")
    segs.append("N3*100 Medical Way~")
    segs.append("N4*Chicago*IL*60601~")
    segs.append("REF*EI*123456789~")  # TIN placeholder

    # 2000B Subscriber HL
    hl2 = hl1 + 1
    segs.append(f"HL*{hl2}*{hl1}*22*0~")
    segs.append("SBR*P*18*******MC~")  # primary, self; product type placeholder

    # 2010BA Subscriber (patient)
    last = _ns(getattr(patient, "last_name", "")) or "DOE"
    first = _ns(getattr(patient, "first_name", "")) or "JOHN"
    dob = getattr(patient, "date_of_birth", None)
    dob_str = dob.strftime("%Y%m%d") if dob else "19800101"
    gender = "U"
    member_id = _ns(getattr(coverage, "member_id", "")) or "MEMBERID"
    segs.append(f"NM1*IL*1*{last}*{first}****MI*{member_id}~")
    segs.append("N3*1 MAIN ST~")
    segs.append("N4*CHICAGO*IL*60601~")
    segs.append(f"DMG*D8*{dob_str}*{gender}~")

    # 2010BB Payer
    payer_disp = _ns(payer_name) or "PAYER"
    segs.append(f"NM1*PR*2*{payer_disp}*****PI*PAYERID~")

    # 2300 Claim
    total = _money(getattr(claim, "total_charge", "0"))
    pos = _ns(getattr(claim, "pos", "")) or "11"
    segs.append(f"CLM*{claim.id}*{total}***{pos}:11*Y*A*Y*I~")
    segs.append(f"REF*D9*{claim.id}~")  # patient control number

    # 2300 HI Diagnoses (max 12)
    dx_codes = list(claim.diagnoses.order_by("order").values_list("code", flat=True))[:12]
    if dx_codes:
        parts = []
        for i, d in enumerate(dx_codes):
            dflat = (d or "").replace(".", "")
            qual = "ABK" if i == 0 else "ABF"
            parts.append(f"{qual}:{dflat}")
        segs.append("HI*" + "*".join(parts) + "~")

    # 2400 Service lines
    for i, ln in enumerate(claim.lines.all(), start=1):
        charge = _money(getattr(ln, "charge", "0"))
        units = str(getattr(ln, "units", "") or "1")
        cpt = _ns(getattr(ln, "cpt", "")) or "99213"
        segs.append(f"LX*{i}~")
        segs.append(f"SV1*HC:{cpt}*{charge}*UN*{units}***1~")
        segs.append(f"DTP*472*D8*{ymd}~")

    # Tail (SE count from ST..SE inclusive)
    st_idx = next(i for i, v in enumerate(segs) if v.startswith("ST*"))
    se_count = (len(segs) - st_idx) + 1  # +1 for SE we add now
    segs.append(f"SE*{se_count}*{control}~")
    segs.append("GE*1*1~")
    segs.append("IEA*1*000000905~")
    return segs

def write_837p_file(path: str, segs: List[str]) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(segs))
    return path

def build_and_write_837p(claim, patient, coverage, payer_name: str) -> str:
    ymd, hms = _now()
    fname = f"claim_{claim.id}_{ymd}{hms}.txt"
    outdir = getattr(settings, "EXPORTS_DIR", os.path.join(os.getcwd(), "exports", "edi"))
    path = os.path.join(outdir, fname)
    segs = build_837p_segments(claim, patient, coverage, payer_name)
    return write_837p_file(path, segs)
