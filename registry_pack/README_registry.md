
# Registry Pack (Patient/Provider Credentialing + Insurance/Coverage/Guarantor)

This pack adds comprehensive, OpenEMR-style master data models without disturbing your existing `apps.patients` tables. It uses **OneToOne** and **ForeignKey** relations so you can attach rich data as you grow.

## What’s included

**Apps/Models (new app: `apps.registry`)**

- **Employer**
- **Payer** (payer_id, address, portal URL, etc.)
- **Facility** (NPI-2, tax id)
- **Provider** (NPI, license, DEA, CAQH, board cert, malpractice)
- **ProviderPayerCredential** (per-payer credentialing status, effective dates)
- **PatientProfile** (MRN, SSN, demographics, HIPAA/consents, portal, PCP, employment)
- **EmergencyContact** (priority-ordered)
- **Guarantor** (with employer)
- **Coverage** (member/group, relationship, subscriber details, copay/coinsurance/deductible, eligibility snapshot, card images)
- **Authorization** (per patient/coverage, CPT, ICD list, units, date window)
- **Referral** (from/to provider, reason, dates)
- **Document** (generic attachments via contenttypes)

All address fields are stored as **JSON** for flexibility: `{"street":"","city":"","state":"","postal_code":"","country":""}`.

## Install

1. **Unzip at your project root** (same folder as `manage.py`) so the paths look like:
   ```
   apps/registry/models.py
   apps/registry/admin.py
   ```

2. **Add to `INSTALLED_APPS`** in your project settings:
   ```python
   'apps.registry',
   ```

3. **Migrate:**
   ```bash
   python manage.py makemigrations registry
   python manage.py migrate
   ```

4. Open Django admin and you’ll see the new sections. Link records to existing Patients, Payers, Providers, etc.

## Notes

- File uploads (`Coverage.card_front`, `Coverage.card_back`, `Document.file`) use default Django storage. If you haven’t set up `MEDIA_ROOT`/`MEDIA_URL` yet, you can still migrate; uploading will need media configured later.
- All related names are **namespaced** (e.g., `patient.registry_coverages`, `patient.registry_authorizations`) to avoid clashes.
- This is **FHIR‑friendly**: Coverage/Authorization/Referral/Provider map cleanly to FHIR resources (`Coverage`, `Authorization` via `CoverageEligibilityRequest/Response` or custom; `ServiceRequest`/`ReferralRequest`; `Practitioner`).
- You can safely extend with site-specific fields later by adding columns or JSON attributes.
