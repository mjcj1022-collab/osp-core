"""
osp_core.models — the canonical, shared entities for the OSP suite.

Every app (Make-Ready, REDLINE, BIM, ODEN) imports this package and reads/writes
these tables. They live in the Postgres `core` schema (db_table = 'core"."x'), so
each app's own tables stay in its own schema. ONLY this package migrates `core`.

Shared identity lives here; app-specific detail lives in the app's own schema
keyed to these ids. See FIELD-OWNERSHIP.md.
"""
from django.db import models

APP_CHOICES = [
    ("makeready", "Make-Ready Workstation"),
    ("redline", "REDLINE"),
    ("bim", "Light Speed BIM"),
    ("oden", "ODEN"),
]


class TimeStamped(models.Model):
    """Timestamps + soft-delete + who-touched-it on every core row.
    Soft delete: set deleted_at instead of DELETE; app querysets should filter
    deleted_at__isnull=True. created_by/updated_by hold the actor's email."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=200, blank=True)
    updated_by = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True


class Tenant(TimeStamped):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        db_table = 'core"."tenant'

    def __str__(self):
        return self.slug


class User(TimeStamped):
    """Platform user profile. Authentication is external (IdP JWT); this row is the
    stable local identity the IdP subject maps to. NOT Django's AUTH_USER_MODEL."""
    email = models.EmailField(unique=True)
    external_id = models.CharField(max_length=255, blank=True, db_index=True)  # IdP `sub`
    display_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core"."user'

    def __str__(self):
        return self.email


class TenantScoped(TimeStamped):
    """Base: every row belongs to exactly one tenant (indexed)."""
    tenant = models.ForeignKey("osp_core.Tenant", on_delete=models.CASCADE, related_name="+", db_index=True)

    class Meta:
        abstract = True


class Membership(TenantScoped):
    """Which users belong to which tenant, and their role there.
    A user can belong to multiple tenants (one Membership each)."""
    ROLE_CHOICES = [("admin", "Admin"), ("member", "Member"), ("viewer", "Viewer")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    class Meta:
        db_table = 'core"."membership'
        unique_together = [("tenant", "user")]


class Entitlement(TenantScoped):
    """Which apps a tenant has bought. Source of truth for packaging/pricing."""
    app = models.CharField(max_length=20, choices=APP_CHOICES)
    tier = models.CharField(max_length=40, default="standard")
    active = models.BooleanField(default=True)
    seats = models.PositiveIntegerField(default=0)  # 0 = unlimited/unset
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'core"."entitlement'
        unique_together = [("tenant", "app")]


class Project(TenantScoped):
    """The 'job'. job_number is the natural cross-app key + deep-link handle."""
    job_number = models.CharField(max_length=80)
    name = models.CharField(max_length=300, blank=True)
    client = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=40, default="active")
    geo = models.JSONField(null=True, blank=True)  # optional bbox/centroid
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core"."project'
        unique_together = [("tenant", "job_number")]
        indexes = [models.Index(fields=["job_number"], name="core_project_jobnum_idx")]


class Pole(TenantScoped):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="poles")
    tag = models.CharField(max_length=120)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    # NOTE: a PostGIS `geom geography(Point,4326)` column is added by migration 0003,
    # generated from (lng, lat), with a GIST index — for spatial queries without
    # requiring GeoDjango/GDAL in the app.
    owner = models.CharField(max_length=120, blank=True)
    height_ft = models.FloatField(null=True, blank=True)
    pole_class = models.CharField(max_length=40, blank=True)

    class Meta:
        db_table = 'core"."pole'
        unique_together = [("tenant", "project", "tag")]
        indexes = [models.Index(fields=["tag"], name="core_pole_tag_idx")]


class Attachment(TenantScoped):
    """A wire/equipment attachment on a pole (the shared make-ready primitive)."""
    pole = models.ForeignKey(Pole, on_delete=models.CASCADE, related_name="attachments")
    kind = models.CharField(max_length=60)                 # power, comm, fiber, streetlight...
    height_ft = models.FloatField(null=True, blank=True)
    owner = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'core"."attachment'


class Audit(TenantScoped):
    actor = models.CharField(max_length=200)
    entity = models.CharField(max_length=60)
    entity_id = models.CharField(max_length=80)
    action = models.CharField(max_length=60)
    meta = models.JSONField(default=dict, blank=True)
    ts = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core"."audit'
        indexes = [models.Index(fields=["entity", "entity_id"], name="core_audit_entity_idx")]
