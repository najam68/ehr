
from django.db import models
from django.core.validators import RegexValidator
from .validators import validate_npi, validate_ssn
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# External app dependencies (assumes these apps exist)
from apps.patients.models import Patient

# ---------- Master data ----------

class Employer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=32, blank=True, default="")
    address_json = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name


class Payer(models.Model):
    name = models.CharField(max_length=200)
    payer_id = models.CharField(max_length=32, blank=True, default="", help_text="Clearinghouse/EDI payer id (e.g., CMS Payer ID)")
    clearinghouse_id = models.CharField(max_length=32, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    fax = models.CharField(max_length=32, blank=True, default="")
    address_json = models.JSONField(default=dict, blank=True)
    portal_url = models.URLField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["payer_id"])]

    def __str__(self):
        return f"{self.name} ({self.payer_id})" if self.payer_id else self.name


class Facility(models.Model):
    FACILITY_TYPES = [
        ("CLINIC","Clinic"),
        ("HOSPITAL","Hospital"),
        ("ASC","Ambulatory Surgery Center"),
        ("OTHER","Other"),
    ]
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=16, choices=FACILITY_TYPES, default="CLINIC")
    npi_2 = models.CharField(max_length=15, blank=True, default="")
    tax_id = models.CharField(max_length=20, blank=True, default="")
    address_json = models.JSONField(default=dict, blank=True)
    phone = models.CharField(max_length=32, blank=True, default="")
    fax = models.CharField(max_length=32, blank=True, default="")

    def __str__(self):
        return self.name


# ---------- Providers & Credentialing ----------

class Provider(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    npi = models.CharField(validators=[validate_npi], max_length=15, blank=True, default="")
    taxonomy_code = models.CharField(max_length=20, blank=True, default="")
    specialty = models.CharField(max_length=100, blank=True, default="")
    license_number = models.CharField(max_length=50, blank=True, default="")
    license_state = models.CharField(max_length=2, blank=True, default="")
    license_expiry = models.DateField(null=True, blank=True)
    dea_number = models.CharField(max_length=20, blank=True, default="")
    dea_expiry = models.DateField(null=True, blank=True)
    caqh_id = models.CharField(max_length=30, blank=True, default="")
    caqh_status = models.CharField(max_length=30, blank=True, default="")
    board_certified = models.BooleanField(default=False)
    board_cert_info = models.TextField(blank=True, default="")
    malpractice_insurer = models.CharField(max_length=100, blank=True, default="")
    malpractice_policy = models.CharField(max_length=100, blank=True, default="")
    malpractice_expiry = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class ProviderPayerCredential(models.Model):
    STATUS_CHOICES = [
        ("APPLIED","Applied"),
        ("IN_PROCESS","In Process"),
        ("APPROVED","Approved"),
        ("DENIED","Denied"),
        ("TERMINATED","Terminated"),
    ]
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="registry_payer_credentials")
    payer = models.ForeignKey(Payer, on_delete=models.CASCADE, related_name="registry_provider_credentials")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="APPLIED")
    effective_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    contract_id = models.CharField(max_length=50, blank=True, default="")
    fee_schedule_name = models.CharField(max_length=100, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("provider","payer")


# ---------- Patients & Profiles ----------

class PatientProfile(models.Model):
    MARITAL_CHOICES = [
        ("S","Single"),
        ("M","Married"),
        ("D","Divorced"),
        ("W","Widowed"),
        ("P","Partner"),
        ("U","Unknown"),
    ]
    EMPLOYMENT_CHOICES = [
        ("FT","Full-time"),("PT","Part-time"),("UNEMP","Unemployed"),
        ("RET","Retired"),("STUD","Student"),("UNK","Unknown")
    ]

    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name="registry_profile")
    mrn = models.CharField(max_length=40, blank=True, default="", help_text="Medical Record Number")
    ssn = models.CharField(validators=[validate_ssn], max_length=11, blank=True, default="")
    marital_status = models.CharField(max_length=1, choices=MARITAL_CHOICES, default="U")
    race = models.CharField(max_length=60, blank=True, default="")
    ethnicity = models.CharField(max_length=60, blank=True, default="")
    preferred_language = models.CharField(max_length=60, blank=True, default="")
    interpreter_required = models.BooleanField(default=False)

    employment_status = models.CharField(max_length=10, choices=EMPLOYMENT_CHOICES, default="UNK")
    occupation = models.CharField(max_length=100, blank=True, default="")
    employer = models.ForeignKey(Employer, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees")

    portal_enrolled = models.BooleanField(default=False)
    portal_username = models.CharField(max_length=100, blank=True, default="")
    portal_last_login = models.DateTimeField(null=True, blank=True)

    hipaa_ack_date = models.DateField(null=True, blank=True)
    privacy_notice_date = models.DateField(null=True, blank=True)
    consent_to_treat = models.BooleanField(default=True)
    consent_date = models.DateField(null=True, blank=True)
    assignment_of_benefits = models.BooleanField(default=True)
    aob_date = models.DateField(null=True, blank=True)

    preferred_pharmacy = models.CharField(max_length=200, blank=True, default="")
    primary_care_provider = models.ForeignKey('Provider', null=True, blank=True, on_delete=models.SET_NULL, related_name="panel_patients")

    def __str__(self):
        return f"Profile for Patient {self.patient_id}"


class EmergencyContact(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="registry_emergency_contacts")
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=60, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    alt_phone = models.CharField(max_length=32, blank=True, default="")
    address_json = models.JSONField(default=dict, blank=True)
    priority = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["priority","id"]

    def __str__(self):
        return f"{self.name} ({self.relationship})"


class Guarantor(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="registry_guarantors")
    name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=60, blank=True, default="")
    dob = models.DateField(null=True, blank=True)
    ssn = models.CharField(max_length=11, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    address_json = models.JSONField(default=dict, blank=True)
    employer = models.ForeignKey(Employer, null=True, blank=True, on_delete=models.SET_NULL, related_name="registry_guarantors")
    effective_start = models.DateField(null=True, blank=True)
    effective_end = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


# ---------- Insurance & Authorizations ----------

class Coverage(models.Model):
    ELIGIBILITY_CHOICES = [
        ("UNKNOWN","Unknown"),
        ("ACTIVE","Active"),
        ("INACTIVE","Inactive"),
        ("NEEDS_UPDATE","Needs Update"),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="registry_coverages")
    payer = models.ForeignKey(Payer, on_delete=models.PROTECT, related_name="registry_coverages")
    plan_name = models.CharField(max_length=120, blank=True, default="")
    member_id = models.CharField(max_length=80)
    group_number = models.CharField(max_length=80, blank=True, default="")
    relationship = models.CharField(max_length=20, default="self")  # self/spouse/child/other
    subscriber_name = models.CharField(max_length=200, blank=True, default="")
    subscriber_dob = models.DateField(null=True, blank=True)
    subscriber_ssn = models.CharField(max_length=11, blank=True, default="")
    subscriber_phone = models.CharField(max_length=32, blank=True, default="")
    subscriber_address_json = models.JSONField(default=dict, blank=True)
    subscriber_employer = models.ForeignKey(Employer, null=True, blank=True, on_delete=models.SET_NULL, related_name="registry_coverages")
    effective_start = models.DateField(null=True, blank=True)
    effective_end = models.DateField(null=True, blank=True)
    copay = models.DecimalField(validators=[MinValueValidator(0)], max_digits=10, decimal_places=2, default=0)
    coinsurance_percent = models.DecimalField(validators=[MinValueValidator(0), MaxValueValidator(100)], max_digits=5, decimal_places=2, default=0, help_text="Percent 0-100")
    deductible = models.DecimalField(validators=[MinValueValidator(0)], max_digits=10, decimal_places=2, default=0)
    oop_max = models.DecimalField(validators=[MinValueValidator(0)], max_digits=10, decimal_places=2, default=0)
    is_primary = models.BooleanField(default=True)
    priority = models.PositiveSmallIntegerField(default=1)
    card_front = models.FileField(upload_to="uploads/insurance_cards/", blank=True, null=True)
    card_back = models.FileField(upload_to="uploads/insurance_cards/", blank=True, null=True)
    eligibility_last_checked = models.DateTimeField(null=True, blank=True)
    eligibility_status = models.CharField(max_length=20, choices=ELIGIBILITY_CHOICES, default="UNKNOWN")
    eligibility_payload = models.JSONField(default=dict, blank=True)

    # --- Pack A fields (all with exactly 4 spaces indent) ---
    plan_type = models.CharField(max_length=64, blank=True, default="")
    network = models.CharField(max_length=64, blank=True, default="")
    group_name = models.CharField(max_length=120, blank=True, default="")
    rx_bin = models.CharField(max_length=20, blank=True, default="")
    rx_pcn = models.CharField(max_length=20, blank=True, default="")
    rx_group = models.CharField(max_length=20, blank=True, default="")
    rx_id = models.CharField(max_length=30, blank=True, default="")
    payer_contact_json = models.JSONField(default=dict, blank=True)
    cob_order = models.PositiveSmallIntegerField(default=1)
    coverage_class_json = models.JSONField(default=list, blank=True)
    extensions_json = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["member_id","group_number"]),
            models.Index(fields=["patient","is_primary","priority"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['patient'],
                condition=Q(is_primary=True),
                name='uniq_primary_coverage_per_patient'
            ),
        ]

    def __str__(self):
        return f"{self.patient_id} | {self.payer} | {self.member_id}"
    
class Authorization(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="registry_authorizations")
    coverage = models.ForeignKey(Coverage, on_delete=models.SET_NULL, null=True, blank=True, related_name="authorizations")
    procedure_code = models.CharField(max_length=20, help_text="CPT/HCPCS")
    diagnosis_codes = models.JSONField(default=list, blank=True)  # list of ICD-10
    authorized_units = models.PositiveIntegerField(default=0)
    used_units = models.PositiveIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    auth_number = models.CharField(max_length=80, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.auth_number or self.procedure_code} ({self.patient_id})"


class Referral(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="registry_referrals")
    from_provider = models.ForeignKey(Provider, null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals_out")
    to_provider = models.ForeignKey(Provider, null=True, blank=True, on_delete=models.SET_NULL, related_name="referrals_in")
    reason = models.TextField(blank=True, default="")
    date = models.DateField(null=True, blank=True)
    expires = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Referral {self.patient_id} -> {self.to_provider_id}"


# ---------- Generic document attachments ----------

class Document(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="uploads/documents/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["content_type","object_id"])]

    def __str__(self):
        return self.title

class ProviderLicense(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='licenses')
    state = models.CharField(max_length=2)  # e.g., IL
    number = models.CharField(max_length=50)
    license_type = models.CharField(max_length=40, blank=True, default="")
    expiry = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    class Meta:
        indexes = [models.Index(fields=['provider','state','expiry'])]
    def __str__(self):
        return f"{self.provider_id} {self.state} {self.number}"


class ProviderDEARegistration(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='dea_regs')
    dea_number = models.CharField(max_length=20)
    schedules = models.JSONField(default=list, blank=True)  # e.g., ["II","III","IV"]
    expiry = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    class Meta:
        indexes = [models.Index(fields=['provider','dea_number'])]
    def __str__(self):
        return f"{self.provider_id} {self.dea_number}"



class ProviderFacility(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='facilities')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='providers')
    role_title = models.CharField(max_length=100, blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    class Meta:
        indexes = [models.Index(fields=['provider','facility'])]
    def __str__(self):
        return f"{self.provider_id} @ {self.facility_id}"
