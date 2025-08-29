
from functools import wraps
from django.conf import settings
from rest_framework.response import Response

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

def api_write_required(view):
    """
    Require X-API-Key only for NON-safe HTTP methods (POST/PUT/PATCH/DELETE).
    If API_WRITE_KEY is blank, allow all (dev-friendly).
    """
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        key = getattr(settings, "API_WRITE_KEY", "")
        if key and request.method not in SAFE_METHODS:
            sent = request.headers.get("X-API-Key") or request.META.get("HTTP_X_API_KEY")
            if not sent or sent != key:
                return Response({"error": "invalid or missing API key"}, status=401)
        return view(request, *args, **kwargs)
    return _wrapped
