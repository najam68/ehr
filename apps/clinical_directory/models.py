from django.db import models

class Specialty(models.Model):
    title = models.CharField(max_length=120)
    slug = models.SlugField(primary_key=True)  # string PK
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    nucc_code = models.CharField(max_length=20, blank=True)
    synonyms = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

class CareSetting(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(primary_key=True)  # string PK
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    description = models.TextField(blank=True)
    pos_codes = models.JSONField(default=list, blank=True)
    cms_provider_type = models.CharField(max_length=80, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

class Clinic(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    legal_name = models.CharField(max_length=180, blank=True)
    npi = models.CharField(max_length=10, blank=True)
    tin = models.CharField(max_length=20, blank=True)
    address = models.JSONField(default=dict, blank=True)  # {line, city, state, postal, country}
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    care_setting = models.ForeignKey(CareSetting, on_delete=models.PROTECT)  # points to slug PK
    specialties = models.ManyToManyField(Specialty, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
