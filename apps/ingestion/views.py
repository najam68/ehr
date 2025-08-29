from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from .models import Provenance
from .utils import sha256_file

@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload(request):
    """Upload a CSV/CCDA/FHIR file and record provenance only (no transform yet)."""
    f = request.FILES.get("file")
    fmt = request.POST.get("format","UNKNOWN").upper()
    src = request.POST.get("source_system","")
    if not f:
        return Response({"error":"file is required"}, status=status.HTTP_400_BAD_REQUEST)
    h = sha256_file(f)
    prov = Provenance.objects.create(
        source_system=src,
        file_name=f.name,
        file_hash=h,
        format=fmt,
        notes=request.POST.get("notes",""),
    )
    return Response({"provenance_id": prov.id, "hash": h}, status=status.HTTP_201_CREATED)
