from django import forms
from django.utils import timezone
from .models import Patient

class PatientIntakeForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'specialty',  # ⭐ drives dynamic fields

            # Identity
            'first_name','middle_name','last_name','dob','gender','ssn',
            # Contact
            'phone','phone_alt','email',
            # Address
            'address_line1','address_line2','city','state','postal_code','country',
            # Demographics
            'race','ethnicity','language','marital_status','preferred_contact_method',
            # Employment / Guarantor
            'employer_name','occupation','guarantor_name','guarantor_relationship','guarantor_phone',
            # Consents
            'portal_enrolled','consent_to_treat','assignment_of_benefits','hipaa_privacy_ack',
        ]
        widgets = {
            'dob': forms.TextInput(attrs={'placeholder':'YYYY-MM-DD'}),
            'gender': forms.Select(choices=[('','—'),('male','male'),('female','female'),('other','other'),('unknown','unknown')]),
            'country': forms.TextInput(attrs={'value':'US'}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        # If any consent box is ticked, stamp a time (idempotent)
        if (self.cleaned_data.get('consent_to_treat') or
            self.cleaned_data.get('assignment_of_benefits') or
            self.cleaned_data.get('hipaa_privacy_ack')):
            obj.consent_ack_at = obj.consent_ack_at or timezone.now()
        if commit:
            obj.save()
        return obj
