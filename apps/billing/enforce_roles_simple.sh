#!/usr/bin/env bash
set -euo pipefail

log(){ printf "\n▶ %s\n" "$*"; }
die(){ echo "❌ %s\n" "$*" >&2; exit 1; }

[ -f manage.py ] || die "Run from your Django project root (manage.py not found)."

CHART_VIEWS="apps/chart/views.py"
BILL_VIEWS="apps/billing/views.py"
[ -f "$CHART_VIEWS" ] || die "Missing $CHART_VIEWS"
[ -f "$BILL_VIEWS" ] || die "Missing $BILL_VIEWS"

log "Writing apps/common/decorators.py (@group_required)"
mkdir -p apps/common
cat > apps/common/__init__.py <<'PY'
# common package
PY
cat > apps/common/decorators.py <<'PY'
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
PY

log "Patching chart views (Clinician)"
python - <<'PY'
import re
from pathlib import Path

path = Path("apps/chart/views.py")
s = path.read_text()

# Ensure import
if "from apps.common.decorators import group_required" not in s:
    lines = s.splitlines(keepends=True)
    idx = 0
    for i, line in enumerate(lines[:50]):
        if line.startswith("from ") or line.startswith("import "):
            idx = i + 1
    lines.insert(idx, "from apps.common.decorators import group_required\n")
    s = "".join(lines)

def add_deco(src, func, group):
    pattern = re.compile(rf"(^\s*(?:@.*\n)*)^\s*def\s+{func}\s*\(", re.M)
    m = pattern.search(src)
    if not m:
        print(f"skip (not found): {func}")
        return src
    pre = m.group(1) or ""
    if "@group_required(" in pre:
        return src
    insert_at = m.start(1) if pre else m.start()
    return src[:insert_at] + f"@group_required('{group}')\n" + src[insert_at:]

for fn in ["encounter_list","encounter_detail","new_encounter"]:
    s = add_deco(s, fn, "Clinician")

path.write_text(s)
print("chart views patched")
PY

log "Patching billing views (Biller)"
python - <<'PY'
import re
from pathlib import Path

path = Path("apps/billing/views.py")
s = path.read_text()

# Ensure import
if "from apps.common.decorators import group_required" not in s:
    lines = s.splitlines(keepends=True)
    idx = 0
    for i, line in enumerate(lines[:50]):
        if line.startswith("from ") or line.startswith("import "):
            idx = i + 1
    lines.insert(idx, "from apps.common.decorators import group_required\n")
    s = "".join(lines)

def add_deco(src, func, group):
    pattern = re.compile(rf"(^\s*(?:@.*\n)*)^\s*def\s+{func}\s*\(", re.M)
    m = pattern.search(src)
    if not m:
        print(f"skip (not found): {func}")
        return src
    pre = m.group(1) or ""
    if "@group_required(" in pre:
        return src
    insert_at = m.start(1) if pre else m.start()
    return src[:insert_at] + f"@group_required('{group}')\n" + src[insert_at:]

for fn in ["superbill_list","superbill_detail","new_superbill"]:
    s = add_deco(s, fn, "Biller")

path.write_text(s)
print("billing views patched")
PY

echo "▶ Django check"
python manage.py check

echo "✅ Role enforcement applied via @group_required (Clinician -> chart/*, Biller -> billing/*)."
