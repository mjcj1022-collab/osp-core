"""
DRF serializers for the shared core entities. `tenant`, timestamps and the
who-touched-it fields are server-controlled (set from the authenticated caller),
never accepted from the client.
"""
from rest_framework import serializers

from .models import Project, Pole, Attachment


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "job_number", "name", "client", "status", "geo",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pole
        fields = ["id", "project", "tag", "lat", "lng", "owner", "height_ft",
                  "pole_class", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "pole", "kind", "height_ft", "owner", "notes",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
