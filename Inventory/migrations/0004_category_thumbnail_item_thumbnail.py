from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0003_category_icon_category_image_item_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='thumbnail',
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Auto-generated small preview of `image` — don't set this directly.",
                null=True,
                upload_to='inventory/categories/thumbs/',
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='thumbnail',
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Auto-generated small preview of `image` — don't set this directly.",
                null=True,
                upload_to='inventory/items/thumbs/',
            ),
        ),
    ]
