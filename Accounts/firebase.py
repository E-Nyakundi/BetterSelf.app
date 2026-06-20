"""Firebase Admin SDK wiring — replaces django-allauth as of this session.

Why: django-allauth handled email/password + Google/GitHub/Facebook social
login, email verification, and password reset, all through its own
`/accounts/...` URLconf and `EmailAddress` model. Per the brief, that's
gone now — Firebase Authentication does all of it instead:

- Email/password and Google/GitHub sign-in happen client-side via the
  Firebase Web SDK (see Accounts/templates/Accounts/login.html and
  create_user.html), which returns a Firebase ID token.
- The browser POSTs that ID token to `verify-token/` (Accounts/views.py),
  which uses this module to verify it server-side, then creates/updates
  a matching Django `User` + `Profile` and logs them in with Django's own
  session auth. Every other view in the project (`@login_required`,
  `LoginRequiredMixin`, `request.user`) keeps working exactly as before —
  only the front door changed.

Dev mode: if FIREBASE_PRIVATE_KEY is missing/empty, the module falls back
to a lightweight "dev bypass" mode: verify_id_token() accepts any non-empty
string as if it were a valid token and returns a synthetic decoded payload
derived from the token string itself (expected format: "dev:<email>").
This lets local development proceed without a real Firebase project.
NEVER ship with DJANGO_DEBUG=False and missing Firebase credentials.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_app = None
_firebase_available = None  # cached after first _check()


class FirebaseNotConfigured(Exception):
    """Raised when required FIREBASE_* env vars are missing in production."""


def _is_dev_mode():
    """True when Firebase credentials are absent — only permitted in DEBUG."""
    key = getattr(settings, "FIREBASE_PRIVATE_KEY", "") or ""
    email = getattr(settings, "FIREBASE_CLIENT_EMAIL", "") or ""
    project = getattr(settings, "FIREBASE_PROJECT_ID", "") or ""
    return not (key.strip() and email.strip() and project.strip())


def _build_credentials():
    required = {
        "type": "service_account",
        "project_id": settings.FIREBASE_PROJECT_ID,
        "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
        "private_key": settings.FIREBASE_PRIVATE_KEY,
        "client_email": settings.FIREBASE_CLIENT_EMAIL,
        "client_id": settings.FIREBASE_CLIENT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": (
            f"https://www.googleapis.com/robot/v1/metadata/x509/"
            f"{settings.FIREBASE_CLIENT_EMAIL}"
        ),
        "universe_domain": "googleapis.com",
    }
    missing = [k for k in ("project_id", "private_key", "client_email") if not required[k]]
    if missing:
        raise FirebaseNotConfigured(
            f"Missing Firebase service-account env vars: {', '.join(missing)}. "
            "Set FIREBASE_PROJECT_ID / FIREBASE_PRIVATE_KEY / FIREBASE_CLIENT_EMAIL in .env."
        )
    try:
        from firebase_admin import credentials
        return credentials.Certificate(required)
    except ImportError:
        raise FirebaseNotConfigured("firebase-admin package is not installed.")


def get_firebase_app():
    """Lazily initialize the Admin SDK app (once per process)."""
    global _app
    if _app is None:
        try:
            import firebase_admin
            _app = firebase_admin.initialize_app(_build_credentials())
        except ImportError:
            raise FirebaseNotConfigured("firebase-admin package is not installed.")
    return _app


def verify_id_token(id_token):
    """Verify a client-supplied Firebase ID token.

    In dev mode (missing credentials + DEBUG=True), accepts any token of
    the form "dev:<email>" and returns a synthetic decoded payload — so
    local sign-in works without a real Firebase project.

    In production, delegates to firebase_admin.auth.verify_id_token().
    Raises firebase_admin.auth errors or FirebaseNotConfigured on failure.
    """
    if _is_dev_mode():
        if not settings.DEBUG:
            raise FirebaseNotConfigured(
                "Firebase credentials are not configured. "
                "Set FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, and FIREBASE_CLIENT_EMAIL in .env."
            )
        # Dev bypass: token format is "dev:<email>" or any string (treated as email)
        logger.warning(
            "Firebase dev-bypass active: accepting token without real verification. "
            "This MUST NOT happen in production (set DEBUG=False + real Firebase creds)."
        )
        if isinstance(id_token, str) and id_token.startswith("dev:"):
            email = id_token[4:].strip() or "dev@localhost.dev"
        else:
            # Treat the whole token as email for easy manual testing
            email = id_token if "@" in str(id_token) else "dev@localhost.dev"
        uid = f"dev-{email.replace('@', '-').replace('.', '-')}"
        return {
            "uid": uid,
            "email": email,
            "email_verified": True,
            "name": "",
            "firebase": {"sign_in_provider": "password"},
        }

    try:
        app = get_firebase_app()
        from firebase_admin import auth as firebase_auth
        return firebase_auth.verify_id_token(id_token, app=app, check_revoked=False)
    except FirebaseNotConfigured:
        raise
    except Exception:
        raise
