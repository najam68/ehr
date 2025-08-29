from rest_framework import serializers
from apps.claims.models import Denial, DenialStatusHistory

class DenialStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DenialStatusHistory
        fields = ["id", "from_status", "to_status", "note", "created_at"]

class DenialSerializer(serializers.ModelSerializer):
    history = DenialStatusHistorySerializer(many=True, read_only=True)
    class Meta:
        model = Denial
        fields = ["id", "claim_id", "status", "reason", "carc_code", "rarc_code", "created_at", "history"]
