"""
URL map for the OSP shared backend.

  GET  /healthz                     liveness (no auth)
  GET  /api/me/entitlements/        which apps this tenant has (suite launcher)
  /api/projects/  /api/poles/  /api/attachments/   shared data (CRUD, tenant-scoped)

Each app's specialized endpoints get mounted here too as they're folded in
(e.g. /api/makeready/, /api/redline/, /api/bim/).
"""
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from osp_core.api import ProjectViewSet, PoleViewSet, AttachmentViewSet


def healthz(_request):
    return JsonResponse({"status": "ok", "service": "osp-shared-backend"})


router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"poles", PoleViewSet, basename="pole")
router.register(r"attachments", AttachmentViewSet, basename="attachment")

urlpatterns = [
    path("healthz", healthz),
    path("", include("osp_core.urls")),   # /api/me/entitlements/
    path("api/", include(router.urls)),
]
