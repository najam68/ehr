from django.db import models

class Specialty(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    def __str__(self): return self.name

class Subspecialty(models.Model):
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE, related_name='subspecialties')
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    class Meta:
        unique_together = (('specialty','slug'),)
    def __str__(self): return f"{self.specialty.name} – {self.name}"

INPUT_TYPES = (
    ('text','text'),
    ('textarea','textarea'),
    ('number','number'),
    ('date','date'),
    ('email','email'),
    ('phone','phone'),
    ('select','select'),
    ('checkbox','checkbox'),
)

class FieldDefinition(models.Model):
    key = models.SlugField(max_length=140, unique=True)        # e.g. 'chief_complaint'
    label = models.CharField(max_length=160)                   # e.g. 'Chief Complaint'
    input_type = models.CharField(max_length=16, choices=INPUT_TYPES, default='text')
    required = models.BooleanField(default=False)
    group = models.CharField(max_length=60, blank=True, default='')   # e.g. 'History', 'Vitals', 'Allergy'
    order = models.PositiveIntegerField(default=100)
    help_text = models.CharField(max_length=240, blank=True, default='')
    choices_json = models.JSONField(default=list, blank=True)  # for select options
    is_active = models.BooleanField(default=True)

    specialties = models.ManyToManyField(Specialty, blank=True, related_name='field_definitions')
    subspecialties = models.ManyToManyField(Subspecialty, blank=True, related_name='field_definitions')

    def __str__(self): return f"{self.label} ({self.key})"
    class Meta:
        ordering = ['group','order','label']
