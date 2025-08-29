from rest_framework import serializers
from .models import Payer, PayerPlan

class PayerPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayerPlan
        fields = "__all__"

class PayerSerializer(serializers.ModelSerializer):
    plans = PayerPlanSerializer(many=True, read_only=True)
    class Meta:
        model = Payer
        fields = "__all__"
