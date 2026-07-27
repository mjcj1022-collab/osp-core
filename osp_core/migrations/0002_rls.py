"""
Row-Level Security for the tenant-scoped core tables. Each request sets
`app.tenant_id` (see middleware.py); these policies ensure a connection only
sees/modifies rows for that tenant. FORCE makes even the table owner obey.

core.user is intentionally excluded -- it's global identity (no tenant_id); access
to it is mediated by Membership + app logic.

Requires the connecting role to be NON-superuser (superusers bypass RLS).
"""
from django.db import migrations

_TID = "NULLIF(current_setting('app.tenant_id', true), '')::bigint"

# (table, tenant-column-expression)
_TABLES = [
    ('core"."tenant', "id"),
    ('core"."membership', "tenant_id"),
    ('core"."entitlement', "tenant_id"),
    ('core"."project', "tenant_id"),
    ('core"."pole', "tenant_id"),
    ('core"."attachment', "tenant_id"),
    ('core"."audit', "tenant_id"),
]


def _enable(table, col):
    t = '"%s"' % table
    return (
        f'ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;\n'
        f'ALTER TABLE {t} FORCE ROW LEVEL SECURITY;\n'
        f'DROP POLICY IF EXISTS tenant_isolation ON {t};\n'
        f'CREATE POLICY tenant_isolation ON {t}\n'
        f'  USING ({col} = {_TID})\n'
        f'  WITH CHECK ({col} = {_TID});'
    )


def _disable(table):
    t = '"%s"' % table
    return (
        f'DROP POLICY IF EXISTS tenant_isolation ON {t};\n'
        f'ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY;\n'
        f'ALTER TABLE {t} DISABLE ROW LEVEL SECURITY;'
    )


class Migration(migrations.Migration):

    dependencies = [("osp_core", "0001_initial")]

    operations = [
        migrations.RunSQL(sql=_enable(tbl, col), reverse_sql=_disable(tbl))
        for tbl, col in _TABLES
    ]
