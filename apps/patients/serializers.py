from rest_framework import serializers
from .models import Patient, Coverage

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = "__all__"

class CoverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coverage
        fields = "__all__"
