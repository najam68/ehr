from django.db import models
from apps.specialties.models import Specialty
from django.utils import timezone

class Patient(models.Model):

    # --- EMR-grade demographics ---
    middle_name = models.CharField(max_length=60, blank=True, default='')
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=16, blank=True, default='')  # male|female|other|unknown
    ssn = models.CharField(max_length=11, blank=True, default='')

    # contact
    phone = models.CharField(max_length=32, blank=True, default='')
    phone_alt = models.CharField(max_length=32, blank=True, default='')
    email = models.EmailField(blank=True, default='')

    # address
    address_line1 = models.CharField(max_length=120, blank=True, default='')
    address_line2 = models.CharField(max_length=120, blank=True, default='')
    city = models.CharField(max_length=80, blank=True, default='')
    state = models.CharField(max_length=40, blank=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    country = models.CharField(max_length=2, blank=True, default='US')

    # additional demographics
    race = models.CharField(max_length=60, blank=True, default='')
    ethnicity = models.CharField(max_length=60, blank=True, default='')
    language = models.CharField(max_length=60, blank=True, default='')
    marital_status = models.CharField(max_length=20, blank=True, default='')
    preferred_contact_method = models.CharField(max_length=20, blank=True, default='')  # phone|email|sms

    # employment / guarantor
    employer_name = models.CharField(max_length=120, blank=True, default='')
    occupation = models.CharField(max_length=120, blank=True, default='')
    guarantor_name = models.CharField(max_length=120, blank=True, default='')
    guarantor_relationship = models.CharField(max_length=40, blank=True, default='')
    guarantor_phone = models.CharField(max_length=32, blank=True, default='')

    # portal & consents (placeholders for HIPAA)
    portal_enrolled = models.BooleanField(default=False)
    consent_to_treat = models.BooleanField(default=False)
    assignment_of_benefits = models.BooleanField(default=False)
    hipaa_privacy_ack = models.BooleanField(default=False)
    consent_ack_at = models.DateTimeField(null=True, blank=True)

    # timestamps (if you don't already have them)
    created_at = models.DateTimeField(default=timezone.now, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    date_of_birth = models.DateField()
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    specialty = models.ForeignKey( 'specialties.Specialty', null=True, blank=True, on_delete=models.SET_NULL, related_name='patients')
    extra_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

class Coverage(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="coverages")
    payer_name = models.CharField(max_length=120)
    member_id = models.CharField(max_length=80)
    group_number = models.CharField(max_length=80, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    relation_to_subscriber = models.CharField(max_length=30, blank=True)  # self/spouse/etc.
    plan = models.JSONField(default=dict, blank=True)  # extra attributes

    def __str__(self):
        return f"{self.payer_name} - {self.member_id}"


class EmergencyContact(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=60, blank=True, default='')
    phone = models.CharField(max_length=32, blank=True, default='')
    email = models.EmailField(blank=True, default='')

    def __str__(self):
        return f"{self.name} ({self.relationship})"
