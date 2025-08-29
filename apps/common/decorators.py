from functools import wraps
from django.http import HttpResponse

def group_required(group_name):
    # Require user to be in a Django Group; superusers bypass. If unauthenticated, let login_required handle it.
    def _wrap(view_func):
        @wraps(view_func)
        def _inner(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                # Let @login_required handle redirects; call through
                return view_func(request, *args, **kwargs)
            if user.is_superuser or user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponse(
                "<div class='container py-5'><div class='alert alert-danger'>403: You need %s role.</div></div>" % group_name,
                status=403,
            )
        return _inner
    return _wrap
