from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # The uploaded images will be stored in MEDIA_ROOT/profiles/
    profile_img = models.ImageField(upload_to="profiles/", blank=True, null=True)
    email = models.EmailField()
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    # Firebase Authentication (replaces django-allauth this session).
    # firebase_uid links this User to the Firebase account that owns it —
    # it's how verify-token/ finds an existing user on repeat logins.
    # email_verified mirrors Firebase's own claim (set by Firebase itself
    # for password sign-ups that complete email verification, and always
    # true for Google/GitHub since those providers already verified it) —
    # mpesa's is_email_verified() now reads this instead of allauth's
    # EmailAddress model.
    firebase_uid = models.CharField(max_length=128, blank=True, null=True, unique=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    auth_provider = models.CharField(max_length=20, blank=True, default="password")

    def __str__(self):
        return self.user.username
