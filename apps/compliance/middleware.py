import uuid
class RequestMetaMiddleware:
    """
    Placeholder middleware that annotates request with:
      - request.request_id (uuid4)
      - request.client_ip
      - request.user_agent
    So later we can stamp this into audit / disclosure logs.
    """
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        request.request_id = str(uuid.uuid4())
        request.client_ip = request.META.get('HTTP_X_FORWARDED_FOR','').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
        request.user_agent = request.META.get('HTTP_USER_AGENT','')
        return self.get_response(request)


class RequestPurposeMiddleware:
    """Extracts PHI 'purpose' of use (treatment/payment/operations/etc.) for later gating/logging."""
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        # Header takes precedence, fallback to query param
        purpose = request.META.get('HTTP_X_PURPOSE', '') or request.GET.get('purpose', '') or request.POST.get('purpose', '')
        request.phi_purpose = (purpose or '').strip().lower()  # e.g., 'treatment','payment','operations','patient-request','law'
        return self.get_response(request)
