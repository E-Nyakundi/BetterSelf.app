# Generated by Django 5.0.6 on 2024-07-17 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Time_Manager', '0012_rename_time_routine_end_time_routine_start_time'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='routine',
            options={'ordering': ['start_time']},
        ),
        migrations.AddField(
            model_name='goals',
            name='end_year',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='goals',
            name='start_year',
            field=models.DateField(null=True),
        ),
    ]
