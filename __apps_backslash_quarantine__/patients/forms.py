from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    # UI fields
    street = forms.CharField(max_length=128, required=False, label="Street")
    city = forms.CharField(max_length=64, required=False, label="City")
    state = forms.CharField(max_length=32, required=False, label="State")
    postal_code = forms.CharField(max_length=16, required=False, label="ZIP")

    class Meta:
        model = Patient
        fields = "__all__"  # we'll drop any JSON field dynamically in __init__

    def _addr_field_name(self):
        # support either 'address_json' or 'address'
        if hasattr(self.instance, "address_json"):
            return "address_json"
        if hasattr(self.instance, "address"):
            return "address"
        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # hide JSON field(s) from UI if present
        for raw in ("address_json","address"):
            if raw in self.fields:
                self.fields.pop(raw)
        name = self._addr_field_name()
        data = getattr(self.instance, name, {}) or {}
        if isinstance(data, dict):
            self.initial.update({
                "street": data.get("street",""),
                "city": data.get("city",""),
                "state": data.get("state",""),
                "postal_code": data.get("postal_code",""),
            })

    def clean(self):
        cleaned = super().clean()
        addr = {
            "street": cleaned.pop("street","") or "",
            "city": cleaned.pop("city","") or "",
            "state": cleaned.pop("state","") or "",
            "postal_code": cleaned.pop("postal_code","") or "",
        }
        name = self._addr_field_name()
        if name:
            # only set if any field is provided; else keep None/empty
            if any(v for v in addr.values()):
                setattr(self.instance, name, addr)
        return cleaned
