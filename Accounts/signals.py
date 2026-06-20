"""Signal handlers for the Accounts app.

As of the Firebase migration, Accounts.views.verify_firebase_token is the
only real front door and already creates/updates Profile directly — but
this stays as a safety net for any User created outside that path (e.g.
`manage.py createsuperuser`, or a future admin-created account), so
Profile-dependent templates (main_nav.html's avatar, dashboard) never hit
a missing-Profile error.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=get_user_model())
def ensure_profile_exists(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={"email": instance.email or "", "title": "New User"},
        )


@receiver(user_logged_in)
def backfill_profile_email(sender, request, user, **kwargs):
    """Keep Profile.email aligned with the auth email for any login path
    that doesn't already set it explicitly (verify_firebase_token does)."""
    profile, _ = Profile.objects.get_or_create(
        user=user, defaults={"email": user.email or "", "title": "New User"}
    )
    if user.email and profile.email != user.email:
        profile.email = user.email
        profile.save(update_fields=["email"])
