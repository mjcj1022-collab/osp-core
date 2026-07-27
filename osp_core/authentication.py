"""
NetlifyIdentityAuthentication — turns a Netlify Identity JWT into a platform
identity, on every request:

  1. Verify the JWT (HS256) with GOTRUE_JWT_SECRET.
  2. Read email, sub, and app_metadata.roles (which carry `tenant:<slug>` + roles).
  3. Upsert core.User + core.Membership (identity tables are NOT under RLS, so this
     works before any tenant context is set).
  4. SET app.tenant_id on the connection so RLS on the DATA tables isolates the
     request to this tenant.
  5. Return the core.User (as request.user) with .tenant_id / .roles attached.

Wire in settings:
    REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES":
        ["osp_core.authentication.NetlifyIdentityAuthentication"]}
Env: GOTRUE_JWT_SECRET (from Netlify Identity → your site's JWT secret).
"""
import os
import re

import jwt
from django.db import connection
from rest_framework import authentication, exceptions

from .models import Tenant, User, Membership

_TENANT_RE = re.compile(r"^tenant:(.+)$")
_ROLE_RANK = {"admin": 3, "member": 2, "viewer": 1}


def set_pg_tenant(tenant_id):
    """Set the Postgres session var RLS policies read (see migration 0002)."""
    with connection.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id', %s, false)", [str(tenant_id)])


class NetlifyIdentityAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith(self.keyword + " "):
            return None  # anonymous; let permissions decide
        token = header[len(self.keyword) + 1:].strip()

        secret = os.environ.get("GOTRUE_JWT_SECRET") or os.environ.get("NETLIFY_JWT_SECRET")
        if not secret:
            raise exceptions.AuthenticationFailed("Identity JWT secret not configured on server")
        try:
            claims = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_aud": False})
        except jwt.PyJWTError as e:
            raise exceptions.AuthenticationFailed("Invalid token: %s" % e)

        email = claims.get("email")
        if not email:
            raise exceptions.AuthenticationFailed("Token has no email")
        sub = claims.get("sub", "")
        roles = (claims.get("app_metadata") or {}).get("roles") or []

        tenant_slugs = [m.group(1) for r in roles
                        if isinstance(r, str) for m in [_TENANT_RE.match(r)] if m]
        if len(tenant_slugs) != 1:
            raise exceptions.AuthenticationFailed("Exactly one tenant:<slug> role required")
        slug = tenant_slugs[0]

        app_roles = [r for r in roles if isinstance(r, str) and not _TENANT_RE.match(r)]
        role = "member"
        for r in app_roles:
            if _ROLE_RANK.get(r, 0) > _ROLE_RANK.get(role, 0):
                role = r

        # Upsert identity (these tables are not under RLS).
        tenant, _ = Tenant.objects.get_or_create(slug=slug, defaults={"name": slug})
        display = (claims.get("user_metadata") or {}).get("full_name", "")
        user, created = User.objects.get_or_create(
            email=email, defaults={"external_id": sub, "display_name": display}
        )
        if sub and user.external_id != sub:
            user.external_id = sub
            user.save(update_fields=["external_id"])
        Membership.objects.update_or_create(
            tenant=tenant, user=user, defaults={"role": role}
        )

        # Now scope the connection for RLS on the data tables.
        set_pg_tenant(tenant.id)

        user.tenant_id = tenant.id
        user.roles = app_roles
        return (user, token)
