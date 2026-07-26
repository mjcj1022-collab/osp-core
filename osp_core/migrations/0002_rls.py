"""
Row-Level Security for the core tables. Each request sets `app.tenant_id`
(see middleware.py); these policies ensure a connection can only see/modify rows
for that tenant -- DB-enforced isolation, independent of app code.

IMPORTANT: the DB role your apps connect as must NOT own the tables as superuser
(superusers/owners bypass RLS). FORCE ROW LEVEL SECURITY below makes even the
owner obey the policy. Run migrations as an admin role, connect apps as a
non-superuser role.
"""
from django.db import migrations

_TID = "NULLIF(current_setting('app.tenant_id', true), '')::bigint"

# (table, tenant-column-expression)
_TABLES = [
    ('core"."tenant', "id"),
    ('core"."entitlement', "tenant_id"),
    ('core"."project', "tenant_id"),
    ('core"."pole', "tenant_id"),
    ('core"."attachment', "tenant_id"),
    ('core"."audit', "tenant_id"),
]


def _enable(table, col):
    t = '"%s"' % table  # -> "core"."x"
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
