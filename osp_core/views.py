"""
Shared endpoint every app backend exposes: what apps does the current tenant have?
The suite launcher (static/suite-launcher.js) reads this to show/hide apps.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Entitlement
from .permissions import _tenant_id


class MeEntitlementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tid = _tenant_id(request)
        if tid is None:
            return Response({"tenant": None, "apps": []})
        ents = Entitlement.objects.filter(tenant_id=tid, active=True)
        return Response({
            "tenant": tid,
            "apps": [
                {"app": e.app, "tier": e.tier, "seats": e.seats}
                for e in ents
            ],
        })
