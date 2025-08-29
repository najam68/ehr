from rest_framework import viewsets, filters
from .models import Specialty, CareSetting, Clinic
from .serializers import SpecialtySerializer, CareSettingSerializer, ClinicSerializer

class SpecialtyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "slug", "nucc_code", "synonyms"]

class CareSettingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CareSetting.objects.all()
    serializer_class = CareSettingSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "slug", "pos_codes"]

class ClinicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "slug", "npi", "tin"]
