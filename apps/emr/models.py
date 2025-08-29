from django.db import models

# FK strings use app_label.ModelName where app_label = last part of the app package.
# patients.Patient and scheduling.Provider already exist in your project:contentReference[oaicite:7]{index=7}:contentReference[oaicite:8]{index=8}.

class Encounter(models.Model):
    STATUS = [("OPEN","OPEN"), ("CLOSED","CLOSED")]
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="encounters")
    provider = models.ForeignKey('registry.Provider', null=True, blank=True, on_delete=models.SET_NULL, related_name='emr_encounters')
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="OPEN")

    def __str__(self):
        return f"Enc {self.id} • Pt {self.patient_id} • {self.start:%Y-%m-%d %H:%M}"

class ProgressNote(models.Model):
    NOTE_TYPES = [("PROGRESS","Progress"), ("SOAP","SOAP")]
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="notes")
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default="PROGRESS")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Vital(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="vitals")
    measured_at = models.DateTimeField(auto_now_add=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temp_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    pulse_bpm = models.PositiveSmallIntegerField(null=True, blank=True)
    resp_rate = models.PositiveSmallIntegerField(null=True, blank=True)
    bp_systolic = models.PositiveSmallIntegerField(null=True, blank=True)
    bp_diastolic = models.PositiveSmallIntegerField(null=True, blank=True)
    spo2 = models.PositiveSmallIntegerField(null=True, blank=True)

class Problem(models.Model):
    STATUS = [("ACTIVE","ACTIVE"), ("RESOLVED","RESOLVED")]
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="problems")
    code_system = models.CharField(max_length=40, blank=True)   # e.g., icd10cm, snomed
    code = models.CharField(max_length=20, blank=True)
    display = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS, default="ACTIVE")
    onset_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)

class Medication(models.Model):
    STATUS = [("ACTIVE","ACTIVE"), ("STOPPED","STOPPED"), ("COMPLETED","COMPLETED")]
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="medications")
    name = models.CharField(max_length=160)
    dose = models.CharField(max_length=80, blank=True)      # e.g., 500 mg
    route = models.CharField(max_length=40, blank=True)     # PO/IV/IM/etc.
    frequency = models.CharField(max_length=40, blank=True) # b.i.d., q.d., etc.
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="ACTIVE")

class Allergy(models.Model):
    STATUS = [("ACTIVE","ACTIVE"), ("RESOLVED","RESOLVED")]
    SEVERITY = [("MILD","MILD"), ("MODERATE","MODERATE"), ("SEVERE","SEVERE")]
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="allergies")
    substance = models.CharField(max_length=160)
    reaction = models.CharField(max_length=160, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="ACTIVE")

class LabOrder(models.Model):
    STATUS = [("ORDERED","ORDERED"), ("RESULTED","RESULTED"), ("CANCELLED","CANCELLED")]
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="lab_orders")
    encounter = models.ForeignKey(Encounter, null=True, blank=True, on_delete=models.SET_NULL, related_name="lab_orders")
    code = models.CharField(max_length=30, blank=True)     # e.g., LOINC/CPT
    display = models.CharField(max_length=200)
    status = models.CharField(max_length=12, choices=STATUS, default="ORDERED")
    ordered_at = models.DateTimeField(auto_now_add=True)

class LabResult(models.Model):
    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="results")
    name = models.CharField(max_length=120)       # e.g., Hemoglobin
    value = models.CharField(max_length=60)       # keep as text for simplicity
    unit = models.CharField(max_length=20, blank=True)
    reference_range = models.CharField(max_length=60, blank=True)
    abnormal_flag = models.CharField(max_length=12, blank=True)  # H/L/A/…
    observed_at = models.DateTimeField(auto_now_add=True)
