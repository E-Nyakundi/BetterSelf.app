from django.db import models
from django.conf import settings
from BetterSelf.thumbnails import refresh_thumbnail, image_field_changed

# Default icon presets offered when a user creates a category.
# (value, display label) — the value is stored on Category.icon and
# rendered as `fa-solid fa-{value}` in templates.
CATEGORY_ICON_CHOICES = [
    ('box', 'General'),
    ('laptop', 'Computers'),
    ('mobile-screen-button', 'Phones'),
    ('tv', 'Electronics'),
    ('car', 'Vehicles'),
    ('house', 'Property'),
    ('shirt', 'Clothing'),
    ('couch', 'Furniture'),
    ('screwdriver-wrench', 'Tools'),
    ('file', 'Documents'),
    ('book', 'Books'),
    ('kitchen-set', 'Kitchen'),
    ('dumbbell', 'Sports & Fitness'),
    ('gem', 'Jewelry & Valuables'),
    ('paw', 'Pets'),
    ('gamepad', 'Games & Hobbies'),
]

DEFAULT_CATEGORY_ICON = 'box'


# Category model supporting infinite nesting
class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(
        max_length=50,
        choices=CATEGORY_ICON_CHOICES,
        default=DEFAULT_CATEGORY_ICON,
        help_text="Pick an icon that represents this category, or upload a custom image below."
    )
    image = models.ImageField(
        upload_to='inventory/categories/',
        null=True,
        blank=True,
        help_text="Optional custom image — overrides the icon when set."
    )
    thumbnail = models.ImageField(
        upload_to='inventory/categories/thumbs/',
        null=True,
        blank=True,
        editable=False,
        help_text="Auto-generated small preview of `image` — don't set this directly."
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_path()

    def save(self, *args, **kwargs):
        needs_thumb = image_field_changed(self, 'image')
        super().save(*args, **kwargs)
        if needs_thumb:
            refresh_thumbnail(self.image, self.thumbnail)
            super().save(update_fields=['thumbnail'])

    def full_path(self):
        names = [self.name]
        parent = self.parent
        while parent:
            names.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(names))

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('name', 'parent', 'user')  # Prevent duplicate names under same parent/user


# Item model
class Item(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used_like_new', 'Used - Like New'),
        ('used_good', 'Used - Good'),
        ('used_fair', 'Used - Fair'),
        ('damaged', 'Damaged'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=100)
    image = models.ImageField(
        upload_to='inventory/items/',
        null=True,
        blank=True,
        help_text="A photo of the item — snap one live or upload a file."
    )
    thumbnail = models.ImageField(
        upload_to='inventory/items/thumbs/',
        null=True,
        blank=True,
        editable=False,
        help_text="Auto-generated small preview of `image` — don't set this directly."
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='items'
    )
    date_acquired = models.DateField(null=True, blank=True)
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        null=True,
        blank=True
    )
    purpose = models.CharField(max_length=100, null=True, blank=True)
    item_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        needs_thumb = image_field_changed(self, 'image')
        super().save(*args, **kwargs)
        if needs_thumb:
            refresh_thumbnail(self.image, self.thumbnail)
            super().save(update_fields=['thumbnail'])
