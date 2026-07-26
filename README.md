# osp-core

Shared canonical data model + multi-tenancy + entitlements for the OSP suite
(Make-Ready, REDLINE, Light Speed BIM, ODEN). This package **owns the Postgres
`core` schema**. Each app keeps its own backend and its own schema, imports this
package, and reads/writes the shared entities through it.

See `../PLATFORM-ARCHITECTURE.md` for the full design and `FIELD-OWNERSHIP.md` for
who writes which shared field.

## What's in `core`
`Tenant`, `Entitlement` (which apps a tenant bought), `Project` (the "job"),
`Pole`, `Attachment`, `Audit` — all tenant-scoped, all in the `core` Postgres schema.

## Install into an app backend
```bash
pip install -e /path/to/osp-core        # or add a git dependency
```
`settings.py`:
```python
INSTALLED_APPS += ["osp_core"]
MIDDLEWARE += ["osp_core.middleware.TenantRLSMiddleware"]
DATABASES["default"] = {  # every app points at the SAME database
    "ENGINE": "django.db.backends.postgresql",
    # ...shared host/name/user; app connects as a NON-superuser role (RLS)...
}
```

## The one hard rule
**Only osp-core migrates `core`.** App backends must never create/alter `core.*`
tables. Each app migrates only its own schema (`makeready`, `redline`, `bim`).
This is what keeps "separate backends, one DB" from turning into migration wars.

Run core migrations once (as an admin/owner role):
```bash
python manage.py migrate osp_core
```
Validate the hand-authored initial migration against your Django version:
```bash
python manage.py makemigrations --check osp_core
```

## Using shared data in an app
```python
from osp_core.models import Pole, Project
from osp_core.permissions import requires_app

# Make-Ready reads the same pole it (or BIM, or REDLINE) created:
pole = Pole.objects.get(tenant_id=tid, project__job_number=job, tag=tag)

# Gate a REDLINE view on the tenant's entitlement:
class WorkOrderView(APIView):
    permission_classes = [IsAuthenticated, requires_app("redline")]
```

## Entitlements / packaging
`Entitlement(tenant, app, tier, active, seats)` is the source of truth for a
customer's package. Expose it at `/api/me/entitlements` for the suite launcher to
show/hide apps. Billing (Stripe) is deferred — when added, a webhook just flips
`active`; no app code changes.
