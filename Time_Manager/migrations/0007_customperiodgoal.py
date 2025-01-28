# Generated by Django 5.0.6 on 2024-07-10 07:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Time_Manager', '0006_goals_remove_dailygoal_description_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomPeriodGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task', models.CharField(max_length=100, null=True)),
                ('completed', models.BooleanField(default=False)),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('monthly_goal', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='custom_goals', to='Time_Manager.goals')),
            ],
        ),
    ]
