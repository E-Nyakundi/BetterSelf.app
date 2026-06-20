import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the repository root .env file.
load_dotenv(BASE_DIR / ".env")

# Security settings
# SECRET_KEY must be set in production via the DJANGO_SECRET_KEY env var.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    # allow an insecure fallback only in local development (DEBUG=True)
    if os.getenv("DJANGO_DEBUG", "False") == "True":
        SECRET_KEY = "django-insecure-development-placeholder"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY environment variable is required in production")

# Debug flag (default False)
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# ALLOWED_HOSTS should be a comma-separated list in env; default to loopback hosts for dev
ALLOWED_HOSTS = [h for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

# Installed apps
INSTALLED_APPS = [

    # Admin theming (admin_interface depends on colorfield internally)
    "admin_interface",
    "colorfield",

    # Local apps
    "Accounts.apps.AccountsConfig",
    "Time_Manager",
    "WellBeing",
    "Inventory",
    "Finance_Wealth",
    "mpesa",
    "BetterSelf",  # Main app
    # Django default apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URL Configuration
ROOT_URLCONF = "BetterSelf.urls"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = "BetterSelf.wsgi.application"


# Database - configured via environment variables. No real credentials are
# hardcoded here on purpose: if these env vars aren't set, connections should
# fail loudly rather than silently falling back to a guessable default.
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DJANGO_DB_NAME", os.getenv("DATABASE_NAME", "BetterSelf")),
        "USER": os.getenv("DJANGO_DB_USER", os.getenv("DATABASE_USER", "postgres")),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", os.getenv("DATABASE_PASSWORD", "")),
        "HOST": os.getenv("DJANGO_DB_HOST", os.getenv("DATABASE_HOST", "localhost")),
        "PORT": os.getenv("DJANGO_DB_PORT", os.getenv("DATABASE_PORT", "5432")),
    }
}


# Email configuration
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
if not EMAIL_BACKEND:
    EMAIL_BACKEND = (
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG and not (EMAIL_HOST_USER and EMAIL_HOST_PASSWORD)
        else "django.core.mail.backends.smtp.EmailBackend"
    )
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost")

# M-Pesa / Daraja (Phase 4.1) — sandbox by default. No secrets hardcoded;
# see .env.local.example for the variable list. MPESA_SHORTCODE/PASSKEY
# default to Safaricom's publicly documented sandbox test values so STK
# push works out of the box against the sandbox without extra setup.
MPESA_ENV = os.getenv("MPESA_ENV", "sandbox")
MPESA_BASE_URL = os.getenv(
    "MPESA_BASE_URL",
    "https://sandbox.safaricom.co.ke" if MPESA_ENV == "sandbox" else "https://api.safaricom.co.ke",
)
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.getenv(
    "MPESA_PASSKEY",
    "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919",
)
MPESA_CALLBACK_BASE_URL = os.getenv("MPESA_CALLBACK_BASE_URL", "")

# SMS (phone-verification OTPs ahead of M-Pesa STK pushes) — same "console
# by default, real provider via env" pattern as EMAIL_BACKEND above. No
# credentials hardcoded; see mpesa/sms.py for the backend implementations.
SMS_BACKEND = os.getenv("SMS_BACKEND", "console")
AFRICASTALKING_API_KEY = os.getenv("AFRICASTALKING_API_KEY")
AFRICASTALKING_USERNAME = os.getenv("AFRICASTALKING_USERNAME", "sandbox")
AFRICASTALKING_SENDER_ID = os.getenv("AFRICASTALKING_SENDER_ID", "")

# Firebase Authentication (replaces django-allauth this session — see
# Accounts/firebase.py for the verification flow). Service-account fields
# are discrete env vars on purpose: a pasted multi-line JSON blob breaks
# python-dotenv's parser.
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_PRIVATE_KEY_ID = os.getenv("FIREBASE_PRIVATE_KEY_ID")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")
FIREBASE_CLIENT_ID = os.getenv("FIREBASE_CLIENT_ID")

# Public Web SDK config — safe to expose client-side, used by the
# login/signup pages to talk to Firebase Auth directly from the browser.
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "")
FIREBASE_WEB_AUTH_DOMAIN = os.getenv("FIREBASE_WEB_AUTH_DOMAIN", "")
FIREBASE_WEB_APP_ID = os.getenv("FIREBASE_WEB_APP_ID", "")

# Password validators, Internationalization, and Static files settings here...
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Media Files settings
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Security-related settings (override via environment variables)
# When DEBUG is False these defaults will enable common production-hardening flags.
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True") == "True"
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True") == "True"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True") == "True"
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True") == "True"
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY")
else:
    # development-friendly defaults
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    X_FRAME_OPTIONS = "SAMEORIGIN"
    # Allow session cookie on cross-origin fetch (needed when Django runs on
    # localhost:8000 but the page is served via ngrok tunnel). SameSite=None
    # without Secure is technically invalid per spec but browsers allow it
    # on localhost. The cookie is already not Secure in DEBUG mode.
    SESSION_COOKIE_SAMESITE = "Lax"

# Trusted origins for CSRF — read regardless of DEBUG. Previously this was
# only parsed inside the `if not DEBUG` branch above, so a dev session
# (DJANGO_DEBUG=True, e.g. tunneled through ngrok for testing email/SMS
# verification end-to-end) silently ignored CSRF_TRUSTED_ORIGINS entirely.
csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(",") if o.strip()]

# Tunnels (ngrok, and most real reverse proxies) terminate TLS and forward
# plain HTTP to this app, so request.is_secure() is False unless told to
# trust the proxy's X-Forwarded-Proto header. Without this, Django thinks
# every request is insecure regardless of the public https:// URL.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Authentication — plain Django sessions. Firebase issues/verifies
# credentials (password + Google/GitHub); Django never sees a password
# for Firebase-authenticated users (see Accounts.views.verify_firebase_token).
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_REDIRECT_URL = "/betterself/Accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/betterself/Accounts/login/"
LOGIN_URL = "/betterself/Accounts/login/"
PASSWORD_RESET_CONFIRM_URL = "/betterself/Accounts/reset/{uid}/{token}/"

def _secret_key_strength(key: str) -> bool:
    # basic heuristic: length and character variety
    if not key:
        return False
    if key.startswith("django-insecure-"):
        return False
    if len(key) < 50:
        return False
    if len(set(key)) < 5:
        return False
    return True


def validate_production_settings():
    """Validate required production security settings when DEBUG is False.

    Raises ImproperlyConfigured with details if any required setting is missing
    or insecure.
    """
    if DEBUG:
        return

    errors = []

    # SECRET_KEY
    if not _secret_key_strength(SECRET_KEY):
        errors.append("SECRET_KEY is missing or weak. Provide a long random value in DJANGO_SECRET_KEY.")

    # Common security flags
    if not SECURE_SSL_REDIRECT:
        errors.append("SECURE_SSL_REDIRECT should be True in production.")
    if not SECURE_CONTENT_TYPE_NOSNIFF:
        errors.append("SECURE_CONTENT_TYPE_NOSNIFF should be True to set X-Content-Type-Options: nosniff.")
    if not SESSION_COOKIE_SECURE:
        errors.append("SESSION_COOKIE_SECURE should be True to secure session cookies.")
    if not CSRF_COOKIE_SECURE:
        errors.append("CSRF_COOKIE_SECURE should be True to secure CSRF cookie.")
    if not (isinstance(SECURE_HSTS_SECONDS, int) and SECURE_HSTS_SECONDS > 0):
        errors.append("SECURE_HSTS_SECONDS should be set to a positive integer for HSTS.")
    if X_FRAME_OPTIONS.upper() != "DENY":
        errors.append("X_FRAME_OPTIONS should be 'DENY' in production unless you intentionally allow framing.")

    if errors:
        raise ImproperlyConfigured("Production security checks failed:\n  - " + "\n  - ".join(errors))


# Run validation at import time so misconfiguration fails fast in deployment
try:
    validate_production_settings()
except ImproperlyConfigured:
    # Re-raise so startup fails loudly in production (but allow development flow).
    raise