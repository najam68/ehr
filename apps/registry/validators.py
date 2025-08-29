import re
from django.core.exceptions import ValidationError
def validate_npi(value: str):
    s = (value or "").strip()
    if not re.fullmatch(r"\d{10}", s):
        raise ValidationError("Enter a 10-digit NPI.")
    base = "80840" + s[:-1]
    digits = [int(ch) for ch in base]
    for i in range(len(digits)-2, -1, -2):
        d = digits[i] * 2
        digits[i] = d if d < 10 else (d - 9)
    check = (10 - (sum(digits) % 10)) % 10
    if check != int(s[-1]):
        raise ValidationError("Invalid NPI (checksum failed).")
def validate_ssn(value: str):
    s = (value or "").strip()
    if not s:
        return
    if not re.fullmatch(r"\d{3}-\d{2}-\d{4}|\d{9}", s):
        raise ValidationError("Enter SSN as 123-45-6789 or 9 digits.")
