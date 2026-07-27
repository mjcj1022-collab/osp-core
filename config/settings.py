"""
Settings for the OSP shared backend — the single service that BIM, REDLINE,
Make-Ready (and ODEN) all call. One service, one database, one auth +
entitlements layer.

Everything sensitive is env-driven so nothing secret lives in the repo:
  SECRET_KEY           Django secret (any long random string)
  DATABASE_URL         Postgres connection string (the ONE shared database)
  GOTRUE_JWT_SECRET    Netlify Identity JWT secret (verifies logins)
  DEBUG                "true"/"false" (default false)
  ALLOWED_HOSTS        comma-separated hostnames (default "*")
  CORS_ALLOWED_ORIGINS comma-separated front-end origins
"""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def _bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _list(name, default=""):
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
DEBUG = _bool("DEBUG", False)
ALLOWED_HOSTS = _list("ALLOWED_HOSTS", "*") or ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "osp_core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    # Sets Postgres app.tenant_id so row-level security isolates tenants at the DB.
    "osp_core.middleware.TenantRLSMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# One shared database. Requires Postgres (RLS + PostGIS migrations).
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL", ""),
        conn_max_age=600,
        ssl_require=_bool("DB_SSL_REQUIRE", False),
    )
}

# API-only service: token auth via Netlify Identity, JSON responses.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "osp_core.authentication.NetlifyIdentityAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "UNAUTHENTICATED_USER": None,
}

# CORS: only the suite's front-ends may call the API from the browser.
CORS_ALLOWED_ORIGINS = _list(
    "CORS_ALLOWED_ORIGINS",
    "https://light-speed-bim.netlify.app,"
    "https://redline-app.netlify.app,"
    "https://courageous-seahorse-d21112.netlify.app,"
    "https://lucky-basbousa-c909b8.netlify.app",
)
CORS_ALLOW_CREDENTIALS = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"

# Behind Render/Netlify TLS termination.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
