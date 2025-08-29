
# apps/fhir_api/resources.py
# Defensive “DB → FHIR dict” mappers (no strict validation, no UI side effects)
# Only include fields we actually have to avoid validation noise.

def _clean(s):
    return (s or "").strip()

def patient_to_fhir(patient):
    last = _clean(getattr(patient, "last_name", ""))
    first = _clean(getattr(patient, "first_name", ""))
    name = {"use":"official"}
    if last: name["family"] = last
    if first: name["given"] = [first]
    addr = {}
    aj = getattr(patient, "address_json", None) or getattr(patient, "address", None) or {}
    if isinstance(aj, dict):
        if _clean(aj.get("street")): addr["line"] = [_clean(aj.get("street"))]
        if _clean(aj.get("city")): addr["city"] = _clean(aj.get("city"))
        if _clean(aj.get("state")): addr["state"] = _clean(aj.get("state"))
        if _clean(aj.get("postal_code")): addr["postalCode"] = _clean(aj.get("postal_code"))
    res = {
        "resourceType":"Patient",
        "id": str(getattr(patient, "id", "")) or None,
    }
    if name.keys()!= {"use"}: res["name"] = [name]
    g = _clean(getattr(patient, "gender","")).lower()
    if g in ("male","female","other","unknown"): res["gender"]=g
    dob = getattr(patient,"dob",None)
    if dob: res["birthDate"] = dob.isoformat()
    if addr: res["address"] = [addr]
    return res


def practitioner_to_fhir(provider):
    def _clean(v): return (v or '').strip()
    last = _clean(getattr(provider,'last_name',''))
    first = _clean(getattr(provider,'first_name',''))
    name = {'use':'official'}
    if last: name['family'] = last
    if first: name['given'] = [first]
    res = {'resourceType':'Practitioner','id': str(getattr(provider,'id','')) or None}
    if set(name.keys()) != {'use'}: res['name'] = [name]
    # identifiers (NPI + DEA if available)
    idents = []
    npi = _clean(getattr(provider,'npi',''))
    if npi: idents.append({'system':'http://hl7.org/fhir/sid/us-npi','value': npi})
    try:
        from apps.registry.models import ProviderDEARegistration
        dea = ProviderDEARegistration.objects.filter(provider=provider).order_by('-expiry').first()
        if dea and _clean(getattr(dea,'dea_number','')):
            idents.append({'system':'urn:dea','value': _clean(getattr(dea,'dea_number',''))})
    except Exception:
        pass
    if idents: res['identifier'] = idents
    # qualifications (state licenses)
    quals = []
    try:
        from apps.registry.models import ProviderLicense
        for lic in ProviderLicense.objects.filter(provider=provider).order_by('state'):
            quals.append({
                'identifier':[{'system':'urn:state-license','value': _clean(getattr(lic,'number',''))}],
                'code': {'text':'State License'},
                'period': {'end': str(getattr(lic,'expiry','') or '') or None},
                'issuer': {'display': _clean(getattr(lic,'state',''))}
            })
    except Exception:
        pass
    if quals: res['qualification'] = quals
    return res


def practitioner_role_to_fhir(provider, org_id=None):
    # Minimal role; if you have facility/organization, pass its id
    res = {
        "resourceType":"PractitionerRole",
        "id": f"role-{getattr(provider,'id','')}",
        "practitioner":{"reference": f"Practitioner/{getattr(provider,'id','')}"}
    }
    if org_id:
        res["organization"]={"reference": f"Organization/{org_id}"}
    taxonomy = _clean(getattr(provider,"taxonomy_code",""))
    if taxonomy:
        res["code"] = [{"coding":[{"system":"http://nucc.org/provider-taxonomy","code":taxonomy}]}]
    return res

def organization_from_payer(payer):
    res = {"resourceType":"Organization","id": str(getattr(payer,"id","")) or None,"name":_clean(getattr(payer,"name",""))}
    pid = _clean(getattr(payer,"payer_id",""))
    if pid:
        res["identifier"]=[{"system":"urn:oid:2.16.840.1.113883.3.18.7","value":pid}]  # example system
    return res

def coverage_to_fhir(cov):
    res = {
        "resourceType":"Coverage",
        "id": str(getattr(cov,"id","")) or None,
        "status": "active" if getattr(cov,"is_primary",False) else "unknown",
        "beneficiary": {"reference": f"Patient/{getattr(cov,'patient_id','')}"},
        "payor":[{"reference": f"Organization/{getattr(cov,'payer_id','')}"}],
        "class":[]
    }
    if _clean(getattr(cov,"plan_name","")):
        res["class"].append({"type":{"text":"plan"},"value":_clean(getattr(cov,"plan_name",""))})
    mid = _clean(getattr(cov,"member_id",""))
    if mid:
        res["identifier"]=[{"system":"urn:member-id","value":mid}]
    return res

def encounter_to_fhir(enc):
    # Minimal Encounter; status inferred from your model (default finished)
    status = _clean(getattr(enc,"status","")).lower()
    if status not in ("planned","in-progress","finished","cancelled"):
        status = "finished"
    res = {
        "resourceType":"Encounter",
        "id": str(getattr(enc,"id","")) or None,
        "status": status,
        "subject": {"reference": f"Patient/{getattr(enc,'patient_id','')}"}
    }
    return res

def documentreference_soap(enc, soap):
    # Text-only SOAP note as DocumentReference
    text = []
    if soap:
        for k in ("subjective","objective","assessment","plan"):
            v = _clean(getattr(soap,k,""))
            if v: text.append(k.upper()+":\\n"+v)
    content = "\\n\\n".join(text) or "SOAP note"
    res = {
        "resourceType":"DocumentReference",
        "id": f"docref-soap-{getattr(enc,'id','')}",
        "status":"current",
        "type":{"text":"SOAP Note"},
        "subject":{"reference": f"Patient/{getattr(enc,'patient_id','')}"},
        "content":[{"attachment":{"contentType":"text/plain","data": content.encode('utf-8').hex()}}]  # hex; client can decode
    }
    return res

def claim_from_superbill(sb):
    # Very minimal Claim from a Superbill
    patient_id = getattr(sb,'patient_id',None)
    icds = list(getattr(sb,'icd_codes',[]) or [])
    cpts = list(getattr(sb,'cpt_codes',[]) or [])
    total = float(getattr(sb,'total',0) or 0)
    res = {
        "resourceType":"Claim",
        "id": str(getattr(sb,'id','')) or None,
        "status":"active",
        "type":{"coding":[{"system":"http://terminology.hl7.org/CodeSystem/claim-type","code":"professional"}]},
        "use":"claim",
        "patient":{"reference": f"Patient/{patient_id}"} if patient_id else {"display":"Unknown"},
        "priority":{"coding":[{"system":"http://terminology.hl7.org/CodeSystem/processpriority","code":"normal"}]},
        "diagnosis":[],
        "item":[],
        "total":{"value": round(total,2), "currency":"USD"}
    }
    for i, icd in enumerate(icds):
        if icd:
            res["diagnosis"].append({"sequence":i+1,"diagnosisCodeableConcept":{"coding":[{"system":"http://hl7.org/fhir/sid/icd-10-cm","code":icd}]}})
    for j, cpt in enumerate(cpts):
        if cpt:
            res["item"].append({"sequence":j+1,"productOrService":{"coding":[{"system":"http://www.ama-assn.org/go/cpt","code":cpt}]}})
    return res


def observation_from_vital(v):
    # Minimal FHIR Observation from a VitalSign row
    res = {
        "resourceType": "Observation",
        "id": f"obs-{getattr(v,'id','')}",
        "status": "final",
        "code": {"coding": [{
            "system": getattr(v, "code_system", "") or "http://loinc.org",
            "code": getattr(v, "code", "") or "",
            "display": getattr(v, "display", "") or ""
        }]},
        "subject": {"reference": f"Patient/{getattr(v,'patient_id','')}"},
        "encounter": {"reference": f"Encounter/{getattr(v,'encounter_id','')}"},
        "valueQuantity": {
            "value": float(getattr(v, "value", 0) or 0),
            "unit": getattr(v, "unit", "") or ""
        }
    }
    eff = getattr(v, "effective_time", None)
    if eff:
        res["effectiveDateTime"] = eff.isoformat()
    return res


def vitals_bundle_from_encounter(enc, vitals):
    # Bundle wrapper for a set of vitals
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": observation_from_vital(v)} for v in vitals]
    }


def condition_to_fhir(c):
    # Minimal FHIR Condition from ConditionEntry
    out = {
        "resourceType": "Condition",
        "id": str(getattr(c,'id','') or ''),
        "subject": {"reference": f"Patient/{getattr(c,'patient_id','')}"},
        "clinicalStatus": {"text": getattr(c,'clinical_status','') or ''},
        "verificationStatus": {"text": getattr(c,'verification_status','') or ''},
        "code": {"coding": [{
            "system": getattr(c,'code_system','') or '',
            "code": getattr(c,'code','') or '',
            "display": getattr(c,'display','') or ''
        }]}
    }
    if getattr(c,'encounter_id',None):
        out["encounter"] = {"reference": f"Encounter/{getattr(c,'encounter_id','')}"}
    if getattr(c,'onset_date',None):
        out["onsetDateTime"] = c.onset_date.isoformat()
    if getattr(c,'abatement_date',None):
        out["abatementDateTime"] = c.abatement_date.isoformat()
    return out


def allergy_to_fhir(a):
    # Minimal FHIR AllergyIntolerance from AllergyEntry
    out = {
        "resourceType": "AllergyIntolerance",
        "id": str(getattr(a,'id','') or ''),
        "clinicalStatus": {"text": getattr(a,'status','') or ''},
        "code": {"coding": [{
            "system": getattr(a,'substance_system','') or '',
            "code": getattr(a,'substance_code','') or '',
            "display": getattr(a,'substance_display','') or ''
        }]},
        "patient": {"reference": f"Patient/{getattr(a,'patient_id','')}"}
    }
    rxn = (getattr(a,'reaction_text','') or '').strip()
    if rxn:
        out["reaction"] = [{"description": rxn, "severity": (getattr(a,'severity','') or '')}]
    return out


def practitioner_role_from_credential(provider, cred):
    # cred: ProviderPayerCredential, provider: Provider
    # Organization side: use payer id
    org_ref = {"reference": f"Organization/{getattr(cred,'payer_id','')}", "display": str(getattr(cred,'payer',''))}
    role = {
        "resourceType": "PractitionerRole",
        "id": f"role-{getattr(provider,'id','')}-{getattr(cred,'id','')}",
        "practitioner": {"reference": f"Practitioner/{getattr(provider,'id','')}"}
    }
    role["organization"] = org_ref
    # encode network/plan info as friendly extensions
    ext = []
    net_status = getattr(cred, "network_status", "") or ""
    net_name   = getattr(cred, "network_name", "") or ""
    plan_id    = getattr(cred, "plan_id", "") or ""
    plan_name  = getattr(cred, "plan_name", "") or ""
    if net_status: ext.append({"url":"urn:ext:network-status","valueString":net_status})
    if net_name:   ext.append({"url":"urn:ext:network-name","valueString":net_name})
    if plan_id:    ext.append({"url":"urn:ext:plan-id","valueString":plan_id})
    if plan_name:  ext.append({"url":"urn:ext:plan-name","valueString":plan_name})
    if ext: role["extension"] = ext
    # effective window
    eff = getattr(cred,"effective_date",None)
    end = getattr(cred,"end_date",None)
    if eff or end:
        role["period"] = {"start": str(eff) if eff else None, "end": str(end) if end else None}
    return role


def organization_from_facility(fac):
    org = {"resourceType":"Organization","id": str(getattr(fac,'id','') or ''), "name": getattr(fac,'name','') or ''}
    t = getattr(fac,'type','') or ''
    if t: org["type"]=[{"text": t}]
    npi2 = getattr(fac,'npi_2','') or ''
    if npi2:
        org["identifier"]=[{"system":"urn:npi-2","value": npi2}]
    return org


def practitioner_role_from_facility(provider, pf):
    return {
        "resourceType":"PractitionerRole",
        "id": f"role-fac-{getattr(provider,'id','')}-{getattr(pf,'id','')}",
        "practitioner": {"reference": f"Practitioner/{getattr(provider,'id','')}"},
        "organization": {"reference": f"Organization/{getattr(pf,'facility_id','')}"}
    }
