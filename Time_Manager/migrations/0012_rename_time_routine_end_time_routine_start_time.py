# Generated by Django 5.0.6 on 2024-07-16 05:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Time_Manager', '0011_routine_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='routine',
            old_name='time',
            new_name='end_time',
        ),
        migrations.AddField(
            model_name='routine',
            name='start_time',
            field=models.TimeField(default='00:00:00'),
        ),
    ]
