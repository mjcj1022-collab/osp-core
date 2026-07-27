"""
PostGIS geo for poles WITHOUT requiring GeoDjango/GDAL in the apps.

Enables the postgis extension and adds `core.pole.geom` -- a geography(Point,4326)
column GENERATED from (lng, lat) -- plus a GIST index. Django keeps using the
plain lat/lng floats; spatial queries (nearest, within-bbox, etc.) use `geom` via
raw SQL. Supabase has PostGIS available.
"""
from django.db import migrations

# Tolerant: if the database can't provide PostGIS (some managed Postgres tiers
# block CREATE EXTENSION), skip the geom column instead of failing the whole
# deploy. The core API doesn't need geom; lat/lng floats are always stored.
_ADD = """
DO $$
BEGIN
  CREATE EXTENSION IF NOT EXISTS postgis;
  ALTER TABLE "core"."pole"
    ADD COLUMN IF NOT EXISTS geom geography(Point, 4326)
    GENERATED ALWAYS AS (
      CASE
        WHEN lng IS NOT NULL AND lat IS NOT NULL
        THEN ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography
      END
    ) STORED;
  CREATE INDEX IF NOT EXISTS core_pole_geom_gix ON "core"."pole" USING GIST (geom);
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'PostGIS unavailable (%); skipping geom column. lat/lng still stored.', SQLERRM;
END $$;
"""

_DROP = """
DROP INDEX IF EXISTS core.core_pole_geom_gix;
ALTER TABLE "core"."pole" DROP COLUMN IF EXISTS geom;
"""


class Migration(migrations.Migration):

    dependencies = [("osp_core", "0002_rls")]

    operations = [
        migrations.RunSQL(sql=_ADD, reverse_sql=_DROP),
    ]
