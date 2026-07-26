"""
osp_core.models — the canonical, shared entities for the OSP suite.

Every app (Make-Ready, REDLINE, BIM, ODEN) imports this package and reads/writes
these tables. They live in the Postgres `core` schema (db_table = 'core"."x'), so
each app's own tables stay in its own schema. ONLY this package migrates `core`.

Rule of thumb: shared identity lives here; app-specific detail lives in the app's
own schema keyed to these ids. See FIELD-OWNERSHIP.md for who writes what.
"""
from django.db import models

APP_CHOICES = [
    ("makeready", "Make-Ready Workstation"),
    ("redline", "REDLINE"),
    ("bim", "Light Speed BIM"),
    ("oden", "ODEN"),
]


class TenantScoped(models.Model):
    """Base: every row belongs to exactly one tenant."""
    tenant = models.ForeignKey("osp_core.Tenant", on_delete=models.CASCADE, related_name="+")

    class Meta:
        abstract = True


class Tenant(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core"."tenant'

    def __str__(self):
        return self.slug


class Entitlement(TenantScoped):
    """Which apps a tenant has bought. Source of truth for packaging/pricing.
    Billing (Stripe) later just flips `active`; no app code changes."""
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


class Pole(TenantScoped):
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="poles")
    tag = models.CharField(max_length=120)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    owner = models.CharField(max_length=120, blank=True)   # utility that owns the pole
    height_ft = models.FloatField(null=True, blank=True)
    pole_class = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core"."pole'
        unique_together = [("tenant", "project", "tag")]


class Attachment(TenantScoped):
    """A wire/equipment attachment on a pole (the shared make-ready primitive)."""
    pole = models.ForeignKey(Pole, on_delete=models.CASCADE, related_name="attachments")
    kind = models.CharField(max_length=60)                 # power, comm, fiber, streetlight...
    height_ft = models.FloatField(null=True, blank=True)
    owner = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
