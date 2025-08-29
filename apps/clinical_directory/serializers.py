from rest_framework import serializers
from .models import Specialty, CareSetting, Clinic

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = "__all__"

class CareSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareSetting
        fields = "__all__"

class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = "__all__"
