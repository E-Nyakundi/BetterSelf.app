from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WellBeing', '0006_journalentry_energy_journalentry_focus_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalentry',
            name='thumbnail',
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Auto-generated small preview of `image` — don't set this directly.",
                null=True,
                upload_to='journal/images/thumbs/',
            ),
        ),
    ]
