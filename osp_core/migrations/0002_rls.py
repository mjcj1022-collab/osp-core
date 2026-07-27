"""
Row-Level Security for the tenant-scoped DATA tables. Each request sets
`app.tenant_id` (authentication.py, after resolving the tenant from the JWT); the
policy then limits the connection to that tenant's rows.

Design choices (see PLATFORM-ARCHITECTURE.md):
- RLS is applied to DATA tables only (entitlement, project, pole, attachment,
  audit). The IDENTITY tables (tenant, user, membership) are intentionally left
  open so the auth layer can upsert them before any tenant context exists — access
  to identity is governed by Membership + app logic.
- ENABLE without FORCE: the table OWNER (used for migrations + admin/backfill)
  bypasses RLS, so those operations work; the runtime app must connect as a
  NON-owner role (osp_app) for the policy to take effect.
"""
from django.db import migrations

_TID = "NULLIF(current_setting('app.tenant_id', true), '')::bigint"

_TABLES = [
    'core"."entitlement',
    'core"."project',
    'core"."pole',
    'core"."attachment',
    'core"."audit',
]


def _enable(table):
    t = '"%s"' % table
    return (
        f'ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;\n'
        f'DROP POLICY IF EXISTS tenant_isolation ON {t};\n'
        f'CREATE POLICY tenant_isolation ON {t}\n'
        f'  USING (tenant_id = {_TID})\n'
        f'  WITH CHECK (tenant_id = {_TID});'
    )


def _disable(table):
    t = '"%s"' % table
    return (
        f'DROP POLICY IF EXISTS tenant_isolation ON {t};\n'
        f'ALTER TABLE {t} DISABLE ROW LEVEL SECURITY;'
    )


class Migration(migrations.Migration):

    dependencies = [("osp_core", "0001_initial")]

    operations = [
        migrations.RunSQL(sql=_enable(t), reverse_sql=_disable(t)) for t in _TABLES
    ]
