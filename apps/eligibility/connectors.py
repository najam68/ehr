from dataclasses import dataclass, asdict
import hashlib, random

@dataclass
class EligibilityRequest:
    payer_id: str
    member_id: str
    patient_dob: str
    patient_name: str
    provider_npi: str
    tin: str
    dos: str
    service_types: list  # e.g., ["30","98","47"]

@dataclass
class EligibilityResponse:
    active: bool
    network_status: str  # IN_NETWORK/OUT_OF_NETWORK/UNKNOWN
    plan: dict           # {effective, termination, group}
    benefits: list       # [{category, copay, coinsurance, deductibleRemaining, authRequired}]
    notes: list
    raw: dict | None

SERVICE_MAP = {
  "98": "Office Visit", "1": "Medical Care", "47": "Hospital",
  "88": "Pharmacy", "86": "Emergency", "33": "Chiropractic", "30": "Plan"
}

def _seed(member_id: str):
    return int(hashlib.sha256(member_id.encode()).hexdigest(), 16) % (10**8)

def stub_verify(req: EligibilityRequest) -> EligibilityResponse:
    rnd = random.Random(_seed(req.member_id))
    active = rnd.random() > 0.07  # ~93% active
    in_net = rnd.random() > 0.15
    ded_total = rnd.choice([500, 1000, 2000, 3000])
    ded_used = rnd.randint(0, ded_total)
    coins = rnd.choice([0.1, 0.2, 0.3])
    copay_office = rnd.choice([0, 20, 30, 40, 50])
    benefits = []
    sts = req.service_types or ["30","98"]
    for st in sts:
        cat = SERVICE_MAP.get(st, f"Service {st}")
        auth = cat in {"MRI", "CT", "Hospital"} or st in {"47"}
        benefits.append({
          "category": cat,
          "copay": copay_office if cat=="Office Visit" else None,
          "coinsurance": coins,
          "deductibleRemaining": max(ded_total - ded_used, 0),
          "authRequired": auth,
        })
    notes = []
    if not in_net:
        notes.append("Provider appears out-of-network (simulated).")
    return EligibilityResponse(
      active=active,
      network_status="IN_NETWORK" if in_net else "OUT_OF_NETWORK",
      plan={"effective":"2025-01-01","termination": None, "group":"SIM123"},
      benefits=benefits,
      notes=notes,
      raw={"mode":"SIMULATED"}
    )
