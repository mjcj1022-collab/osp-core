"""
Shared data API — the endpoints every suite app calls to read/write the
canonical entities (projects, poles, attachments). Enter a pole in Make-Ready
and BIM sees the same pole here; REDLINE hangs a work order off the same project.

Isolation is enforced twice: Postgres row-level security keyed to the caller's
tenant (migration 0002), plus this app-layer tenant filter as a belt.
"""
from rest_framework import viewsets

from .models import Project, Pole, Attachment
from .permissions import _tenant_id
from .serializers import ProjectSerializer, PoleSerializer, AttachmentSerializer


class TenantScopedViewSet(viewsets.ModelViewSet):
    """Confines every query and write to the authenticated caller's tenant and
    hides soft-deleted rows. Subclasses set `queryset` + `serializer_class`."""

    def get_queryset(self):
        tid = _tenant_id(self.request)
        if tid is None:
            return self.queryset.none()
        return self.queryset.filter(tenant_id=tid, deleted_at__isnull=True)

    def perform_create(self, serializer):
        tid = _tenant_id(self.request)
        email = getattr(self.request.user, "email", "") or ""
        serializer.save(tenant_id=tid, created_by=email, updated_by=email)

    def perform_update(self, serializer):
        email = getattr(self.request.user, "email", "") or ""
        serializer.save(updated_by=email)

    def perform_destroy(self, instance):
        # Soft delete: keep the row, mark it gone (apps filter deleted_at).
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at", "updated_at"])


class ProjectViewSet(TenantScopedViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class PoleViewSet(TenantScopedViewSet):
    queryset = Pole.objects.all()
    serializer_class = PoleSerializer


class AttachmentViewSet(TenantScopedViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
