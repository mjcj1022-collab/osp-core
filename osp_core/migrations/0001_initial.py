"""
Initial schema for osp_core. Creates the Postgres `core` schema first, then the
canonical tables inside it.

NOTE: this migration is hand-authored to match models.py. Before relying on it in
a host project, run `python manage.py makemigrations --check osp_core` there to
confirm it matches (regenerate if your Django version differs).
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE SCHEMA IF NOT EXISTS core;",
            reverse_sql="DROP SCHEMA IF EXISTS core CASCADE;",
        ),
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": 'core"."tenant'},
        ),
        migrations.CreateModel(
            name="Entitlement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("app", models.CharField(choices=[("makeready", "Make-Ready Workstation"), ("redline", "REDLINE"), ("bim", "Light Speed BIM"), ("oden", "ODEN")], max_length=20)),
                ("tier", models.CharField(default="standard", max_length=40)),
                ("active", models.BooleanField(default=True)),
                ("seats", models.PositiveIntegerField(default=0)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="osp_core.tenant")),
            ],
            options={"db_table": 'core"."entitlement', "unique_together": {("tenant", "app")}},
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("job_number", models.CharField(max_length=80)),
                ("name", models.CharField(blank=True, max_length=300)),
                ("client", models.CharField(blank=True, max_length=200)),
                ("status", models.CharField(default="active", max_length=40)),
                ("geo", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="osp_core.tenant")),
            ],
            options={"db_table": 'core"."project', "unique_together": {("tenant", "job_number")}},
        ),
        migrations.CreateModel(
            name="Pole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tag", models.CharField(max_length=120)),
                ("lat", models.FloatField(blank=True, null=True)),
                ("lng", models.FloatField(blank=True, null=True)),
                ("owner", models.CharField(blank=True, max_length=120)),
                ("height_ft", models.FloatField(blank=True, null=True)),
                ("pole_class", models.CharField(blank=True, max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="poles", to="osp_core.project")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="osp_core.tenant")),
            ],
            options={"db_table": 'core"."pole', "unique_together": {("tenant", "project", "tag")}},
        ),
        migrations.CreateModel(
            name="Attachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(max_length=60)),
                ("height_ft", models.FloatField(blank=True, null=True)),
                ("owner", models.CharField(blank=True, max_length=120)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("pole", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="osp_core.pole")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="osp_core.tenant")),
            ],
            options={"db_table": 'core"."attachment'},
        ),
        migrations.CreateModel(
            name="Audit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("actor", models.CharField(max_length=200)),
                ("entity", models.CharField(max_length=60)),
                ("entity_id", models.CharField(max_length=80)),
                ("action", models.CharField(max_length=60)),
                ("meta", models.JSONField(blank=True, default=dict)),
                ("ts", models.DateTimeField(auto_now_add=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="+", to="osp_core.tenant")),
            ],
            options={"db_table": 'core"."audit'},
        ),
    ]
