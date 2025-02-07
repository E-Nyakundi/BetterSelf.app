from django.db import models
from .utils import create_events_for_routine, create_event_for_daily_goal
from django.conf import settings

# Create your models here.

class Goals(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals', null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_year = models.DateField(null=True)
    end_year = models.DateField(null=True)

    def __str__(self):
        return self.name

class YearlyGoal(models.Model):
    goals = models.ForeignKey(Goals, related_name='yearly_goals', on_delete=models.CASCADE, null=True)
    goal = models.CharField(max_length=100, null=True)
    description = models.TextField(null=True)
    completed = models.BooleanField(default=False)
    year = models.DateField(null=True)

    def __str__(self):
        return self.goal

class MonthlyGoal(models.Model):
    yearly_goal = models.ForeignKey(YearlyGoal, related_name='monthly_goals', on_delete=models.CASCADE, null=True)
    goal = models.CharField(max_length=100, null=True)
    description = models.TextField(null=True)
    completed = models.BooleanField(default=False)
    month = models.DateField(null=True)

    def __str__(self):
        return self.goal

class WeeklyGoal(models.Model):
    monthly_goal = models.ForeignKey(MonthlyGoal, related_name='weekly_goals', on_delete=models.CASCADE, null=True)
    goal = models.CharField(max_length=100, null=True)
    description = models.TextField(null=True)
    completed = models.BooleanField(default=False)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    def __str__(self):
        return self.goal

class DayGoal(models.Model):
    weekly_goal = models.ForeignKey(WeeklyGoal, related_name='day_goal', on_delete=models.CASCADE, null=True)
    goal = models.CharField(max_length=100, null=True)
    description = models.TextField(null=True)
    completed = models.BooleanField(default=False)
    date = models.DateField(null=True)

    def __str__(self):
        return self.goal

class DailyGoal(models.Model):
    day_goal = models.ForeignKey(DayGoal, related_name='daily_goals', on_delete=models.CASCADE, null=True)
    goal = models.CharField(max_length=100, null=True)
    description = models.TextField(null=True)
    completed = models.BooleanField(default=False)
    date = models.DateField(null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)

    def __str__(self):
        return self.goal
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        create_event_for_daily_goal(self)



class Routine(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='routines', null=True, blank=True)
    name = models.CharField(max_length=200)
    instruction = models.TextField(blank=True)
    start_time = models.TimeField(default='00:00:00')
    end_time = models.TimeField(default='00:00:00')
    is_weekend = models.BooleanField(default=False)
    days_of_week = models.JSONField(default=list)  # New field to store specific days (0=Monday, 6=Sunday)
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"
    
    class Meta:
        ordering = ['start_time']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        create_events_for_routine(self)


class Schedule(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedule', null=True, blank=True)
    activity = models.CharField(max_length=200, blank=True, null=True)
    start_time = models.TimeField(default='00:00:00')
    end_time = models.TimeField(default='00:00:00')


class Event(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True)
    start_datetime = models.DateTimeField()
    start_time = models.TimeField(default='00:00:00')
    end_datetime = models.DateTimeField()
    end_time = models.TimeField(default='00:00:00')
    is_recurring = models.BooleanField(default=False)
    routine = models.ForeignKey(Routine, related_name='events', on_delete=models.SET_NULL, null=True, blank=True)
    goal = models.ForeignKey(DailyGoal, related_name='events', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title
