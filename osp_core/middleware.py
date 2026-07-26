"""
TenantRLSMiddleware — sets the Postgres session variable `app.tenant_id` for each
request so row-level security policies (see migration 0002) enforce tenant
isolation at the database, not just in app code.

Requires something upstream (your auth layer) to put the tenant id on the request
as `request.tenant_id` (or `request.user.tenant_id`). With Netlify Identity, that's
the `tenant:` claim resolved to a Tenant row.
"""
from django.db import connection


def _tenant_id(request):
    return (
        getattr(request, "tenant_id", None)
        or getattr(getattr(request, "user", None), "tenant_id", None)
    )


class TenantRLSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tid = _tenant_id(request)
        if tid is not None:
            with connection.cursor() as cur:
                # set_config(..., is_local=false) so it persists for the connection
                cur.execute("SELECT set_config('app.tenant_id', %s, false)", [str(tid)])
        return self.get_response(request)
