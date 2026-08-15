from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from BetterSelf.thumbnails import refresh_thumbnail, image_field_changed


class JournalEntry(models.Model):
    SCALE_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='journal',
        null=True, blank=True
    )
    days_date = models.DateField()
    time_of_day = models.TimeField(auto_now_add=True)
    entry = models.TextField(null=True, blank=True)

    # Reflection metrics — simple 1-5 self-rated scales, lightweight enough
    # to fill in every day without friction, rich enough to trend over time.
    mood = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=SCALE_VALIDATORS,
        help_text="How are you feeling overall? 1 = rough day, 5 = great day."
    )
    energy = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=SCALE_VALIDATORS,
        help_text="Physical and mental energy levels today."
    )
    focus = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=SCALE_VALIDATORS,
        help_text="How clear-headed and focused you felt."
    )
    sleep_hours = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text="Hours of sleep last night."
    )
    went_well = models.TextField(
        null=True, blank=True,
        help_text="What went well today?"
    )
    needs_improvement = models.TextField(
        null=True, blank=True,
        help_text="What needs improvement?"
    )

    # Media fields
    image = models.ImageField(upload_to='journal/images/', null=True, blank=True)
    thumbnail = models.ImageField(
        upload_to='journal/images/thumbs/',
        null=True, blank=True, editable=False,
        help_text="Auto-generated small preview of `image` — don't set this directly."
    )
    video = models.FileField(upload_to='journal/videos/', null=True, blank=True)
    audio = models.FileField(upload_to='journal/audio/', null=True, blank=True)
    document = models.FileField(upload_to='journal/documents/', null=True, blank=True)

    def __str__(self):
        return f"{self.days_date} - {self.entry[:30] if self.entry else 'Media Entry'}"

    def save(self, *args, **kwargs):
        needs_thumb = image_field_changed(self, 'image')
        super().save(*args, **kwargs)
        if needs_thumb:
            refresh_thumbnail(self.image, self.thumbnail)
            super().save(update_fields=['thumbnail'])
