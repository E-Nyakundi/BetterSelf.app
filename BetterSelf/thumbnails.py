"""
Shared helper for generating lightweight thumbnails from an uploaded image.

Used by any model that stores a photo and wants a small, fast-loading
version for list/grid views — full-resolution originals are only loaded
when someone opens the detail view.
"""
import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image

THUMBNAIL_SIZE = (400, 400)
THUMBNAIL_QUALITY = 82


def refresh_thumbnail(image_field, thumbnail_field):
    """
    Regenerate `thumbnail_field` from `image_field`.

    If `image_field` is empty, any existing thumbnail is removed instead.
    Caller is responsible for saving the field afterwards
    (e.g. `instance.save(update_fields=['thumbnail'])`).
    """
    if not image_field:
        if thumbnail_field:
            thumbnail_field.delete(save=False)
        return

    image_field.open()
    img = Image.open(image_field)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.thumbnail(THUMBNAIL_SIZE)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=THUMBNAIL_QUALITY)

    base_name = os.path.splitext(os.path.basename(image_field.name))[0]
    thumbnail_field.save(f"thumb_{base_name}.jpg", ContentFile(buffer.getvalue()), save=False)


def image_field_changed(instance, field_name):
    """True if `field_name` differs from what's currently saved in the DB."""
    if not instance.pk:
        return bool(getattr(instance, field_name))
    old_value = (
        type(instance)
        .objects.filter(pk=instance.pk)
        .values_list(field_name, flat=True)
        .first()
    )
    new_value = getattr(instance, field_name)
    return (old_value or '') != (new_value.name if new_value else '')
