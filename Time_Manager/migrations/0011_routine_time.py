# Generated by Django 5.0.6 on 2024-07-16 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Time_Manager', '0010_rename_task_dailygoal_goal_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='routine',
            name='time',
            field=models.TimeField(default='00:00:00'),
        ),
    ]
