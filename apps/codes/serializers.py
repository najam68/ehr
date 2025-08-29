from rest_framework import serializers
from .models import CodeSystem, Code

class CodeSystemSerializer(serializers.ModelSerializer):
    class Meta: model = CodeSystem; fields = "__all__"

class CodeSerializer(serializers.ModelSerializer):
    system = CodeSystemSerializer(read_only=True)
    class Meta: model = Code; fields = "__all__"
