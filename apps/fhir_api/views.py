from .resources import practitioner_role_from_credential, practitioner_to_fhir
from apps.registry.models import Provider as DbProvider, ProviderPayerCredential as DbCred
from .resources import patient_to_fhir, coverage_to_fhir, encounter_to_fhir, documentreference_soap, observation_from_vital, condition_to_fhir, allergy_to_fhir
from .resources import patient_to_fhir, practitioner_to_fhir, practitioner_role_to_fhir, organization_from_payer, coverage_to_fhir, encounter_to_fhir, documentreference_soap, claim_from_superbill, observation_from_vital, condition_to_fhir, allergy_to_fhir
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from datetime import datetime, timezone

from fhir.resources.patient import Patient as FhirPatient
from fhir.resources.bundle import Bundle
from fhir.resources.capabilitystatement import CapabilityStatement

# Try Patient model
try:
    from apps.patients.models import Patient as DbPatient
except Exception:
    DbPatient = None

def _clean(s):
    if s is None:
        return None
    s = str(s).strip()
    return s or None

def _prune(x):
    # Recursively drop None/''/[]/{} so fhir.resources validators don't choke on empties.
    if isinstance(x, str):
        x = x.strip()
        return x or None
    if isinstance(x, list):
        items = [_prune(i) for i in x]
        items = [i for i in items if i not in (None, "", [], {})]
        return items or None
    if isinstance(x, dict):
        items = {k: _prune(v) for k, v in x.items()}
        items = {k: v for k, v in items.items() if v not in (None, "", [], {})}
        return items or None
    return x

def _map_gender(g):
    g = _clean(g)
    if not g: return "unknown"
    g = g.lower()
    if g in {"m","male"}: return "male"
    if g in {"f","female"}: return "female"
    if g in {"other","o"}: return "other"
    return "unknown"

def fhir_patient_dict(dbp):
    addr_src = getattr(dbp, "address_json", None) or getattr(dbp, "address", None) or {}
    street = _clean(addr_src.get("street")) if isinstance(addr_src, dict) else None
    city = _clean(addr_src.get("city")) if isinstance(addr_src, dict) else None
    state = _clean(addr_src.get("state")) if isinstance(addr_src, dict) else None
    postal = _clean(addr_src.get("postal_code")) if isinstance(addr_src, dict) else None

    name_family = _clean(getattr(dbp, "last_name", ""))
    name_given = _clean(getattr(dbp, "first_name", ""))

    data = {"resourceType": "Patient", "id": str(dbp.pk)}

    # Only include name if we have at least one piece
    name = {"use": "official"}
    if name_family: name["family"] = name_family
    if name_given: name["given"] = [name_given]
    if name.keys() != {"use"}:
        data["name"] = [name]

    # Gender and birthDate
    data["gender"] = _map_gender(getattr(dbp, "gender", ""))
    dob = getattr(dbp, "dob", None)
    if dob: data["birthDate"] = dob.isoformat()

    # Address (only if any component present)
    address = {}
    if street: address["line"] = [street]
    if city: address["city"] = city
    if state: address["state"] = state
    if postal: address["postalCode"] = postal
    if address: data["address"] = [address]

    # Prune recursively
    data = _prune(data) or {"resourceType": "Patient", "id": str(dbp.pk)}

    return data

class PatientBundleView(APIView):
    def get(self, request: Request, pk: int):
        if DbPatient is None:
            raise Http404("Patient model not available")
        dbp = get_object_or_404(DbPatient, pk=pk)
        patient_res = FhirPatient(**fhir_patient_dict(dbp))
        bundle = Bundle.construct()
        bundle.type = "collection"
        bundle.entry = [{"resource": patient_res.dict()}]
        return Response(bundle.dict())

class FirstPatientBundleView(APIView):
    def get(self, request: Request):
        if DbPatient is None:
            raise Http404("Patient model not available")
        first = DbPatient.objects.order_by("pk").first()
        if not first:
            raise Http404("No Patient rows found")
        patient_res = FhirPatient(**fhir_patient_dict(first))
        bundle = Bundle.construct()
        bundle.type = "collection"
        bundle.entry = [{"resource": patient_res.dict()}]
        return Response(bundle.dict())

class PatientResourceView(APIView):
    def get(self, request: Request, pk: int):
        if DbPatient is None:
            raise Http404("Patient model not available")
        dbp = get_object_or_404(DbPatient, pk=pk)
        patient_res = FhirPatient(**fhir_patient_dict(dbp))
        return Response(patient_res.dict())

class CapabilityStatementView(APIView):
    def get(self, request: Request):
        # Build with required fields at construction time to satisfy validators
        now_iso = datetime.now(timezone.utc).isoformat()
        cs = CapabilityStatement(
            status="active",
            kind="instance",
            date=now_iso,
            fhirVersion="4.0.1",
            format=["json"],
            rest=[{
                "mode": "server",
                "resource": [
                    {"type": "Patient", "interaction": [{"code": "read"}, {"code": "search-type"}]}
                ]
            }]
        )
        return Response(cs.dict())
from apps.registry.models import Provider as DbProvider, Payer as DbPayer, Coverage as DbCoverage
from apps.chart.models import Encounter as DbEncounter, VitalSign as DbVital, ConditionEntry as DbCondition, AllergyEntry as DbAllergy, SoapNote as DbSoap
from apps.billing.models import Superbill as DbSuperbill


class FHIRHealthView(APIView):
    def get(self, request: Request):
        # quick smoke of first records; do not fail if missing
        out = {"ok": True, "checks": []}
        try:
            p = DbPatient.objects.first()
            out["checks"].append({"patient_first": bool(p)})
        except Exception as e:
            out["checks"].append({"patient_first": False, "error": str(e)})
        try:
            pr = DbProvider.objects.first()
            out["checks"].append({"provider_first": bool(pr)})
        except Exception as e:
            out["checks"].append({"provider_first": False, "error": str(e)})
        try:
            cov = DbCoverage.objects.first()
            out["checks"].append({"coverage_first": bool(cov)})
        except Exception as e:
            out["checks"].append({"coverage_first": False, "error": str(e)})
        try:
            enc = DbEncounter.objects.first()
            out["checks"].append({"encounter_first": bool(enc)})
        except Exception as e:
            out["checks"].append({"encounter_first": False, "error": str(e)})
        try:
            sb = DbSuperbill.objects.first()
            out["checks"].append({"superbill_first": bool(sb)})
        except Exception as e:
            out["checks"].append({"superbill_first": False, "error": str(e)})
        return JsonResponse(out)

class PatientResource(APIView):
    def get(self, request: Request, pk: int):
        p = get_object_or_404(DbPatient, pk=pk)
        return JsonResponse(patient_to_fhir(p))


class PractitionerResource(APIView):
    def get(self, request: Request, pk: int):
        pr = get_object_or_404(DbProvider, pk=pk)
        return JsonResponse(practitioner_to_fhir(pr))

class PractitionerRoleResource(APIView):
    def get(self, request: Request, pk: int):
        pr = get_object_or_404(DbProvider, pk=pk)
        # we don't have organization/facility id; return bare role
        return JsonResponse(practitioner_role_to_fhir(pr))

class OrganizationFromPayer(APIView):
    def get(self, request: Request, pk: int):
        payer = get_object_or_404(DbPayer, pk=pk)
        return JsonResponse(organization_from_payer(payer))

class CoverageResource(APIView):
    def get(self, request: Request, pk: int):
        cov = get_object_or_404(DbCoverage, pk=pk)
        return JsonResponse(coverage_to_fhir(cov))

class EncounterResource(APIView):
    def get(self, request: Request, pk: int):
        enc = get_object_or_404(DbEncounter, pk=pk)
        return JsonResponse(encounter_to_fhir(enc))

class DocumentReferenceSoap(APIView):
    def get(self, request: Request, pk: int):
        enc = get_object_or_404(DbEncounter, pk=pk)
        try:
            soap = DbSoap.objects.filter(encounter=enc).first()
        except Exception:
            soap = None
        return JsonResponse(documentreference_soap(enc, soap))

class ClaimFromSuperbill(APIView):
    def get(self, request: Request, pk: int):
        sb = get_object_or_404(DbSuperbill, pk=pk)
        return JsonResponse(claim_from_superbill(sb))

from apps.registry.models import Coverage as DbCoverage


class CoverageEligibilityResponseView(APIView):
    """Very small read-only FHIR-like response for a Coverage."""
    def get(self, request: Request, pk: int):
        try:
            cov = DbCoverage.objects.select_related("patient","payer").get(pk=pk)
        except DbCoverage.DoesNotExist:
            return JsonResponse({"resourceType":"OperationOutcome","issue":[{"severity":"error","diagnostics":"Coverage not found"}]}, status=404)
        out = {
            "resourceType": "CoverageEligibilityResponse",
            "id": str(cov.id),
            "status": "active",
            "patient": {"reference": f"Patient/{cov.patient_id}"},
            "insurer": {"reference": f"Organization/{cov.payer_id}"},
            "outcome": (cov.eligibility_status or "unknown").lower(),
            "disposition": "Eligibility checked",
            "created": cov.eligibility_last_checked.isoformat() if cov.eligibility_last_checked else None,
        }
        return JsonResponse(out)

from .resources import vitals_bundle_from_encounter, observation_from_vital

class VitalsObservationBundle(APIView):
    def get(self, request: Request, pk: int):
        try:
            enc = DbEncounter.objects.get(pk=pk)
        except DbEncounter.DoesNotExist:
            return JsonResponse({"resourceType":"OperationOutcome","issue":[{"severity":"error","diagnostics":"Encounter not found"}]}, status=404)
        vitals = DbVital.objects.filter(encounter=enc).order_by('id')[:50]
        # Use bundle helper if available; fall back to building entries
        try:
            return JsonResponse(vitals_bundle_from_encounter(enc, vitals))
        except Exception:
            bundle={"resourceType":"Bundle","type":"collection","entry":[]}
            for v in vitals:
                bundle["entry"].append({"resource": observation_from_vital(v)})
            return JsonResponse(bundle)


class PatientEverything(APIView):
    """Bundle: Patient + Coverages + last Encounter (+ SOAP) + vitals + problems + allergies."""
    def get(self, request: Request, pk: int):
        try:
            p = DbPatient.objects.get(pk=pk)
        except DbPatient.DoesNotExist:
            return JsonResponse({"resourceType":"OperationOutcome","issue":[{"severity":"error","diagnostics":"Patient not found"}]}, status=404)

        bundle = {"resourceType":"Bundle","type":"collection","entry":[]}

        # Patient
        bundle["entry"].append({"resource": patient_to_fhir(p)})

        # Coverages
        try:
            from apps.registry.models import Coverage as DbCoverage
            for cov in DbCoverage.objects.filter(patient=p).order_by("-is_primary","priority","id")[:10]:
                bundle["entry"].append({"resource": coverage_to_fhir(cov)})
        except Exception:
            pass

        # Last encounter + SOAP + vitals (fallback to patient-level vitals if none on encounter)
        try:
            enc = DbEncounter.objects.filter(patient=p).order_by("-id").first()
            if enc:
                bundle["entry"].append({"resource": encounter_to_fhir(enc)})
                try:
                    from apps.chart.models import SoapNote as DbSoap
                    soap = DbSoap.objects.filter(encounter=enc).first()
                except Exception:
                    soap = None
                bundle["entry"].append({"resource": documentreference_soap(enc, soap)})

                vit_qs = list(DbVital.objects.filter(encounter=enc).order_by("id")[:50])
                if not vit_qs:
                    vit_qs = list(DbVital.objects.filter(patient=p).order_by("-id")[:50])
                for v in vit_qs:
                    bundle["entry"].append({"resource": observation_from_vital(v)})
        except Exception:
            pass

        # Problems
        try:
            for c in DbCondition.objects.filter(patient=p).order_by("-id")[:50]:
                bundle["entry"].append({"resource": condition_to_fhir(c)})
        except Exception:
            pass

        # Allergies
        try:
            for a in DbAllergy.objects.filter(patient=p).order_by("-id")[:50]:
                bundle["entry"].append({"resource": allergy_to_fhir(a)})
        except Exception:
            pass

        return JsonResponse(bundle)

class PractitionerRoleForProvider(APIView):
    # Returns a Bundle of PractitionerRole resources (one per payer credential). Falls back to single role if none.
    def get(self, request: Request, pk: int):
        try:
            pr = DbProvider.objects.get(pk=pk)
        except DbProvider.DoesNotExist:
            return JsonResponse({"resourceType":"OperationOutcome","issue":[{"severity":"error","diagnostics":"Provider not found"}]}, status=404)
        roles = []
        # Facility-based roles (if linked)
        try:
            pfs = DbPF.objects.filter(provider=pr).select_related('facility')
            for pf in pfs:
                roles.append({"resource": practitioner_role_from_facility(pr, pf)})
        except Exception:
            pass

        try:
            creds = DbCred.objects.filter(provider=pr).select_related('payer').order_by('payer__name')
            for c in creds:
                roles.append({"resource": practitioner_role_from_credential(pr, c)})
        except Exception:
            pass
        if not roles:
            # no credentials -> return a minimal single role as a Bundle for consistency
            roles = [{"resource": {"resourceType":"PractitionerRole","id": f"role-{pr.id}","practitioner":{"reference": f"Practitioner/{pr.id}"}}}]
        return JsonResponse({"resourceType":"Bundle","type":"collection","entry": roles})

class ClaimResponseView(APIView):
    # Minimal ClaimResponse for a Superbill (demo stub)
    def get(self, request: Request, pk: int):
        try:
            sb = DbSuperbill.objects.get(pk=pk)
        except DbSuperbill.DoesNotExist:
            return JsonResponse({"resourceType":"OperationOutcome","issue":[{"severity":"error","diagnostics":"Superbill not found"}]}, status=404)
        total = float(getattr(sb,"total",0) or 0)
        out = {
            "resourceType":"ClaimResponse",
            "id": f"cr-{sb.id}",
            "status":"active",
            "type":{"coding":[{"system":"http://terminology.hl7.org/CodeSystem/claim-type","code":"professional"}]},
            "use":"claim",
            "outcome":"complete",
            "disposition":"Processed (demo)",
            "request":{"reference": f"Claim/{sb.id}"},
            "total":[{"category":{"text":"submitted"},"amount":{"value": round(total,2),"currency":"USD"}}]
        }
        
        # If stored payload exists, merge friendly fields
        try:
            from apps.billing.models import ClaimResponseStore
            store = ClaimResponseStore.objects.filter(superbill=sb).first()
            if store and isinstance(store.payload, dict):
                if 'outcome' in store.payload:
                    out['outcome'] = store.payload['outcome']
                if 'disposition' in store.payload:
                    out['disposition'] = store.payload['disposition']
                if 'total' in store.payload and isinstance(store.payload['total'], (int,float)):
                    out['total']=[{'category':{'text':'submitted'},'amount':{'value': float(store.payload['total']), 'currency':'USD'}}]
        except Exception:
            pass
        
        return JsonResponse(out)

from apps.registry.models import ProviderFacility as DbPF
from .resources import organization_from_facility, practitioner_role_from_facility

class OrganizationFromFacility(APIView):
    def get(self, request: Request, pk: int):
        from apps.registry.models import Facility as DbFacility
        try:
            fac = DbFacility.objects.get(pk=pk)
        except DbFacility.DoesNotExist:
            return JsonResponse({"resourceType":"OperationOutcome","issue":[{"severity":"error","diagnostics":"Facility not found"}]}, status=404)
        return JsonResponse(organization_from_facility(fac))

# facility roles will be added inside view body at runtime

class FHIRPing(APIView):
    def get(self, request: Request):
        return JsonResponse({"ok": True, "pong": True})
