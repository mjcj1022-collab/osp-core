"""
Include in any app's root urls:
    path("", include("osp_core.urls")),
Exposes GET /api/me/entitlements/
"""
from django.urls import path

from .views import MeEntitlementsView

urlpatterns = [
    path("api/me/entitlements/", MeEntitlementsView.as_view(), name="me-entitlements"),
]
