from django.db import models
from .utils import create_events_for_routine, create_event_for_daily_goal
from django.conf import settings
from datetime import date, timedelta

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

    def get_daily_goals_queryset(self):
        """All DailyGoal leaves under this goal's full yearly→...→daily tree.

        Single source of truth for "how much of this goal tree is done" —
        used by progress_percentage() and current_streak() so the dashboard,
        the future dedicated Goal Progress page (Phase 2), and the goal tree
        view all agree on what counts.

        Note: for a user with many top-level goals this is one query per
        call site per goal (not yet prefetch-optimized). That's the known,
        tracked N+1 risk for this app — see Phase 7 of the roadmap, which
        formalizes prefetch_related + a query-count regression check across
        the whole Goals tree, not just this method.
        """
        return DailyGoal.objects.filter(
            day_goal__weekly_goal__monthly_goal__yearly_goal__goals=self
        )

    def progress_percentage(self):
        """% of this goal tree's DailyGoal leaves marked completed.

        Returns None (not 0) when there are no DailyGoal leaves yet at all,
        so callers can render an honest "no tasks logged yet" state instead
        of a misleading 0%.
        """
        qs = self.get_daily_goals_queryset()
        total = qs.count()
        if total == 0:
            return None
        completed = qs.filter(completed=True).count()
        return round(completed / total * 100)

    def current_streak(self, reference_date=None, max_lookback_days=400):
        """Consecutive days (walking back from reference_date) where every
        DailyGoal scheduled for that day under this tree was completed.

        Days with no DailyGoal scheduled at all are skipped rather than
        treated as a break — a day you had nothing planned for this goal
        shouldn't zero out a real streak. A day with goals scheduled but
        not all completed *does* break the streak.

        This is the "simplest honest version" the roadmap calls for: it's
        derived entirely from existing DailyGoal.date/.completed data, no
        new model. If a goal has no DailyGoal history at all, returns 0 so
        the dashboard can show "streak tracking starts now" instead of a
        fabricated number.
        """
        reference_date = reference_date or date.today()
        rows = self.get_daily_goals_queryset().filter(
            date__isnull=False
        ).values_list('date', 'completed')

        if not rows:
            return 0

        all_done_by_date = {}
        for goal_date, completed in rows:
            # A day counts as "done" only if every goal scheduled that day
            # was completed — start True, AND in any incomplete goal.
            all_done_by_date[goal_date] = all_done_by_date.get(goal_date, True) and completed

        streak = 0
        day = reference_date
        for _ in range(max_lookback_days):
            if day in all_done_by_date:
                if all_done_by_date[day]:
                    streak += 1
                else:
                    break
            # else: nothing scheduled that day — skip without breaking
            day -= timedelta(days=1)
        return streak

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
        if self.date and self.start_time and self.end_time:
            create_event_for_daily_goal(self)


class Routine(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='routines')
    name = models.CharField(max_length=200)
    instruction = models.TextField(blank=True)
    start_time = models.TimeField(default='00:00:00')
    end_time = models.TimeField(default='00:00:00')
    is_weekend = models.BooleanField(default=False)
    days_of_week = models.JSONField(default=list)
    is_split = models.BooleanField(default=False)  # New field to track split routines
    original_routine = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)  # For tracking splits

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

    def save(self, *args, **kwargs):
        if kwargs.pop('skip_split', False):
            super().save(*args, **kwargs)
            return

        # Convert string days to integers for comparison
        days_as_ints = [int(day) if isinstance(day, str) else day for day in self.days_of_week]

        if (self.is_weekend and self.days_of_week and 
            not set(days_as_ints).issuperset({5, 6})):  # Now comparing integers
            
            # Create weekend version
            weekend_routine = Routine(
                user=self.user,
                name=f"Weekend: {self.name}",
                instruction=self.instruction,
                start_time=self.start_time,
                end_time=self.end_time,
                is_weekend=True,
                days_of_week=[5, 6],  # Sat, Sun as integers
                is_split=True,
                original_routine=self if self.pk else None
            )
            weekend_routine.save(skip_split=True)

            # Create weekday version (only Mon-Fri)
            weekday_days = [day for day in days_as_ints if day < 5]
            if weekday_days:  # Only create if there are weekday days
                weekday_routine = Routine(
                    user=self.user,
                    name=f"Weekdays: {self.name}",
                    instruction=self.instruction,
                    start_time=self.start_time,
                    end_time=self.end_time,
                    is_weekend=False,
                    days_of_week=weekday_days,
                    is_split=True,
                    original_routine=self if self.pk else None
                )
                weekday_routine.save(skip_split=True)

            self.is_split = True
            if self.pk:
                return self.delete()
            return

        super().save(*args, **kwargs)
        create_events_for_routine(self)
        
    def clean_days_of_week(self):
        if self.days_of_week:
            return [int(day) for day in self.days_of_week]
        return []                                                                   

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
