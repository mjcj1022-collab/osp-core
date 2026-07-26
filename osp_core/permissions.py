"""
DRF permission that enforces per-tenant app entitlements.

Usage in any app's view:
    from osp_core.permissions import requires_app
    class WorkOrderViewSet(ViewSet):
        permission_classes = [IsAuthenticated, requires_app("redline")]

Or set `required_app = "redline"` on the view and use HasAppEntitlement directly.
"""
from rest_framework.permissions import BasePermission

from .models import Entitlement


def _tenant_id(request):
    return (
        getattr(request, "tenant_id", None)
        or getattr(getattr(request, "user", None), "tenant_id", None)
    )


class HasAppEntitlement(BasePermission):
    app = None
    message = "Your plan does not include this app."

    def has_permission(self, request, view):
        app = getattr(view, "required_app", None) or self.app
        tid = _tenant_id(request)
        if not app or tid is None:
            return False
        return Entitlement.objects.filter(
            tenant_id=tid, app=app, active=True
        ).exists()


def requires_app(app_name):
    """Factory: requires_app('bim') -> a permission class scoped to that app."""
    return type(
        "HasAppEntitlement_%s" % app_name,
        (HasAppEntitlement,),
        {"app": app_name},
    )
