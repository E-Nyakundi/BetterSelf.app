# Generated by Django 5.1.5 on 2025-02-07 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Time_Manager', '0019_event_user_goals_user_routine_user_schedule_activity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='end_time',
            field=models.TimeField(default='00:00:00'),
        ),
        migrations.AddField(
            model_name='event',
            name='start_time',
            field=models.TimeField(default='00:00:00'),
        ),
    ]
